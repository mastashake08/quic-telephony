import logging
from typing import Dict, Optional

from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import (
    HeadersReceived,
    DatagramReceived,
    WebTransportStreamDataReceived,
    H3Event
)
from collections import deque
import asyncio
from aioquic.quic.events import ProtocolNegotiated, QuicEvent
from typing import Deque, Dict, Optional
from quic_telephony.sessions import WebTransportHandler

logger = logging.getLogger(__name__)


class WebTransportServerProtocol(QuicConnectionProtocol):
    """
    HTTP/3 server protocol with WebTransport support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http: Optional[H3Connection] = None
        self._sessions: Dict[int, WebTransportHandler] = {}
        self.http_event_queue: Deque[H3Event] = deque()
        self.queue: asyncio.Queue[Dict] = asyncio.Queue()

    def quic_event_received(self, event: QuicEvent):
        """
        Handle QUIC-level events.
        """
        if isinstance(event, ProtocolNegotiated):
            self._http = H3Connection(self._quic, enable_webtransport=True)
        if isinstance(event, WebTransportStreamDataReceived):
                    self.queue.put_nowait(
                        {
                            "data": event.data,
                            "stream": event.stream_id,
                            "type": "webtransport.stream.receive",
                        }
                    )

        # Pass event to HTTP/3 layer
        if self._http:
            for http_event in self._http.handle_event(event):
                self.http_event_received(http_event)

    def http_event_received(self, event):
        """
        Handle HTTP/3 events, including WebTransport sessions.
        """
        if isinstance(event, HeadersReceived):
            self.handle_headers(event)
        elif isinstance(event, DatagramReceived):
            self.queue.put_nowait(
                        {
                            "data": event.data,
                            "type": "webtransport.datagram.receive",
                        }
                    )
            self.handle_datagram(event)
        elif isinstance(event, WebTransportStreamDataReceived):
            self.handle_stream_data(event)

    def handle_headers(self, event: HeadersReceived):
        """
        Process HTTP/3 headers and establish WebTransport sessions.
        """
        headers = {k.decode(): v.decode() for k, v in event.headers}
        if headers.get(":method") == "CONNECT" and headers.get(":protocol") == "webtransport":
            handler = WebTransportHandler(connection=self._http, stream_id=event.stream_id)
            handler.accept_session()
            self._sessions[event.stream_id] = handler
        else:
            self._http.send_headers(
                stream_id=event.stream_id, headers=[(b":status", b"405")]
            )
            

    def handle_datagram(self, event: DatagramReceived):
        """
        Process received WebTransport datagrams.
        """
        for session in self._sessions.values():
            session.http_event_received(event)

    def handle_stream_data(self, event: WebTransportStreamDataReceived):
        """
        Process received WebTransport stream data.
        """
        handler = self._sessions.get(event.session_id)
        if handler:
            handler.http_event_received(event)
