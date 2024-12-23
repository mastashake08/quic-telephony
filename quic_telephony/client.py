import asyncio
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration


class WebTransportClient:
    def __init__(self, url, port):
        self.url = url
        self.session = None
        self.port = port

    async def connect(self):
        """Establish a WebTransport connection to the server."""
        configuration = QuicConfiguration(is_client=True, alpn_protocols=["h3"])
        configuration.verify_mode = False  # Skip certificate verification for testing

        print(f"Connecting to {self.url}...")
        async with connect(self.url, self.port, configuration=configuration) as session:
            self.session = session
            print(f"Connected to {self.url}")

            # Listen for incoming datagrams
            asyncio.create_task(self.listen_for_datagrams())

            # Example commands
            await self.register("user123")
            await asyncio.sleep(1)

            # Dummy SDP offer (replace with real SDP)
            dummy_sdp_offer = "v=0\no=- 0 0 IN IP4 127.0.0.1\ns=-\nt=0 0\nm=audio 9 RTP/AVP 0\n"
            await self.offer("user123", dummy_sdp_offer)
            await asyncio.sleep(1)

            # Dummy SDP answer (replace with real SDP)
            dummy_sdp_answer = "v=0\no=- 0 0 IN IP4 127.0.0.1\ns=-\nt=0 0\nm=audio 9 RTP/AVP 0\n"
            await self.answer("user123", dummy_sdp_answer)
            await asyncio.sleep(1)

            # End the call
            await self.bye("user123")
            await asyncio.sleep(1)

    async def listen_for_datagrams(self):
        """Listen for server responses."""
        while True:
            datagram = await self.session.receive_datagram()
            if datagram:
                print(f"Received: {datagram.decode()}")

    async def send_command(self, command):
        """Send a command to the server."""
        if not self.session:
            raise ConnectionError("Client is not connected to the server.")
        await self.session.send_datagram(command.encode())
        print(f"Sent: {command}")

    async def register(self, user_id):
        """Register a user with the server."""
        command = f"REGISTER {user_id}"
        await self.send_command(command)

    async def offer(self, user_id, sdp_offer):
        """Send an SDP offer to initiate a call."""
        command = f"OFFER {user_id}|{sdp_offer}"
        await self.send_command(command)

    async def answer(self, user_id, sdp_answer):
        """Send an SDP answer to respond to a call."""
        command = f"ANSWER {user_id}|{sdp_answer}"
        await self.send_command(command)

    async def bye(self, user_id):
        """Terminate a call."""
        command = f"BYE {user_id}"
        await self.send_command(command)


async def main():
    client = WebTransportClient("localhost", port=4433)
    await client.connect()


if __name__ == "__main__":
    asyncio.run(main())
