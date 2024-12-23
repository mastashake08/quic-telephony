import argparse
import asyncio
import logging
from typing import Dict, List, Optional

from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.asyncio import serve
from aioquic.h3.connection import H3Connection, H3_ALPN
from aioquic.h3.events import DatagramReceived, HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

SERVER_NAME = "WebRTC Signaling Server"

# In-memory store for registered users
registered_users: Dict[str, QuicConnectionProtocol] = {}


class SignalingServerProtocol(QuicConnectionProtocol):
    """
    HTTP/3-based signaling server protocol.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http: Optional[H3Connection] = None

    def quic_event_received(self, event: QuicEvent):
        """
        Handle QUIC events.
        """
        if self._http is None:
            self._http = H3Connection(self._quic, enable_webtransport=True)

        # Pass QUIC events to HTTP/3 layer
        for http_event in self._http.handle_event(event):
            self.http_event_received(http_event)

    def http_event_received(self, event):
        """
        Handle HTTP/3 events, including WebTransport sessions.
        """
        if isinstance(event, HeadersReceived):
            self.handle_headers(event)
        elif isinstance(event, DatagramReceived):
            self.handle_datagram(event.data)

    def handle_headers(self, event: HeadersReceived):
        """
        Handle HTTP/3 headers to establish WebTransport sessions.
        """
        headers = {k.decode(): v.decode() for k, v in event.headers}
        logging.info(headers)
        if headers.get(":method") == "CONNECT" and headers.get(":protocol") == "webtransport":
            # Accept the WebTransport session
            headers = [
            (b":status", b"200"),
            (b"sec-webtransport-http3-draft", b"draft02"),
        ]
            self._http.send_headers(
                stream_id=event.stream_id,
                headers=headers,
            )
            logging.info(f"WebTransport session established on stream {event.stream_id}")
            self.send_datagram("ERROR Unknown command")
        else:
            # Reject unsupported requests
            self._http.send_headers(
                stream_id=event.stream_id, headers=[(b":status", b"405")]
            )
            self._http.reset_stream(event.stream_id)
    def handle_datagram(self, data: bytes):
            """
            Process signaling commands sent as WebTransport datagrams.
            """
            logging.info(data)
            try:
                message = data.decode()
                command, *args = message.split(" ", 1)
                payload = args[0] if args else ""

                if command == "REGISTER":
                    self.register_user(payload)
                elif command == "CALL":
                    self.handle_call(payload)
                elif command == "ANSWER":
                    self.handle_answer(payload)
                elif command == "BYE":
                    self.handle_bye(payload)
                elif command == "DIRECTORY":
                    self.send_directory()
                else:
                    self.send_datagram("ERROR Unknown command")
            except Exception as e:
                logging.error(f"Error processing datagram: {e}")
                self.send_datagram("ERROR Processing command")

    def register_user(self, user_id: str):
        """
        Register a user with the server.
        """
        registered_users[user_id] = self
        logging.info(f"User registered: {user_id}")
        self.send_datagram(f"REGISTERED {user_id}")

    def handle_call(self, payload: str):
        """
        Forward an SDP offer to the specified user.
        """
        try:
            target_user, sdp_offer = payload.split("|", 1)
            target_protocol = registered_users.get(target_user)
            if target_protocol:
                target_protocol.send_datagram(f"CALL {sdp_offer}")
                self.send_datagram(f"CALL_SENT {target_user}")
                logging.info(f"CALL sent from {self._quic} to {target_user}")
            else:
                self.send_datagram(f"ERROR User {target_user} not found")
        except ValueError:
            self.send_datagram("ERROR Invalid CALL format")

    def handle_answer(self, payload: str):
        """
        Forward an SDP answer to the specified user.
        """
        try:
            target_user, sdp_answer = payload.split("|", 1)
            target_protocol = registered_users.get(target_user)
            if target_protocol:
                target_protocol.send_datagram(f"ANSWER {sdp_answer}")
                self.send_datagram(f"ANSWER_SENT {target_user}")
                logging.info(f"ANSWER sent from {self._quic} to {target_user}")
            else:
                self.send_datagram(f"ERROR User {target_user} not found")
        except ValueError:
            self.send_datagram("ERROR Invalid ANSWER format")

    def handle_bye(self, user_id: str):
        """
        End a call with the specified user.
        """
        target_protocol = registered_users.get(user_id)
        if target_protocol:
            target_protocol.send_datagram(f"BYE")
            self.send_datagram(f"BYE_SENT {user_id}")
            logging.info(f"BYE sent to {user_id}")
        else:
            self.send_datagram(f"ERROR User {user_id} not found")

    def send_directory(self):
        """
        Send the list of registered user IDs to the client.
        """
        directory = " ".join(registered_users.keys())
        self.send_datagram(f"DIRECTORY {directory}")
        logging.info(f"DIRECTORY sent: {directory}")

    def send_datagram(self, message: str):
        """
        Send a datagram back to the client.
        """
        logging.info("Sending data....")
        self._quic.send_datagram_frame(data=message.encode())


async def main():
    """
    Start the signaling server and keep it running indefinitely.
    """
    configuration = QuicConfiguration(is_client=False, alpn_protocols=["h3"])
    configuration.load_cert_chain(certfile="tests/cert.pem", keyfile="tests/key.pem")

    logging.info("Starting signaling server...")
    server = await serve(
        "localhost",
        4433,
        configuration=configuration,
        create_protocol=SignalingServerProtocol,
    )
    logging.info("Signaling server running on https://0.0.0.0:4433")

    try:
        await asyncio.Future()  # Keep the server running indefinitely
    except KeyboardInterrupt:
        logging.info("Shutting down signaling server...")
        server.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
