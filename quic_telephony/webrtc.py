import logging
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

logger = logging.getLogger(__name__)


class WebRTCConnection:
    """
    Manages a WebRTC connection for a user.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.peer_connection = RTCPeerConnection()
        self.recorder = MediaRecorder(f"call_{user_id}.mp4")

        @self.peer_connection.on("track")
        async def on_track(track):
            logger.info(f"Track received: {track.kind}")
            await self.recorder.addTrack(track)

    async def handle_offer(self, sdp: str) -> str:
        """
        Process SDP offer and generate an SDP answer.
        """
        logger.info(f"Processing SDP offer for user {self.user_id}")
        offer = RTCSessionDescription(sdp=sdp, type="offer")
        await self.peer_connection.setRemoteDescription(offer)
        answer = await self.peer_connection.createAnswer()
        await self.peer_connection.setLocalDescription(answer)

        # Start recording
        await self.recorder.start()

        return self.peer_connection.localDescription.sdp

    async def close(self):
        """
        Close the WebRTC connection and stop recording.
        """
        await self.peer_connection.close()
        await self.recorder.stop()
