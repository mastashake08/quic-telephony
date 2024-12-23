import logging
from typing import Dict
import asyncio
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import DatagramReceived
from quic_telephony.webrtc import WebRTCConnection

logger = logging.getLogger(__name__)


class WebTransportHandler:
    """
    Handles WebTransport sessions, including datagrams and streams.
    """

    def __init__(self, connection: H3Connection, stream_id: int):
        self.connection = connection
        self.stream_id = stream_id
        self.accepted = False
        self.closed = False
        self.users: Dict[str, WebRTCConnection] = {}

    def http_event_received(self, event):
        """
        Handle HTTP/3 or WebTransport-specific events.
        """
        if isinstance(event, DatagramReceived):
            self.handle_datagram(event.data)

    def accept_session(self):
        """
        Accept a WebTransport session and send appropriate headers.
        """
        self.accepted = True
        headers = [
            (b":status", b"200"),
            (b"sec-webtransport-http3-draft", b"draft02"),
        ]

        self.connection.send_headers(stream_id=self.stream_id, headers=headers)
        
        logger.info(f"WebTransport session accepted on stream {self.stream_id}")

    def handle_datagram(self, data: bytes):
        """
        Handle WebTransport datagrams for signaling commands.
        """
        message = data.decode()
        logger.info(f"Received Datagram: {message}")

        command, *payload = message.split(" ", 1)
        payload = payload[0] if payload else ""

        if command == "REGISTER":
            user_id = payload.strip()
            self.users[user_id] = WebRTCConnection(user_id=user_id)
            self.send_datagram(f"REGISTERED {user_id}")
        elif command == "OFFER":
            user_id, sdp = payload.split("|", 1)
            webrtc_connection = self.users.get(user_id)
            if webrtc_connection:
                asyncio.create_task(self.process_offer(webrtc_connection, user_id, sdp))
            else:
                self.send_datagram(f"ERROR User {user_id} not found")
        elif command == "BYE":
            user_id = payload.strip()
            asyncio.create_task(self.close_connection(user_id))
        else:
            self.send_datagram("ERROR Unknown command")

    async def process_offer(self, webrtc_connection: WebRTCConnection, user_id: str, sdp: str):
        """
        Process the SDP offer and send the SDP answer.
        """
        answer_sdp = await webrtc_connection.handle_offer(sdp)
        self.send_datagram(f"ANSWER {user_id}|{answer_sdp}")

    async def close_connection(self, user_id: str):
        """
        Close a user's WebRTC connection.
        """
        webrtc_connection = self.users.pop(user_id, None)
        if webrtc_connection:
            await webrtc_connection.close()
            self.send_datagram(f"CALL_ENDED {user_id}")
        else:
            self.send_datagram(f"ERROR User {user_id} not found")

    def send_datagram(self, message: str):
        """
        Send a WebTransport datagram to the client.
        """
        self.connection.send_datagram(data=message.encode())
