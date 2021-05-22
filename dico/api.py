import io
import typing
import pathlib
from .base.http import HTTPRequestBase
from .model import Channel, Message, MessageReference, AllowedMentions, Snowflake, Embed, Attachment, Overwrite, Emoji, User, Interaction, InteractionResponse, Webhook, Guild, ApplicationCommand
from .utils import from_emoji


class APIClient:
    """
    REST API handling client.

    .. note::
        If you chose to use async request handler, all request functions will return coroutine which will return raw instance.

    :param token: Token of the client.
    :param base: HTTP request handler to use. Must inherit :class:`.base.http.HTTPRequestBase`.
    :param default_allowed_mentions: Default :class:`.model.channel.AllowedMentions` object to use. Default None.
    :param application_id: ID of the application. Required if you use interactions.
    :param **http_options: Options of HTTP request handler.

    :ivar http: HTTP request client.
    :ivar default_allowed_mentions: Default :class:`.model.channel.AllowedMentions` object of the API client.
    :ivar application_id: ID of the application. Can be ``None``, and if it is, you must pass parameter application_id for all methods that has it.
    """

    def __init__(self,
                 token,
                 *,
                 base: typing.Type[HTTPRequestBase],
                 default_allowed_mentions: AllowedMentions = None,
                 application_id: typing.Union[int, str, Snowflake] = None,
                 **http_options):
        self.http = base.create(token, **http_options)
        self.default_allowed_mentions = default_allowed_mentions
        self.application_id = Snowflake.ensure_snowflake(application_id)

    # Channel

    def request_channel(self, channel: typing.Union[int, str, Snowflake, Channel]):
        channel = self.http.request_channel(int(channel))
        if isinstance(channel, dict):
            channel = Channel.create(self, channel)
        return channel

    def modify_guild_channel(self,
                             channel: typing.Union[int, str, Snowflake, Channel],
                             *,
                             name: str = None,
                             channel_type: int = None,
                             position: int = None,
                             topic: str = None,
                             nsfw: bool = None,
                             rate_limit_per_user: int = None,
                             bitrate: int = None,
                             user_limit: int = None,
                             permission_overwrites: typing.List[Overwrite] = None,
                             parent: typing.Union[int, str, Snowflake, Channel] = None,
                             rtc_region: str = None,
                             video_quality_mode: int = None):
        if permission_overwrites:
            permission_overwrites = [x.to_dict() for x in permission_overwrites]
        if parent:
            parent = int(parent)
        channel = self.http.modify_guild_channel(int(channel), name, channel_type, position, topic, nsfw, rate_limit_per_user,
                                                 bitrate, user_limit, permission_overwrites, parent, rtc_region, video_quality_mode)
        if isinstance(channel, dict):
            channel = Channel.create(self, channel)
        return channel

    def modify_group_dm_channel(self, channel: typing.Union[int, str, Snowflake, Channel], *, name: str = None, icon: bin = None):
        channel = self.http.modify_group_dm_channel(int(channel), name, icon)
        if isinstance(channel, dict):
            channel = Channel.create(self, channel)
        return channel

    def modify_thread_channel(self,
                              channel: typing.Union[int, str, Snowflake, Channel], *,
                              name: str = None,
                              archived: bool = None,
                              auto_archive_duration: int = None,
                              locked: bool = None,
                              rate_limit_per_user: int = None):
        channel = self.http.modify_thread_channel(int(channel), name, archived, auto_archive_duration, locked, rate_limit_per_user)
        if isinstance(channel, dict):
            channel = Channel.create(self, channel)
        return channel

    def delete_channel(self, channel: typing.Union[int, str, Snowflake, Channel]):
        return self.http.delete_channel(int(channel))

    def request_channel_messages(self,
                                 channel: typing.Union[int, str, Snowflake, Channel], *,
                                 around: typing.Union[int, str, Snowflake, Message] = None,
                                 before: typing.Union[int, str, Snowflake, Message] = None,
                                 after: typing.Union[int, str, Snowflake, Message] = None,
                                 limit: int = 50):
        messages = self.http.request_channel_messages(int(channel), around and str(int(around)), before and str(int(before)), after and str(int(after)), limit)
        # This looks unnecessary, but this is to ensure they are all numbers.
        if isinstance(messages, list):
            messages = [Message.create(self, x) for x in messages]
        return messages

    def request_channel_message(self, channel: typing.Union[int, str, Snowflake, Channel], message: typing.Union[int, str, Snowflake, Message]):
        message = self.http.request_channel_message(int(channel), int(message))
        if isinstance(message, dict):
            message = Message.create(self, channel)
        return message

    def create_message(self,
                       channel: typing.Union[int, str, Snowflake, Channel],
                       content: str = None,
                       *,
                       embed: typing.Union[Embed, dict] = None,
                       file: typing.Union[io.FileIO, pathlib.Path, str] = None,
                       files: typing.List[typing.Union[io.FileIO, pathlib.Path, str]] = None,
                       tts: bool = False,
                       allowed_mentions: typing.Union[AllowedMentions, dict] = None,
                       message_reference: typing.Union[Message, MessageReference, dict] = None) -> typing.Union[Message, typing.Coroutine[dict, Message, dict]]:
        """
        Sends message create request to API.

        .. note::
            - FileIO object passed to ``file`` or ``files`` parameter will be automatically closed when requesting,
              therefore it is recommended to pass file path.

        .. warning::
            - You must pass at least one of ``content`` or ``embed`` or ``file`` or ``files`` parameter.
            - You can't use ``file`` and ``files`` at the same time.

        :param channel: Channel to create message. Accepts both :class:`.model.channel.Channel` and channel ID.
        :param content: Content of the message.
        :param embed: Embed of the message.
        :param file: File of the message.
        :param files: Files of the message.
        :param tts: Whether to speak message.
        :param allowed_mentions: :class:`.model.channel.AllowedMentions` to use for this request.
        :param message_reference: Message to reply.
        :return: Union[:class:`.model.channel.Message`, Coroutine[dict]]
        """
        if files and file:
            raise TypeError("you can't pass both file and files.")
        if file:
            files = [file]
        if files:
            for x in range(len(files)):
                sel = files[x]
                if not isinstance(sel, io.FileIO):
                    files[x] = open(sel, "rb")
        if isinstance(message_reference, Message):
            message_reference = MessageReference.from_message(message_reference)
        if embed and not isinstance(embed, dict):
            embed = embed.to_dict()
        if message_reference and not isinstance(message_reference, dict):
            message_reference = message_reference.to_dict()
        params = {"channel_id": int(channel),
                  "content": content,
                  "embed": embed,
                  "nonce": None,  # What does this do tho?
                  "message_reference": message_reference,
                  "tts": tts,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions)}
        if files:
            params["files"] = files
        try:
            msg = self.http.create_message_with_files(**params) if files else self.http.create_message(**params)
            if isinstance(msg, dict):
                msg = Message.create(self, msg)
            return msg
        finally:
            if files:
                [x.close() for x in files if not x.closed]

    def create_reaction(self,
                        channel: typing.Union[int, str, Snowflake, Channel],
                        message: typing.Union[int, str, Snowflake, Message],
                        emoji: typing.Union[str, Emoji]):
        return self.http.create_reaction(int(channel), int(message), from_emoji(emoji))

    def delete_reaction(self,
                        channel: typing.Union[int, str, Snowflake, Channel],
                        message: typing.Union[int, str, Snowflake, Message],
                        emoji: typing.Union[str, Emoji],
                        user: typing.Union[int, str, Snowflake, User] = "@me"):
        return self.http.delete_reaction(int(channel), int(message), from_emoji(emoji), int(user) if user != "@me" else user)

    def request_reactions(self,
                          channel: typing.Union[int, str, Snowflake, Channel],
                          message: typing.Union[int, str, Snowflake, Message],
                          emoji: typing.Union[str, Emoji],
                          after: typing.Union[int, str, Snowflake, User] = None,
                          limit: int = None):
        users = self.http.request_reactions(int(channel), int(message), from_emoji(emoji), int(after), limit)
        if isinstance(users, list):
            return [User.create(self, x) for x in users]
        return users

    def delete_all_reactions(self, channel: typing.Union[int, str, Snowflake, Channel], message: typing.Union[int, str, Snowflake, Message]):
        return self.http.delete_all_reactions(int(channel), int(message))

    def delete_all_reactions_emoji(self,
                                   channel: typing.Union[int, str, Snowflake, Channel],
                                   message: typing.Union[int, str, Snowflake, Message],
                                   emoji: typing.Union[str, Emoji]):
        return self.http.delete_all_reactions_emoji(int(channel), int(message), from_emoji(emoji))

    def edit_message(self,
                     channel: typing.Union[int, str, Snowflake, Channel],
                     message: typing.Union[int, str, Snowflake, Message],
                     *,
                     content: str = None,
                     embed: typing.Union[Embed, dict] = None,
                     allowed_mentions: typing.Union[AllowedMentions, dict] = None,
                     attachments: typing.List[typing.Union[Attachment, dict]] = None) -> typing.Union[Message, typing.Coroutine[dict, Message, dict]]:
        if embed and not isinstance(embed, dict):
            embed = embed.to_dict()
        _att = []
        if attachments:
            for x in attachments:
                if not isinstance(x, dict):
                    x = x.to_dict()
                _att.append(x)
        params = {"channel_id": int(channel),
                  "message_id": int(message),
                  "content": content,
                  "embed": embed,
                  "flags": None,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions),
                  "attachments": _att}
        msg = self.http.edit_message(**params)
        if isinstance(msg, dict):
            msg = Message.create(self, msg)
        return msg

    def delete_message(self,
                       channel: typing.Union[int, str, Snowflake, Channel],
                       message: typing.Union[int, str, Snowflake, Message]):
        return self.http.delete_message(int(channel), int(message))

    def bulk_delete_messages(self, channel: typing.Union[int, str, Snowflake, Channel], messages: typing.List[typing.Union[int, str, Snowflake, Message]]):
        return self.http.bulk_delete_messages(int(channel), list(map(int, messages)))

    def edit_channel_permissions(self, channel: typing.Union[int, str, Snowflake, Channel], overwrite: Overwrite):
        ow_dict = overwrite.to_dict()
        return self.http.edit_channel_permissions(int(channel), ow_dict["id"], ow_dict["allow"], ow_dict["deny"], ow_dict["type"])

    # Webhook

    def create_webhook(self, channel: typing.Union[int, str, Snowflake, Channel], *, name: str = None, avatar: str = None):
        hook = self.http.create_webhook(int(channel), name, avatar)
        if isinstance(hook, dict):
            return Webhook(self, hook)
        return hook

    def request_channel_webhooks(self, channel: typing.Union[int, str, Snowflake, Channel]):
        hooks = self.http.request_channel_webhooks(int(channel))
        if isinstance(hooks, list):
            return [Webhook(self, x) for x in hooks]
        return hooks

    def request_guild_webhooks(self, guild: typing.Union[int, str, Snowflake, Guild]):
        hooks = self.http.request_guild_webhooks(int(guild))
        if isinstance(hooks, list):
            return [Webhook(self, x) for x in hooks]
        return hooks

    def request_webhook(self, webhook: typing.Union[int, str, Snowflake, Webhook], webhook_token: str = None):  # Requesting webhook using webhook, seems legit.
        hook = self.http.request_webhook(int(webhook)) if not webhook_token else self.http.request_webhook_with_token(int(webhook), webhook_token)
        if isinstance(hook, dict):
            return Webhook(self, hook)
        return hook

    def modify_webhook(self,
                       webhook: typing.Union[int, str, Snowflake, Webhook],
                       *,
                       webhook_token: str = None,
                       name: str = None,
                       avatar: str = None,
                       channel: typing.Union[int, str, Snowflake, Channel] = None):
        hook = self.http.modify_webhook(int(webhook), name, avatar, str(int(channel)) if channel is not None else channel) if not webhook_token \
            else self.http.modify_webhook_with_token(int(webhook), webhook_token, name, avatar)
        if isinstance(hook, dict):
            return Webhook(self, hook)
        return hook

    def delete_webhook(self, webhook: typing.Union[int, str, Snowflake, Webhook], webhook_token: str = None):
        return self.http.delete_webhook(int(webhook)) if not webhook_token else self.http.delete_webhook_with_token(int(webhook), webhook_token)

    def execute_webhook(self,
                        webhook: typing.Union[int, str, Snowflake, Webhook],
                        *,
                        webhook_token: str = None,
                        wait: bool = None,
                        thread: typing.Union[int, str, Snowflake, Channel] = None,
                        content: str = None,
                        username: str = None,
                        avatar_url: str = None,
                        tts: bool = False,
                        file: typing.Union[io.FileIO, pathlib.Path, str] = None,
                        files: typing.List[typing.Union[io.FileIO, pathlib.Path, str]] = None,
                        embed: typing.Union[Embed, dict] = None,
                        embeds: typing.List[typing.Union[Embed, dict]] = None,
                        allowed_mentions: typing.Union[AllowedMentions, dict] = None):
        if webhook_token is None and not isinstance(webhook, Webhook):
            raise TypeError("you must pass webhook_token if webhook is not dico.Webhook object.")
        if thread and isinstance(thread, Channel) and not thread.is_thread_channel():
            raise TypeError("thread must be thread channel.")
        if file and files:
            raise TypeError("you can't pass both file and files.")
        if embed and embeds:
            raise TypeError("you can't pass both embed and embeds.")
        if file:
            files = [file]
        if files:
            for x in range(len(files)):
                sel = files[x]
                if not isinstance(sel, io.FileIO):
                    files[x] = open(sel, "rb")
        if embed:
            embeds = [embed]
        if embeds:
            embeds = [x.to_dict() for x in embeds if not isinstance(x, dict)]
        params = {"webhook_id": int(webhook),
                  "webhook_token": webhook_token if not isinstance(webhook, Webhook) else webhook.token,
                  "wait": wait,
                  "thread_id": str(int(thread)) if thread else thread,
                  "content": content,
                  "username": username,
                  "avatar_url": avatar_url,
                  "tts": tts,
                  "embeds": embeds,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions)}
        if files:
            params["files"] = files
        try:
            msg = self.http.execute_webhook(**params) if not files else self.http.execute_webhook_with_files(**params)
            if isinstance(msg, dict):
                return Message.create(self, msg, webhook_token=webhook_token or webhook.token)
            return msg
        finally:
            if files:
                [x.close() for x in files if not x.closed]

    def request_webhook_message(self,
                                webhook: typing.Union[int, str, Snowflake, Webhook],
                                message: typing.Union[int, str, Snowflake, Message],
                                *,
                                webhook_token: str = None):
        if not isinstance(webhook, Webhook) and not webhook_token:
            raise TypeError("you must pass webhook_token if webhook is not dico.Webhook object.")
        msg = self.http.request_webhook_message(int(webhook), webhook_token or webhook.token, int(message))
        if isinstance(msg, dict):
            return Message.create(self, msg, webhook_token=webhook_token or webhook.token)
        return msg

    def edit_webhook_message(self,
                             webhook: typing.Union[int, str, Snowflake, Webhook],
                             message: typing.Union[int, str, Snowflake, Message],
                             *,
                             webhook_token: str = None,
                             content: str = None,
                             embed: typing.Union[Embed, dict] = None,
                             embeds: typing.List[typing.Union[Embed, dict]] = None,
                             file: typing.Union[io.FileIO, pathlib.Path, str] = None,
                             files: typing.List[typing.Union[io.FileIO, pathlib.Path, str]] = None,
                             allowed_mentions: typing.Union[AllowedMentions, dict] = None,
                             attachments: typing.List[typing.Union[Attachment, dict]] = None):
        if not isinstance(webhook, Webhook) and not webhook_token:
            raise TypeError("you must pass webhook_token if webhook is not dico.Webhook object.")
        if file and files:
            raise TypeError("you can't pass both file and files.")
        if embed and embeds:
            raise TypeError("you can't pass both embed and embeds.")
        if file:
            files = [file]
        if files:
            for x in range(len(files)):
                sel = files[x]
                if not isinstance(sel, io.FileIO):
                    files[x] = open(sel, "rb")
        if embed:
            embeds = [embed]
        if embeds:
            embeds = [x.to_dict() for x in embeds if not isinstance(x, dict)]
        _att = []
        if attachments:
            for x in attachments:
                if not isinstance(x, dict):
                    x = x.to_dict()
                _att.append(x)
        params = {"webhook_id": int(webhook),
                  "webhook_token": webhook_token or webhook.token,
                  "message_id": int(message),
                  "content": content,
                  "embeds": embeds,
                  "files": files,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions),
                  "attachments": _att}
        try:
            msg = self.http.edit_webhook_message(**params)
            if isinstance(msg, dict):
                return Message.create(self, msg, webhook_token=webhook_token or webhook.token)
            return msg
        finally:
            if files:
                [x.close() for x in files if not x.closed]

    def delete_webhook_message(self,
                               webhook: typing.Union[int, str, Snowflake, Webhook],
                               message: typing.Union[int, str, Snowflake, Message],
                               *,
                               webhook_token: str = None):
        if not isinstance(webhook, Webhook) and not webhook_token:
            raise TypeError("you must pass webhook_token if webhook is not dico.Webhook object.")
        return self.http.delete_webhook_message(int(webhook), webhook_token or webhook.token, int(message))

    # Interaction

    def request_application_commands(self,
                                     guild: typing.Union[int, str, Snowflake, Guild] = None,
                                     *,
                                     application_id: typing.Union[int, str, Snowflake] = None):
        if not application_id and not self.application_id:
            raise TypeError("you must pass application_id if it is not set in client instance.")
        app_commands = self.http.request_application_commands(int(application_id or self.application_id), int(guild) if guild else guild)
        if isinstance(app_commands, list):
            return [ApplicationCommand(x) for x in app_commands]
        return app_commands

    def create_interaction_response(self,
                                    interaction: typing.Union[int, str, Snowflake, Interaction],
                                    interaction_response: InteractionResponse,
                                    *,
                                    interaction_token: str = None):
        if not isinstance(interaction, Interaction) and not interaction_token:
            raise TypeError("you must pass interaction_token if interaction is not dico.Interaction object.")
        return self.http.create_interaction_response(int(interaction), interaction_token or interaction.token, interaction_response.to_dict())

    def request_original_interaction_response(self,
                                              interaction: typing.Union[int, str, Snowflake, Interaction] = None,
                                              *,
                                              interaction_token: str = None,
                                              application_id: typing.Union[int, str, Snowflake] = None):
        if not application_id and not self.application_id:
            raise TypeError("you must pass application_id if it is not set in client instance.")
        if not isinstance(interaction, Interaction) and not interaction_token:
            raise TypeError("you must pass interaction_token if interaction is not dico.Interaction object.")
        msg = self.http.request_original_interaction_response(application_id or self.application_id, interaction_token or interaction.token)
        if isinstance(msg, dict):
            return Message.create(self, msg, interaction_token=interaction_token or interaction.token, original_response=True)
        return msg

    def create_followup_message(self,
                                interaction: typing.Union[int, str, Snowflake, Interaction] = None,
                                *,
                                interaction_token: str = None,
                                application_id: typing.Union[int, str, Snowflake] = None,
                                content: str = None,
                                username: str = None,
                                avatar_url: str = None,
                                tts: bool = False,
                                file: typing.Union[io.FileIO, pathlib.Path, str] = None,
                                files: typing.List[typing.Union[io.FileIO, pathlib.Path, str]] = None,
                                embed: typing.Union[Embed, dict] = None,
                                embeds: typing.List[typing.Union[Embed, dict]] = None,
                                allowed_mentions: typing.Union[AllowedMentions, dict] = None,
                                ephemeral: bool = False):
        if not application_id and not self.application_id:
            raise TypeError("you must pass application_id if it is not set in client instance.")
        if not isinstance(interaction, Interaction) and not interaction_token:
            raise TypeError("you must pass interaction_token if interaction is not dico.Interaction object.")
        if file and files:
            raise TypeError("you can't pass both file and files.")
        if embed and embeds:
            raise TypeError("you can't pass both embed and embeds.")
        if file:
            files = [file]
        if files:
            for x in range(len(files)):
                sel = files[x]
                if not isinstance(sel, io.FileIO):
                    files[x] = open(sel, "rb")
        if embed:
            embeds = [embed]
        if embeds:
            embeds = [x.to_dict() for x in embeds if not isinstance(x, dict)]
        params = {"application_id": application_id or self.application_id,
                  "interaction_token": interaction_token or interaction.token,
                  "content": content,
                  "username": username,
                  "avatar_url": avatar_url,
                  "tts": tts,
                  "embeds": embeds,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions)}
        if files:
            params["files"] = files
        if ephemeral:
            params["flags"] = 64
        try:
            msg = self.http.create_followup_message(**params)
            if isinstance(msg, dict):
                return Message.create(self, msg, interaction_token=interaction_token or interaction.token)
            return msg
        finally:
            if files:
                [x.close() for x in files if not x.closed]

    def edit_interaction_response(self,
                                  interaction: typing.Union[int, str, Snowflake, Interaction] = None,
                                  message: typing.Union[int, str, Snowflake, Message] = "@original",
                                  *,
                                  interaction_token: str = None,
                                  application_id: typing.Union[int, str, Snowflake] = None,
                                  content: str = None,
                                  file: typing.Union[io.FileIO, pathlib.Path, str] = None,
                                  files: typing.List[typing.Union[io.FileIO, pathlib.Path, str]] = None,
                                  embed: typing.Union[Embed, dict] = None,
                                  embeds: typing.List[typing.Union[Embed, dict]] = None,
                                  allowed_mentions: typing.Union[AllowedMentions, dict] = None,
                                  attachments: typing.List[typing.Union[Attachment, dict]] = None):
        if not application_id and not self.application_id:
            raise TypeError("you must pass application_id if it is not set in client instance.")
        if not isinstance(interaction, Interaction) and not interaction_token:
            raise TypeError("you must pass interaction_token if interaction is not dico.Interaction object.")
        if file and files:
            raise TypeError("you can't pass both file and files.")
        if embed and embeds:
            raise TypeError("you can't pass both embed and embeds.")
        if file:
            files = [file]
        if files:
            for x in range(len(files)):
                sel = files[x]
                if not isinstance(sel, io.FileIO):
                    files[x] = open(sel, "rb")
        if embed:
            embeds = [embed]
        if embeds:
            embeds = [x.to_dict() for x in embeds if not isinstance(x, dict)]
        _att = []
        if attachments:
            for x in attachments:
                if not isinstance(x, dict):
                    x = x.to_dict()
                _att.append(x)
        params = {"application_id": application_id or self.application_id,
                  "interaction_token": interaction_token or interaction.token,
                  "message_id": int(message) if message != "@original" else message,
                  "content": content,
                  "embeds": embeds,
                  "files": files,
                  "allowed_mentions": self.get_allowed_mentions(allowed_mentions),
                  "attachments": _att}
        try:
            msg = self.http.edit_interaction_response(**params)
            if isinstance(msg, dict):
                return Message.create(self, msg, interaction_token=interaction_token or interaction.token, original_response=message is None or message == "@original")
            return msg
        finally:
            if files:
                [x.close() for x in files if not x.closed]

    @property
    def edit_followup_message(self):
        return self.edit_interaction_response

    def delete_interaction_response(self,
                                    interaction: typing.Union[int, str, Snowflake, Interaction] = None,
                                    message: typing.Union[int, str, Snowflake, Message] = "@original",
                                    *,
                                    interaction_token: str = None,
                                    application_id: typing.Union[int, str, Snowflake] = None):
        if not application_id and not self.application_id:
            raise TypeError("you must pass application_id if it is not set in client instance.")
        if not isinstance(interaction, Interaction) and not interaction_token:
            raise TypeError("you must pass interaction_token if interaction is not dico.Interaction object.")
        return self.http.delete_interaction_response(application_id or self.application_id, interaction_token or interaction.token, int(message) if message != "@original" else message)

    # Misc

    def get_allowed_mentions(self, allowed_mentions):
        _all_men = allowed_mentions or self.default_allowed_mentions
        if _all_men and not isinstance(_all_men, dict):
            _all_men = _all_men.to_dict()
        return _all_men

    @property
    def has_cache(self):
        return hasattr(self, "cache")
