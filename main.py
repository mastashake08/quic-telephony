import asyncio
import logging
from typing import Dict, Optional
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.asyncio import serve
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import (
    HeadersReceived,
    DatagramReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

logging.basicConfig(level=logging.DEBUG)

# Global registry of connected clients
clients: Dict[str, "WebTransportHandler"] = {}


class WebTransportHandler:
    def __init__(self, connection: H3Connection, stream_id: int):
        self._http = connection
        self.stream_id = stream_id
        self.user_id: Optional[str] = None

    def register(self, user_id: str):
        """
        Register a user and associate it with this handler.
        """
        global clients
        self.user_id = user_id
        clients[user_id] = self
        logging.info(f"User registered: {user_id}")
        logging.info(self)
        # self.send_datagram(user_id=self.stream_id,  message=f"REGISTERED {user_id}".encode())
        # self._http.send_data(stream_id=self.stream_id,  data=f"REGISTERED {user_id}".encode(), end_stream=False)
        return f"REGISTERED {user_id}".encode()

    def send_datagram(self, message: str, user_id):
        """
        Send a datagram back to the client.
        """
        self._http.send_datagram(data=message, stream_id=user_id)

    def handle_call(self, payload: str):
        """
        Forward an SDP offer to the target user.
        """
        try:
            logging.info(payload)
            global clients
            target_user, sdp_offer = payload.split("|", 1)
            logging.info("GETTING USER")
            logging.info(target_user)
            target_handler = clients[target_user]
            logging.info(target_handler)
            return target_user, sdp_offer, target_handler
        except ValueError:
            self.send_datagram(message=b"ERROR Invalid CALL format", user_id=self.stream_id)

    def handle_answer(self, payload: str):
        """
        Forward an SDP answer to the calling user.
        """
        try:
            target_user, sdp_answer = payload.split("|", 1)
            target_handler = clients.get(target_user)
            if target_handler:
                target_handler.send_datagram(f"ANSWER {self.user_id}|{sdp_answer}")
                self.send_datagram(f"ANSWER_SENT {target_user}")
                logging.info(f"ANSWER sent from {self.user_id} to {target_user}")
            else:
                self.send_datagram(f"ERROR User {target_user} not found")
        except ValueError:
            self.send_datagram("ERROR Invalid ANSWER format")

    def handle_bye(self, target_user: str):
        """
        Send a BYE command to the target user.
        """
        target_handler = clients.get(target_user)
        if target_handler:
            target_handler.send_datagram(f"BYE {self.user_id}")
            self.send_datagram(f"BYE_SENT {target_user}")
            logging.info(f"BYE sent from {self.user_id} to {target_user}")
        else:
            self.send_datagram(f"ERROR User {target_user} not found")


class WebTransportServerProtocol(QuicConnectionProtocol):
    """
    HTTP/3-based WebTransport server protocol.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http = None
        self._handlers: Dict[int, WebTransportHandler] = {}

    def quic_event_received(self, event: QuicEvent):
        """
        Handle QUIC events and route them to HTTP/3.
        """
        if self._http is None:
            self._http = H3Connection(self._quic, enable_webtransport=True)

        for http_event in self._http.handle_event(event):
            self.http_event_received(http_event)

    def http_event_received(self, event):
        """
        Handle HTTP/3 events, including WebTransport requests.
        """
        logging.info(event)

        if isinstance(event, HeadersReceived):
            self.handle_headers(event)
            return

        if isinstance(event, DatagramReceived):
            self._handle_datagram_event(event)
            return

        if isinstance(event, WebTransportStreamDataReceived):
            self._handle_webtransport_stream_event(event)
            return

    def _handle_datagram_event(self, event):
        handler = self._handlers.get(event.stream_id)
        logging.info(handler)
        if handler:
            self.handle_datagram(handler, event.data)

    def _handle_webtransport_stream_event(self, event):
        handler = self._handlers.get(event.session_id)
        logging.info(handler)
        if handler:
            self.handle_webtransport_stream(handler, event.data)

    def handle_headers(self, event: HeadersReceived):
        """
        Handle HTTP/3 headers for WebTransport.
        """
        headers = {k.decode(): v.decode() for k, v in event.headers}
        if headers.get(":method") == "CONNECT" and headers.get(":protocol") == "webtransport":
            self._http.send_headers(
                stream_id=event.stream_id,
                headers=[(b":status", b"200"), (b"sec-webtransport-http3-draft", b"draft02")],
            )
            logging.info(f"WebTransport session established on stream {event.stream_id}")
            self._handlers[event.stream_id] = WebTransportHandler(self._http, event.stream_id)
        else:
            self._http.send_headers(
                stream_id=event.stream_id, headers=[(b":status", b"405")]
            )
            self._http.reset_stream(event.stream_id)

    def handle_datagram(self, handler: WebTransportHandler, data: bytes):
        """
        Process datagrams for signaling commands.
        """
        try:
            message = data.decode()
            command, *args = message.split(" ", 1)
            payload = args[0] if args else ""

            if command == "REGISTER":
                message = handler.register(payload)
                handler.send_datagram(message)
            elif command == "CALL":
                handler.handle_call(payload)
            elif command == "ANSWER":
                handler.handle_answer(payload)
            elif command == "BYE":
                handler.handle_bye(payload)
            elif command == "DIRECTORY":
                clients_list = self.get_connected_clients()
                handler.send_datagram(f"CONNECTED CLIENTS: {', '.join(clients_list)}")
            else:
                handler.send_datagram("ERROR Unknown command")
        except Exception as e:
            logging.error(f"Error processing datagram: {e}")
            handler.send_datagram(message="ERROR Processing command", user_id=self.stream_id)

    def get_connected_clients(self):
        # Assuming self._handlers contains the connected clients
        return list(self._handlers.keys())

    def handle_stream(self, handler: WebTransportHandler, data: bytes, stream_id: int):
        """
        Handle stream data for WebTransport.
        """
        try:
            message = data.decode()
            command, *args = message.split(" ", 1)
            payload = args[0] if args else ""
            logging.info(command)
            if command == "REGISTER":
               register =  handler.register(payload)
               self._quic.send_stream_data(stream_id, register, end_stream=False)
            elif command == "CALL":
                target_user, sdp_offer, target_handler = handler.handle_call(payload)
                
                #self._quic.send_stream_data(target_handler.stream_id, sdp_offer.encode(), end_stream=False)
                self._quic.send_stream_data(stream_id, f"Offer sent {sdp_offer}".encode(), end_stream=False)
            elif command == "ANSWER":
                handler.handle_answer(payload)
            elif command == "BYE":
                handler.handle_bye(payload)
            else:
                response_message = f"ERROR Unknown command"
                self._quic.send_stream_data(stream_id, response_message.encode(), end_stream=False)
            
        except Exception as e:
            logging.error(f"Error processing stream {stream_id}: {e}")

async def stream_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Handle incoming stream data and map to the appropriate client.
    """
    try:
       logging.info("READER")
       logging.info(writer) 
    except Exception as e:
        logging.error(e)

async def main():
    """
    Start the standalone WebTransport signaling server.
    """
    configuration = QuicConfiguration(is_client=False, alpn_protocols=["h3"])
    configuration.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    await serve(
        "localhost",
        4433,
        configuration=configuration,
        create_protocol=WebTransportServerProtocol,
        stream_handler=stream_handler
    )
    await asyncio.Future()  # Run indefinitely


if __name__ == "__main__":
    asyncio.run(main())
