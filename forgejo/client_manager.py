# forgejo - A maubot plugin to act as a Forgejo client and webhook receiver.
# Copyright (C) 2020 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# https://www.gnu.org/licenses/.
from typing import TYPE_CHECKING, Optional

from aiohttp import ClientError, ClientSession, web

from maubot.handlers import web as web_handler
from mautrix.types import UserID

from .api import ForgejoClient
from .db import DBManager

if TYPE_CHECKING:
    from .bot import ForgejoBot


class ClientManager:
    client_id: str
    client_secret: str
    forgejo_url: str
    _clients: dict[UserID, ForgejoClient]
    _db: DBManager
    _http: ClientSession
    _bot: "ForgejoBot"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        http: ClientSession,
        db: DBManager,
        bot: "ForgejoBot",
        forgejo_url: str = "https://git.it-zone.org",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.forgejo_url = forgejo_url
        self._db = db
        self._http = http
        self._bot = bot
        self._clients = {}

    async def load_db(self) -> None:
        self._clients = {
            cli.user_id: self._make(cli.token) for cli in await self._db.get_clients()
        }

    def _make(
        self,
        token: str,
        refresh_token: Optional[str] = None,
        expiry: Optional[float] = None,
    ) -> ForgejoClient:
        return ForgejoClient(
            http=self._http,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token=token,
            refresh_token=refresh_token,
            expiry=expiry,
            forgejo_url=self.forgejo_url,
        )

    async def put(
        self,
        user_id: UserID,
        token: str,
        refresh_token: Optional[str] = None,
        expiry: Optional[float] = None,
    ) -> None:
        await self._db.put_client(user_id, token, refresh_token, expiry)

    async def remove(self, user_id: UserID) -> None:
        self._clients.pop(user_id, None)
        await self._db.delete_client(user_id)

    def get_all(self) -> dict[UserID, ForgejoClient]:
        return self._clients.copy()

    def get(self, user_id: UserID, create: bool = False) -> ForgejoClient | None:
        try:
            return self._clients[user_id]
        except KeyError:
            if create:
                client = self._make("")
                self._clients[user_id] = client
                return client
            return None

    @web_handler.get("/auth")
    async def login_callback(self, request: web.Request) -> web.Response:
        try:
            error_code = request.query["error"]
            error_msg = request.query["error_description"]
            error_uri = request.query.get("error_uri", "<no URI provided>")
        except KeyError:
            pass
        else:
            return web.Response(
                status=400,
                text=f"Failed to log in: {error_code}\n\n"
                f"{error_msg}\n\n"
                f"More info at {error_uri}",
            )
        try:
            code = request.query["code"]
            state = request.query["state"]
        except KeyError as e:
            return web.Response(status=400, text=f"Missing {e.args[0]} parameter")
        try:
            parts = state.rsplit("|", 2)
            if len(parts) != 3:
                raise ValueError("Invalid state format")
            _, user_id, room_id = parts
            user_id = UserID(user_id)
        except (IndexError, ValueError):
            return web.Response(status=400, text="Invalid state parameter")
        client = self.get(user_id)
        if not client:
            return web.Response(status=401, text="Invalid state token")
        try:
            await client.finish_login(code, state)
        except ValueError:
            return web.Response(status=401, text="Invalid state token")
        except (KeyError, ClientError):
            return web.Response(status=401, text="Failed to finish login")
        try:
            user_info = await client.get_viewer()
            user = user_info.get("login", "unknown")
        except Exception:
            user = "unknown"
        await self.put(user_id, client.token, client.refresh_token, client.expiry)
        if room_id:
            from mautrix.types import Format, RoomID, TextMessageEventContent

            content = TextMessageEventContent(
                msgtype="m.text",
                format=Format.HTML,
                body=f"Successfully logged in as @{user}",
                formatted_body=f"Successfully logged in as <a href='https://matrix.to/#/{user_id}'>@{user}</a>",
            )
            try:
                await self._bot.client.send_message(RoomID(room_id), content)
            except Exception:
                pass
        return web.Response(status=200, text=f"Logged in as {user}")
