import typing


class GetGateway:
    def __init__(self, resp: dict):
        self.url: str = resp["url"]
        self.shards: typing.Optional[int] = resp.get("shards", 0)
        self.session_start_limit: typing.Optional[SessionStartLimit] = SessionStartLimit.optional(resp.get("session_start_limit"))

    def to_dict(self):
        return {"url": self.url, "shards": self.shards, "session_start_limit": self.session_start_limit}


class SessionStartLimit:
    def __init__(self, resp: dict):
        self.total = resp["total"]
        self.remaining = resp["remaining"]
        self.reset_after = resp["reset_after"]
        self.max_concurrency = resp["max_concurrency"]

    @classmethod
    def optional(cls, resp: dict):
        if resp:
            return cls(resp)

    def to_dict(self):
        return {"total": self.total, "remaining": self.remaining, "reset_after": self.reset_after, "max_concurrency": self.max_concurrency}


class Intents:

    values = {
        "GUILDS": 1 << 0,
        "GUILD_MEMBERS": 1 << 1,
        "GUILD_BANS": 1 << 2,
        "GUILD_EMOJIS": 1 << 3,
        "GUILD_INTEGRATIONS": 1 << 4,
        "GUILD_WEBHOOKS": 1 << 5,
        "GUILD_INVITES": 1 << 6,
        "GUILD_VOICE_STATES": 1 << 7,
        "GUILD_PRESENCES": 1 << 8,
        "GUILD_MESSAGES": 1 << 9,
        "GUILD_MESSAGE_REACTIONS": 1 << 10,
        "GUILD_MESSAGE_TYPING": 1 << 11,
        "DIRECT_MESSAGES": 1 << 12,
        "DIRECT_MESSAGE_REACTIONS": 1 << 13,
        "DIRECT_MESSAGE_TYPING": 1 << 14,
    }

    def __init__(self, *args):
        self.enabled = []
        self.__setattr__ = self.__setattr
        for x in args:
            if x.upper() not in self.values.keys():
                raise
            self.enabled.append(x.upper())

    def __int__(self):
        return sum([self.values[x] for x in self.enabled])

    def __setattr(self, key, value):
        if not isinstance(value, bool):
            raise TypeError(f"only type `bool` is supported for setting intents.")
        o_key = key
        key = key.upper()
        if key not in self.values.keys():
            raise AttributeError(f"invalid name: `{o_key}`")
        if not value and key in self.enabled:
            self.enabled.remove(key)
        elif value and key not in self.enabled:
            self.enabled.append(key)

    def add(self, value):
        o_value = value
        value = value.upper()
        if value not in self.values.keys():
            raise AttributeError(f"invalid name: `{o_value}`")
        if value not in self.enabled:
            self.enabled.append(value)

    def remove(self, value):
        o_value = value
        value = value.upper()
        if value not in self.values.keys():
            raise AttributeError(f"invalid name: `{o_value}`")
        if value in self.enabled:
            self.enabled.remove(value)

    @classmethod
    def full(cls):
        return cls(*cls.values.keys())

    @classmethod
    def no_privileged(cls):
        ret = cls.full()
        ret.guild_presences = False
        ret.guild_members = False
        return ret


class GatewayResponse:
    def __init__(self, resp: dict):
        self.op = resp["op"]
        self.d = resp.get("d", {})
        self.s = resp.get("s")
        self.t = resp.get("t")

    def to_dict(self):
        return {"op": self.op, "d": self.d, "s": self.s, "t": self.t}


# https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway

class Opcodes:
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

    @staticmethod
    def as_string(code: int):
        opcodes = {0: "Dispatch",
                   1: "Heartbeat",
                   2: "Identify",
                   3: "Presence Update",
                   4: "Voice State Update",
                   6: "Resume",
                   7: "Reconnect",
                   8: "Request Guild Members",
                   9: "Invalid Session",
                   10: "Hello",
                   11: "Heartbeat ACK"}
        return opcodes.get(code)