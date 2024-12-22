from aiortc import RTCPeerConnection, RTCSessionDescription
from quic_telephony.recorder import CallRecorder


class MediaHandler:
    def __init__(self, protocol):
        self.protocol = protocol
        self.peer_connections = {}
        self.recorders = {}

    async def handle_offer(self, payload):
        user_id, sdp = payload.split("|", 1)
        peer_connection = RTCPeerConnection()
        self.peer_connections[user_id] = peer_connection

        # Set up recording
        recorder = CallRecorder(f"call_{user_id}.mp4")
        self.recorders[user_id] = recorder

        @peer_connection.on("track")
        async def on_track(track):
            print(f"Track received: {track.kind}")
            await recorder.add_track(track)

        # Process the SDP offer
        offer = RTCSessionDescription(sdp=sdp, type="offer")
        await peer_connection.setRemoteDescription(offer)
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)

        # Start recording
        await recorder.start()
        return f"ANSWER {user_id}|{peer_connection.localDescription.sdp}"

    async def handle_answer(self, payload):
        user_id, sdp = payload.split("|", 1)
        peer_connection = self.peer_connections.get(user_id)
        if not peer_connection:
            return f"ERROR User {user_id} not found"

        answer = RTCSessionDescription(sdp=sdp, type="answer")
        await peer_connection.setRemoteDescription(answer)
        print(f"SDP Answer set for user {user_id}")
        return f"ANSWER_ACCEPTED {user_id}"

    async def handle_bye(self, payload):
        user_id = payload.strip()
        peer_connection = self.peer_connections.pop(user_id, None)
        recorder = self.recorders.pop(user_id, None)

        if peer_connection:
            await peer_connection.close()
        if recorder:
            await recorder.stop()

        return f"CALL ENDED {user_id}"
