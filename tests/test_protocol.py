import pytest
from quic_telephony.protocol import QuicCallProtocol


@pytest.mark.asyncio
async def test_handle_datagram():
    protocol = QuicCallProtocol()
    response = await protocol.handle_datagram(b"REGISTER user123", None)
    assert response == b"REGISTERED user123"
