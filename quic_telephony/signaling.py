from quic_telephony.sessions import SessionManager
from quic_telephony.media import MediaHandler


class SignalingHandler:
    def __init__(self, protocol):
        self.protocol = protocol
        self.commands = {
            "REGISTER": self.handle_register,
            "OFFER": self.handle_offer,
            "ANSWER": self.handle_answer,
            "BYE": self.handle_bye,
        }

    async def handle_command(self, command, payload):
        handler = self.commands.get(command)
        if handler:
            return await handler(payload)
        return "ERROR Invalid command"

    async def handle_register(self, payload):
        user_id = payload.strip()
        session_ticket = self.protocol._quic.tls.session_ticket
        if session_ticket:
            self.protocol.session_manager.save_session(session_ticket, user_id)
            print(f"User {user_id} registered with session ticket")
        return f"REGISTERED {user_id}"

    async def handle_offer(self, payload):
        return await self.protocol.media_handler.handle_offer(payload)

    async def handle_answer(self, payload):
        return await self.protocol.media_handler.handle_answer(payload)

    async def handle_bye(self, payload):
        return await self.protocol.media_handler.handle_bye(payload)
