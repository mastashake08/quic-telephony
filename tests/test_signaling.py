import pytest
from quic_telephony.signaling import SignalingHandler


@pytest.mark.asyncio
async def test_handle_register():
    protocol = mock_protocol()
    signaling = SignalingHandler(protocol)
    response = await signaling.handle_command("REGISTER", "user123")
    assert response == "REGISTERED user123"
