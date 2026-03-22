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
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple

from maubot import MessageEvent
from maubot.handlers import command
from mautrix.types import Event, EventType, RelationType

from .api import ForgejoClient, ForgejoError

if TYPE_CHECKING:
    from .bot import ForgejoBot


def authenticated(_outer_fn=None, *, required: bool = True, error: bool = True):
    def decorator(fn):
        async def wrapper(self: "Commands", evt: Event, **kwargs) -> None:
            client = self.bot.clients.get(evt.sender)
            if required and (not client or not client.token):
                if error and hasattr(evt, "reply"):
                    await evt.reply(
                        "You're not logged in. Log in with `!forgejo login` first."
                    )
                return
            elif client and not client.token:
                client = None
            try:
                return await fn(self, evt, **kwargs, client=client)
            except ForgejoError as e:
                if error:
                    await evt.reply(str(e))

        return wrapper

    return decorator(_outer_fn) if _outer_fn else decorator


async def get_relation_target(
    evt: Event, expected_type: RelationType
) -> Optional[Dict[str, Any]]:
    if evt.content.relates_to.rel_type != expected_type:
        return None
    orig_evt = await evt.client.get_event(evt.room_id, evt.content.relates_to.event_id)
    if orig_evt.sender != evt.client.mxid or orig_evt.type != EventType.ROOM_MESSAGE:
        return None
    try:
        return orig_evt.content["xyz.maubot.forgejo.webhook"]
    except KeyError:
        return None


def with_webhook_meta(relation_type: RelationType):
    def decorator(fn):
        async def wrapper(self: "Commands", evt: Event, **kwargs) -> None:
            webhook_meta = await get_relation_target(evt, relation_type)
            if not webhook_meta:
                return
            await fn(self, evt, **kwargs, webhook_meta=webhook_meta)

        return wrapper

    return decorator


repo_syntax = r"([A-Za-z0-9_-]+)/([A-Za-z0-9-_.]+)"


class Commands:
    bot: "ForgejoBot"

    _command_prefix: str
    _aliases: Set[str]

    def __init__(self, bot: "ForgejoBot") -> None:
        self.bot = bot
        self.reload_config()

    def reload_config(self) -> None:
        prefix = self.bot.config["command_options.prefix"]
        if isinstance(prefix, str):
            self._command_prefix = prefix
            self._aliases = {prefix}
        elif isinstance(prefix, list) and len(prefix) > 0:
            self._command_prefix = prefix[0]
            self._aliases = set(prefix)
        else:
            self._command_prefix = "forgejo"
            self._aliases = {"forgejo", "fg"}

    @command.new(
        name=lambda self: self._command_prefix,
        aliases=lambda self, alias: alias in self._aliases,
        require_subcommand=True,
    )
    async def forgejo(self, evt: MessageEvent) -> None:
        pass

    @forgejo.subcommand("login", help="Log into Forgejo.")
    @command.argument("flags", required=False, pass_raw=True)
    @authenticated(required=False)
    async def login(
        self, evt: MessageEvent, flags: str, client: Optional[ForgejoClient]
    ) -> None:
        redirect_url = self.bot.webapp_url / "auth"
        login_url = str(
            self.bot.clients.get(evt.sender, create=True).get_login_url(
                redirect_uri=redirect_url,
                user_id=evt.sender,
                room_id=evt.room_id,
            )
        )
        if client:
            try:
                user_info = await client.get_viewer()
                username = user_info.get("login", "unknown")
                await evt.reply(
                    f"You're already logged in as @{username}, but you can "
                    f"[click here to switch to a different account]({login_url})"
                )
            except ForgejoError as e:
                if e.status_code in (401, 403):
                    await evt.reply(
                        f"You are not logged in. [Click here to log in]({login_url})"
                    )
                    await self.bot.clients.remove(evt.sender)
                else:
                    await evt.reply(f"Failed to verify login: {e.message}")
                    await evt.reply(f"[Click here to log in]({login_url})")
            except Exception as e:
                await evt.reply(f"Failed to verify login: {e}")
                await evt.reply(f"[Click here to log in]({login_url})")
        else:
            await evt.reply(f"[Click here to log in]({login_url})")

    @forgejo.subcommand("logout", help="Delete the stored Forgejo access token.")
    @authenticated
    async def logout(self, evt: MessageEvent, client: ForgejoClient) -> None:
        await client.delete_token()
        await self.bot.clients.remove(evt.sender)
        await evt.reply("Successfully logged out")

    @forgejo.subcommand("ping", help="Check your login status.")
    @authenticated
    async def ping(self, evt: MessageEvent, client: ForgejoClient) -> None:
        try:
            user_info = await client.get_viewer()
            username = user_info.get("login", "unknown")
            await evt.reply(f"You're logged in as @{username}")
        except ForgejoError as e:
            if e.status_code in (401, 403):
                await evt.reply(
                    "Your login has expired or been revoked. "
                    "Please log in again with `!forgejo login`."
                )
                # Remove the invalid client
                await self.bot.clients.remove(evt.sender)
            else:
                await evt.reply(f"Failed to get user info: {e.message}")
        except Exception as e:
            await evt.reply(f"Failed to get user info: {e}")

    @forgejo.subcommand(
        "webhook", aliases=["w"], help="Manage webhooks.", required_subcommand=True
    )
    async def webhook(self, evt: MessageEvent) -> None:
        await evt.reply(
            "**Usage:** `!{self._command_prefix} webhook <add|remove|list>`"
        )
        return

    @webhook.subcommand("list", aliases=["ls", "l"], help="List webhooks in this room.")
    async def webhook_list(self, evt: MessageEvent) -> None:
        hooks = await self.bot.webhook_manager.get_all_for_room(evt.room_id)
        info = "\n".join(
            f"* `{hook.repo}` added by "
            f"[{hook.user_id}](https://matrix.to/#/{hook.user_id})"
            for hook in hooks
        )
        await evt.reply(f"Forgejo webhooks in this room:\n\n{info}")

    @webhook.subcommand(
        "add", aliases=["a", "create", "c"], help="Add a webhook for this room."
    )
    @command.argument("repo", required=False, matches=repo_syntax, label="owner/repo")
    @authenticated
    async def webhook_create(
        self, evt: MessageEvent, repo: Optional[Tuple[str, str]], client: ForgejoClient
    ) -> None:
        if not repo:
            await evt.reply(
                f"**Usage:** `!{self._command_prefix} webhook add <owner/repo>`"
            )
            return
        repo_name = f"{repo[0]}/{repo[1]}"
        existing = await self.bot.webhook_manager.get_by_repo(repo_name, evt.room_id)
        if existing:
            await evt.reply("This room already has a webhook for that repo")
            return
        webhook = await self.bot.webhook_manager.create(
            repo_name, evt.sender, evt.room_id
        )
        try:
            await client.create_webhook(
                *repo,
                url=self.bot.webapp_url / "webhook" / str(webhook.id),
                secret=webhook.secret,
                content_type="json",
                events=[
                    "create",
                    "delete",
                    "fork",
                    "push",
                    "issues",
                    "issue_assign",
                    "issue_label",
                    "issue_milestone",
                    "issue_comment",
                    "pull_request",
                    "pull_request_assign",
                    "pull_request_label",
                    "pull_request_milestone",
                    "pull_request_comment",
                    "pull_request_review",
                    "pull_request_review_approved",
                    "pull_request_review_rejected",
                    "pull_request_review_comment",
                    "pull_request_review_request",
                    "pull_request_sync",
                    "repository",
                    "release",
                    "package",
                    "wiki",
                    "status",
                    "workflow_run",
                    "workflow_job",
                ],
            )
        except ForgejoError as e:
            await evt.reply(f"Failed to create webhook: {e.message}")
            await self.bot.webhook_manager.delete(webhook.id)
        else:
            await evt.reply(f"Successfully created webhook for {repo_name}")

    @webhook.subcommand("remove", aliases=["delete", "rm", "del"])
    @command.argument("repo", required=True, matches=repo_syntax, label="owner/repo")
    @authenticated(required=False)
    async def webhook_remove(
        self, evt: MessageEvent, repo: Tuple[str, str], client: Optional[ForgejoClient]
    ) -> None:
        repo_name = f"{repo[0]}/{repo[1]}"
        webhook_info = await self.bot.webhook_manager.get_by_repo(
            evt.room_id, repo_name
        )
        if not webhook_info:
            await evt.reply("This room does not have a webhook for that repo")
            return
        await self.bot.webhook_manager.delete(webhook_info.id)
        if webhook_info.forgejo_id:
            if client:
                try:
                    await client.delete_webhook(*repo, hook_id=webhook_info.forgejo_id)
                except ForgejoError as e:
                    if e.status_code == 404:
                        await evt.reply("Webhook deleted successfully")
                        return
                    else:
                        self.bot.log.warning(
                            f"Failed to remove {webhook_info} from Forgejo",
                            exc_info=True,
                        )
                else:
                    await evt.reply("Webhook deleted successfully")
                    return
            await evt.reply(
                "Webhook deleted locally, but it may still exist on Forgejo"
            )
        else:
            await evt.reply("Webhook deleted locally")

    @webhook.subcommand("inspect", aliases=["i"])
    @command.argument("repo", required=True, matches=repo_syntax, label="owner/repo")
    @authenticated
    async def webhook_inspect(
        self, evt: MessageEvent, repo: Tuple[str, str], client: ForgejoClient
    ) -> None:
        repo_name = f"{repo[0]}/{repo[1]}"
        webhook_info = await self.bot.webhook_manager.get_by_repo(
            evt.room_id, repo_name
        )
        if not webhook_info:
            await evt.reply("This room does not have a webhook for that repo")
            return

        info_parts = [
            f"**Repository:** `{repo_name}`",
            f"**Room:** `{webhook_info.room_id}`",
            f"**User:** [{webhook_info.user_id}](https://matrix.to/#/{webhook_info.user_id})",
        ]

        if webhook_info.forgejo_id:
            info_parts.append(f"**Forgejo Hook ID:** `{webhook_info.forgejo_id}`")
            try:
                hooks = await client.list_webhooks(*repo)
                for hook in hooks:
                    if hook.id == webhook_info.forgejo_id:
                        info_parts.append(
                            f"**Active:** {'Yes' if hook.active else 'No'}"
                        )
                        info_parts.append(
                            f"**Events:** {', '.join(hook.events) if hook.events else 'None'}"
                        )
                        info_parts.append(
                            f"**URL:** `{hook.config.url if hook.config else 'N/A'}'"
                        )
                        break
            except ForgejoError as e:
                info_parts.append(f"_Could not fetch Forgejo details: {e.message}_")
        else:
            info_parts.append(
                "_Webhook not yet registered with Forgejo (pending ping)_"
            )

        await evt.reply("\n".join(info_parts))
