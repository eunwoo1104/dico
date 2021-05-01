from ..base.model import DiscordObjectBase, FlagBase, TypeBase


class User(DiscordObjectBase):
    def __init__(self, client, resp):
        super().__init__(client, resp)
        self._cache_type = "user"
        self.username = resp["username"]
        self.discriminator = resp["discriminator"]
        self.avatar = resp["avatar"]
        self.bot = resp.get("bot", False)
        self.system = resp.get("system", False)
        self.mfa_enabled = resp.get("mfa_enabled", False)
        self.locale = resp.get("locale")
        self.verified = resp.get("verified", False)
        self.email = resp.get("email")
        self.flags = UserFlags.from_value(resp.get("flags", 0))
        self.premium_type = PremiumTypes(resp.get("premium_type", 0))
        self.public_flags = UserFlags.from_value(resp.get("public_flags", 0))

    def __str__(self):
        return f"{self.username}#{self.discriminator}"

    @property
    def mention(self):
        return f"<@{self.id}>"


class UserFlags(FlagBase):
    NONE = 0
    DISCORD_EMPLOYEE = 1 << 0
    PARTNERED_SERVER_OWNER = 1 << 1
    HYPESQUAD_EVENTS = 1 << 2
    BHG_HUNTER_LEVEL_1 = 1 << 3
    HOUSE_BRAVERY = 1 << 6
    HOUSE_BRILLIANCE = 1 << 7
    HOUSE_BALANCE = 1 << 8
    EARLY_SUPPORTER = 1 << 9
    TEAM_USER = 1 << 10
    BHG_HUNTER_LEVEL_2 = 1 << 14
    VERIFIED_BOT = 1 << 16
    EARLY_VERIFIED_BOT_DEVELOPER = 1 << 17


class PremiumTypes(TypeBase):
    NONE = 0
    NITRO_CLASSIC = 1
    NITRO = 2