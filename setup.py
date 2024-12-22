from setuptools import setup, find_packages

setup(
    name="quic_telephony",
    version="0.1.0",
    description="A QUIC-based WebRTC telephony server with call recording.",
    author="Jyrone Parker",
    author_email="jyrone.parker@gmail.com",
    packages=find_packages(),
    install_requires=[
        "aioquic",
        "aiortc",
    ],
    entry_points={
        "console_scripts": [
            "quic_telephony=quic_telephony.protocol:main",
        ],
    },
)
