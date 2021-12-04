import time
import asyncio
import logging

import aiohttp

from typing import TYPE_CHECKING, Optional, List, Union

from .encryptor import Encryptor
from .voice_socket import VoiceSocket
from ..model import VoiceOpcodes, GatewayResponse, SpeakingFlags
from ..ws.websocket import Ignore, WSClosing

if TYPE_CHECKING:
    from ..client import Client
    from ..model import VoiceServerUpdate, VoiceState, Snowflake


class VoiceWebsocket:
    AVAILABLE_MODES = Encryptor.AVAILABLE
    WS_KWARGS = {"autoclose": False, "autoping": False, "timeout": 60}

    def __init__(self, ws: aiohttp.ClientWebSocketResponse, client: "Client", payload: "VoiceServerUpdate", voice_state: "VoiceState"):
        self.client: "Client" = client
        self.ws: aiohttp.ClientWebSocketResponse = ws
        self.guild_id: "Snowflake" = payload.guild_id
        self.endpoint: str = f"wss://{payload.endpoint}?v=4"
        self.token: str = payload.token
        self.session_id = voice_state.session_id
        self.logger: logging.Logger = logging.getLogger(f"dico.voice.{self.guild_id}")
        self.__keep_running: bool = True
        self.ssrc: Optional[int] = None
        self.ip: Optional[str] = None
        self.port: Optional[int] = None
        self.modes: Optional[List[str]] = None
        self.heartbeat_interval: Optional[int] = None
        self._reconnecting: bool = False
        self._fresh_reconnecting: bool = False
        self.last_heartbeat_ack: float = 0
        self.last_heartbeat_send: float = 0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.ping: float = 0.0
        self._ping_start: float = 0.0
        self.mode: Optional[str] = None
        self.sock = None
        self.secret_key: Optional[list] = None
        self.encryptor: Optional[Encryptor] = None
        self.self_ip: Optional[str] = None
        self.self_port: Optional[int] = None

    def get_mode(self) -> str:
        return [x for x in self.modes if x in self.AVAILABLE_MODES][0]

    async def close(self, code: int = 1000, reconnect: bool = False):
        await self.cancel_heartbeat()
        if not self.__keep_running:
            return
        if self.sock:
            self.sock.close()
        if not self.ws.closed:
            await self.ws.close(code=code)
        self.__keep_running = reconnect

    async def run(self):
        while self.__keep_running:
            if self._reconnecting:
                await self.resume()
            else:
                await self.identify()
            while not self.ws.closed:
                try:
                    msg = await self.ws.receive()
                    resp = await self.receive(msg)
                except Ignore:
                    continue
                except WSClosing as ex:
                    self.logger.warning(f"Voice websocket is closing with code: {ex.code}")
                    if self.sock:
                        pass
                    if ex.code in (4006, 4009):
                        await self.reconnect(fresh=True)
                    elif ex.code in (4015,):
                        await self.reconnect()
                    else:
                        await self.close(code=ex.code)
                    break
                value = await self.process(resp)
            if self._reconnecting or self._fresh_reconnecting:
                self.ws = await self.client.http.session.ws_connect(self.endpoint, **self.WS_KWARGS)
            else:
                self.__keep_running = False

    async def receive(self, resp: aiohttp.WSMessage) -> GatewayResponse:
        self.logger.debug(f"Voice raw receive {resp.type}: {resp.data}")
        if resp.type == aiohttp.WSMsgType.TEXT:
            return GatewayResponse(resp.json())
        elif resp.type == aiohttp.WSMsgType.CONTINUATION:
            raise Ignore
        elif resp.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
            raise WSClosing(resp.data or self.ws.close_code)

    async def process(self, resp: GatewayResponse):
        if resp.op == VoiceOpcodes.READY:
            self.ssrc = resp.d["ssrc"]
            self.ip = resp.d["ip"]
            self.port = resp.d["port"]
            self.modes = resp.d["modes"]
            self.mode = self.get_mode()
            self.sock = await VoiceSocket.connect(self, ip_discovery=not bool(self.self_ip and self.self_port))
            await self.select_protocol()
        elif resp.op == VoiceOpcodes.HELLO:
            self.heartbeat_interval = resp.d["heartbeat_interval"]
            self._heartbeat_task = self.client.loop.create_task(self.run_heartbeat())
        elif resp.op == VoiceOpcodes.HEARTBEAT_ACK:
            self.last_heartbeat_ack = time.time()
            self.ping = self.last_heartbeat_ack - self._ping_start
        elif resp.op == VoiceOpcodes.SESSION_DESCRIPTION:
            self.secret_key = resp.d["secret_key"]
            self.encryptor = Encryptor(self.secret_key)

    async def reconnect(self, fresh: bool = False):
        if self._reconnecting or self._fresh_reconnecting:
            self.logger.warning("Reconnection is already running, but another reconnection is requested. This request is ignored.")
            return
        await self.cancel_heartbeat()
        self._reconnecting = not fresh
        self._fresh_reconnecting = fresh
        self.logger.info("Reconnecting to Websocket...")
        if not self.ws.closed:
            await self.close(4000, reconnect=True)

    async def identify(self):
        payload = {
            "op": VoiceOpcodes.IDENTIFY,
            "d": {
                "server_id": str(self.guild_id),
                "user_id": str(self.client.user.id),
                "session_id": self.session_id,
                "token": self.token,
            }
        }
        await self.ws.send_json(payload)

    async def resume(self):
        payload = {
            "op": VoiceOpcodes.RESUME,
            "d": {
                "server_id": str(self.guild_id),
                "session_id": self.session_id,
                "token": self.token,
            }
        }
        await self.ws.send_json(payload)
        self._reconnecting = False

    async def select_protocol(self):
        payload = {
            "op": VoiceOpcodes.SELECT_PROTOCOL,
            "d": {
                "protocol": "udp",
                "data": {
                    "address": self.self_ip,
                    "port": self.self_port,
                    "mode": self.mode,
                },
            }
        }
        print(payload)
        await self.ws.send_json(payload)

    async def speaking(self, speaking_flag: Union[SpeakingFlags, int] = SpeakingFlags.MICROPHONE, is_speaking: bool = True):
        payload = {
            "op": VoiceOpcodes.SPEAKING,
            "d": {
                "speaking": speaking_flag if is_speaking else 0,
                "delay": 0,
                "ssrc": self.ssrc
            }
        }
        await self.ws.send_json(payload)

    async def run_heartbeat(self):
        try:
            while self:
                if self._reconnecting or self._fresh_reconnecting:
                    break  # Just making sure
                if not self.last_heartbeat_send <= self.last_heartbeat_ack <= time.time():
                    if self._reconnecting or self._fresh_reconnecting:
                        break
                    self.logger.warning("Heartbeat timeout, reconnecting...")
                    self.loop.create_task(self.reconnect())
                    break
                data = {"op": VoiceOpcodes.HEARTBEAT, "d": 1501184119561}
                self._ping_start = time.time()
                await self.ws.send_json(data)
                self.last_heartbeat_send = time.time()
                await asyncio.sleep(self.heartbeat_interval / 1000)
        except asyncio.CancelledError:
            return

    async def cancel_heartbeat(self):
        if self._heartbeat_task.cancelled():
            return
        self.last_heartbeat_ack = 0
        self.last_heartbeat_send = 0
        self._heartbeat_task.cancel()
        try:
            await self._heartbeat_task
        except asyncio.CancelledError:
            pass

    def set_self_ip(self, self_ip, self_port):
        self.self_ip = self_ip
        self.self_port = self_port

    @property
    def loop(self):
        return self.client.loop

    @property
    def parent_ws(self):
        return self.client.ws if not self.client.monoshard else self.client.get_shard(self.guild_id)

    @classmethod
    async def connect(cls, client: "Client", payload: "VoiceServerUpdate", voice_state: "VoiceState"):
        url = f"wss://{payload.endpoint}?v=4"
        ws = await client.http.session.ws_connect(url, **cls.WS_KWARGS)
        resp = cls(ws, client, payload, voice_state)
        return resp
