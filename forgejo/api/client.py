# forgejo - A maubot plugin to act as a Forgejo client and webhook receiver.
# Copyright (C) 2021 Tulir Asokan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Any, Dict, List, Optional, Union
import random
import string
import time

from aiohttp import ClientSession
from yarl import URL

from .types import Webhook

OptStrList = Optional[List[str]]


class ForgejoError(Exception):
    def __init__(self, message: str, status_code: int, **kwargs) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.kwargs = kwargs
        self.message = message


class ForgejoClient:
    """Forgejo REST API client (no GraphQL support)."""

    base_url: URL
    api_url: URL
    user_base_url: URL
    login_url: URL
    login_finish_url: URL

    client_id: str
    client_secret: str

    http: ClientSession
    token: str
    _login_state: str

    def __init__(
        self,
        http: ClientSession,
        client_id: str,
        client_secret: str,
        token: str,
        refresh_token: Optional[str] = None,
        expiry: Optional[float] = None,
        forgejo_url: str = "https://git.it-zone.org",
    ) -> None:
        self.http = http
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self.refresh_token = refresh_token
        self.expiry = expiry
        self._login_state = ""
        self._login_redirect_uri = ""
        self.base_url = URL(forgejo_url)
        self.api_url = self.base_url / "api" / "v1"
        self.user_base_url = self.base_url
        self.login_url = self.base_url / "login" / "oauth" / "authorize"
        self.login_finish_url = self.base_url / "login" / "oauth" / "access_token"

    def get_login_url(
        self, redirect_uri: Union[str, URL], user_id: str = "", room_id: str = ""
    ) -> URL:
        """Generate OAuth2 login URL for Forgejo."""
        random_state = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=64)
        )
        self._login_state = f"{random_state}|{user_id}|{room_id}"
        self._login_redirect_uri = str(redirect_uri)
        return self.login_url.with_query(
            {
                "client_id": self.client_id,
                "redirect_uri": str(redirect_uri),
                "response_type": "code",
                "state": self._login_state,
            }
        )

    async def finish_login(self, code: str, state: str) -> tuple[str, str]:
        """Complete OAuth2 flow and get access token. Returns (user_id, room_id) from state."""
        if "|" not in state:
            raise ValueError("Invalid state format")
        parts = state.rsplit("|", 2)
        if len(parts) != 3:
            raise ValueError("Invalid state format")
        random_part, user_id, room_id = parts
        if f"{random_part}|{user_id}|{room_id}" != self._login_state:
            raise ValueError("Invalid state")
        resp = await self.http.post(
            self.login_finish_url,
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self._login_redirect_uri,
            },
            headers={
                "Accept": "application/json",
            },
        )
        data = await resp.json()
        self.token = data["access_token"]
        # Store refresh token and expiry if provided
        self.refresh_token = data.get("refresh_token")
        if "expires_in" in data:
            # expires_in is seconds from now
            self.expiry = time.time() + data["expires_in"]
        elif "expiry" in data:
            # expiry might be a timestamp
            self.expiry = data["expiry"]
        return user_id, room_id

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/json",
        }

    def is_token_expired(self) -> bool:
        if self.expiry is None:
            return False
        return time.time() >= self.expiry - 60

    async def ensure_valid_token(self) -> None:
        if self.is_token_expired():
            if self.refresh_token is None:
                raise ForgejoError(
                    "Token expired and no refresh token available", status_code=401
                )
            await self.refresh_access_token()

    async def refresh_access_token(self) -> None:
        if self.refresh_token is None:
            raise ForgejoError("No refresh token available", status_code=400)
        resp = await self.http.post(
            self.login_finish_url,
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            headers={
                "Accept": "application/json",
            },
        )
        if resp.status >= 400:
            try:
                data = await resp.json()
                message = data.get("message", resp.reason)
            except Exception:
                message = resp.reason
            raise ForgejoError(message=message, status_code=resp.status)
        data = await resp.json()
        self.token = data["access_token"]
        if "refresh_token" in data:
            self.refresh_token = data["refresh_token"]
        if "expires_in" in data:
            self.expiry = time.time() + data["expires_in"]

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make a REST API request to Forgejo."""
        await self.ensure_valid_token()
        url = self.api_url / path
        resp = await self.http.request(method, url, headers=self.headers, **kwargs)
        if resp.status >= 400:
            try:
                data = await resp.json()
                message = data.get("message", resp.reason)
            except Exception:
                message = resp.reason
            raise ForgejoError(message=message, status_code=resp.status)
        if resp.status == 204:
            return None
        return await resp.json()

    async def get_viewer(self) -> Dict[str, Any]:
        """Get current authenticated user info."""
        return await self._request("GET", "user")

    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        return await self._request("GET", f"repos/{owner}/{repo}")

    async def list_webhooks(self, owner: str, repo: str) -> List[Webhook]:
        """List webhooks for a repository."""
        data = await self._request("GET", f"repos/{owner}/{repo}/hooks")
        return [Webhook.deserialize(info) for info in data]

    async def get_webhook(self, owner: str, repo: str, hook_id: int) -> Webhook:
        """Get a specific webhook."""
        data = await self._request("GET", f"repos/{owner}/{repo}/hooks/{hook_id}")
        return Webhook.deserialize(data)

    async def create_webhook(
        self,
        owner: str,
        repo: str,
        url: URL,
        *,
        active: bool = True,
        events: OptStrList = None,
        content_type: str = "json",
        secret: Optional[str] = None,
        insecure_ssl: bool = False,
    ) -> Webhook:
        """Create a webhook for a repository."""
        payload = {
            "type": "gitea",
            "config": {
                "url": str(url),
                "content_type": content_type,
                "secret": secret or "",
            },
            "events": events or ["push"],
            "active": active,
        }
        if insecure_ssl:
            payload["config"]["insecure_ssl"] = "1"
        data = await self._request(
            "POST",
            f"repos/{owner}/{repo}/hooks",
            json=payload,
        )
        return Webhook.deserialize(data)

    async def edit_webhook(
        self,
        owner: str,
        repo: str,
        hook_id: int,
        *,
        url: Optional[URL] = None,
        active: Optional[bool] = None,
        events: OptStrList = None,
        add_events: OptStrList = None,
        remove_events: OptStrList = None,
        content_type: Optional[str] = None,
        secret: Optional[str] = None,
        insecure_ssl: Optional[bool] = None,
    ) -> Webhook:
        """Edit an existing webhook."""
        payload: Dict[str, Any] = {}
        if events:
            if add_events or remove_events:
                raise ValueError(
                    "Cannot override event list and add/remove at the same time"
                )
            payload["events"] = events
        if add_events or remove_events:
            payload["add_events"] = add_events or []
            payload["remove_events"] = remove_events or []
        if active is not None:
            payload["active"] = active
        config = {}
        if url is not None:
            config["url"] = str(url)
        if content_type is not None:
            config["content_type"] = content_type
        if secret is not None:
            config["secret"] = secret
        if insecure_ssl is not None:
            config["insecure_ssl"] = "1" if insecure_ssl else "0"
        if config:
            payload["config"] = config
        data = await self._request(
            "PATCH",
            f"repos/{owner}/{repo}/hooks/{hook_id}",
            json=payload,
        )
        return Webhook.deserialize(data)

    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> None:
        """Delete a webhook."""
        await self._request("DELETE", f"repos/{owner}/{repo}/hooks/{hook_id}")

    async def reset_token(self) -> Optional[str]:
        return None

    async def delete_token(self) -> None:
        self.token = ""
        self.refresh_token = None
        self.expiry = None
