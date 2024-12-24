#
# demo application for http3_server.py
#

import datetime
import os
from urllib.parse import urlencode

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocketDisconnect

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.environ.get("STATIC_ROOT", os.path.join(ROOT, "htdocs"))
STATIC_URL = "/"
LOGS_PATH = os.path.join(STATIC_ROOT, "logs")
QVIS_URL = "https://qvis.quictools.info/"

async def echo(request):
    """
    HTTP echo endpoint.
    """
    content = await request.body()
    media_type = request.headers.get("content-type")
    return Response(content, media_type=media_type)


async def padding(request):
    """
    Dynamically generated data, maximum 50MB.
    """
    size = min(50000000, request.path_params["size"])
    return PlainTextResponse("Z" * size)


async def ws(websocket):
    """
    WebSocket echo endpoint.
    """
    if "chat" in websocket.scope["subprotocols"]:
        subprotocol = "chat"
    else:
        subprotocol = None
    await websocket.accept(subprotocol=subprotocol)

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(message)
    except WebSocketDisconnect:
        pass


async def wt(scope: Scope, receive: Receive, send: Send) -> None:
    """
    WebTransport signaling endpoint for WebRTC SDP exchange.
    """
    # Accept the WebTransport session
    message = await receive()
    assert message["type"] == "webtransport.connect"
    await send({"type": "webtransport.accept"})

    while True:
        message = await receive()
        if message["type"] == "webtransport.datagram.receive":
            data = message["data"].decode()
            print(f"Received: {data}")

            # Simulate an SDP exchange
            if data.startswith("CALL"):
                target_user, sdp = data.split("|", 1)
                print(f"Forwarding SDP offer to {target_user}")
                await send(
                    {
                        "type": "webtransport.datagram.send",
                        "data": f"SDP offer for {target_user}: {sdp}".encode(),
                    }
                )


starlette = Starlette(
    routes=[
        Route("/{size:int}", padding),
        Route("/echo", echo, methods=["POST"]),
        WebSocketRoute("/ws", ws),
    ]
)


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "webtransport" and scope["path"] == "/wt":
        await wt(scope, receive, send)
    else:
        await starlette(scope, receive, send)