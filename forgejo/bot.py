# forgejo - A maubot plugin to act as a Forgejo client and webhook receiver.
# Copyright (C) 2021 Tulir Asokan
# Copyright (C) 2026 Dr Serge Victor
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
from typing import Type

from maubot import Plugin
from mautrix.util.async_db import UpgradeTable

from .api import ForgejoWebhookReceiver
from .avatar_manager import AvatarManager
from .client_manager import ClientManager
from .commands import Commands
from .config import Config
from .db import DBManager
from .migrations import upgrade_table
from .webhook import WebhookHandler, WebhookManager


class ForgejoBot(Plugin):
    db: DBManager
    webhook_receiver: ForgejoWebhookReceiver
    webhook_manager: WebhookManager
    webhook_handler: WebhookHandler
    avatars: AvatarManager
    clients: ClientManager
    commands: Commands
    config: Config

    async def start(self) -> None:
        self.config.load_and_update()

        self.db = DBManager(self.database)
        self.clients = ClientManager(
            self.config["client_id"],
            self.config["client_secret"],
            self.http,
            self.db,
            self,
            self.config["forgejo_url"],
        )
        self.webhook_manager = WebhookManager(self.db)
        self.webhook_handler = WebhookHandler(bot=self)
        self.avatars = AvatarManager(bot=self)
        self.webhook_receiver = ForgejoWebhookReceiver(
            handler=self.webhook_handler,
            secrets=self.webhook_manager,
            global_secret=self.config["global_webhook_secret"],
            log=self.log.getChild("webhook_receiver"),
        )
        self.commands = Commands(bot=self)

        await self.clients.load_db()
        await self.avatars.load_db()

        self.register_handler_class(self.webhook_receiver)
        self.register_handler_class(self.clients)
        self.register_handler_class(self.commands)
        self.register_handler_class(self.webhook_manager)

    def on_external_config_update(self) -> None:
        self.config.load_and_update()
        self.clients.client_id = self.config["client_id"]
        self.clients.client_secret = self.config["client_secret"]
        self.clients.forgejo_url = self.config["forgejo_url"]
        self.webhook_handler.reload_config()
        self.commands.reload_config()

    @classmethod
    def get_config_class(cls) -> Type[Config]:
        return Config

    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable:
        return upgrade_table
