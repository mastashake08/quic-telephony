from aioquic.asyncio.protocol import QuicConnectionProtocol
from quic_telephony.signaling import SignalingHandler
from quic_telephony.session import SessionManager
from quic_telephony.media import MediaHandler


class QuicCallProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signaling = SignalingHandler(self)
        self.session_manager = SessionManager()
        self.media_handler = MediaHandler(self)

    async def handle_datagram(self, data, addr):
        message = data.decode()
        command, *payload = message.split(" ", 1)
        payload = payload[0] if payload else ""

        if command in self.signaling.commands:
            response = await self.signaling.handle_command(command, payload)
        else:
            response = "ERROR Unknown command"

        if response:
            self._quic.send_datagram(response.encode())
