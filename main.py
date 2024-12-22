from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from quic_telephony.protocol import QuicCallProtocol

async def main():
    configuration = QuicConfiguration(is_client=False)
    configuration.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    await serve(
        "0.0.0.0",
        4433,
        configuration=configuration,
        create_protocol=QuicCallProtocol,
    )


# Uncomment to run the server
# asyncio.run(main())
