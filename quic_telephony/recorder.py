from aiortc.contrib.media import MediaRecorder

class CallRecorder:
    def __init__(self, filename):
        self.recorder = MediaRecorder(filename)

    async def start(self, track):
        await self.recorder.addTrack(track)
        await self.recorder.start()

    async def stop(self):
        await self.recorder.stop()
