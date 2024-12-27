
# Quic Telephony

**Quic Telephony** is a Python-based server that leverages **QUIC** and **WebRTC** protocols to provide a telephony service with features like call handling, media streaming, call recording, and session persistence using session tickets.

## Features

- **WebRTC Media Streaming**: Supports SDP offers and answers to establish WebRTC connections.
- **Call Recording**: Records audio and/or video streams and saves them to local files.
- **Session Ticket Mapping**: Maintains session tickets to enable persistent user connections across reconnections.
- **QUIC Transport**: Uses QUIC for low-latency and secure signaling.
- **Extendable Architecture**: Modular design for easy extension and customization.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- **QUIC** and **WebRTC** dependencies:
  - `aioquic`
  - `aiortc`

### Install via `pip`

```bash
pip install quic-telephony
```

Alternatively, clone this repository and install locally:

```bash
git clone https://github.com/yourusername/quic-telephony.git
cd quic-telephony
pip install .
```

---

## Usage

### Start the Server

Run the server to listen for incoming QUIC/WebRTC connections.

```bash
python -m quic_telephony.main
```

By default, the server listens on `0.0.0.0:4433`. You can configure the QUIC settings in the `main.py` file.

### Example Commands

#### 1. **Register a User**
Register a user with a `REGISTER` command.

```plaintext
REGISTER user123
```

#### 2. **Initiate a Call**
Send an SDP offer using the `OFFER` command.

```plaintext
OFFER user123|<sdp_offer>
```

#### 3. **Respond to a Call**
Respond with an SDP answer using the `ANSWER` command.

```plaintext
ANSWER user123|<sdp_answer>
```

#### 4. **End a Call**
Terminate a call with the `BYE` command.

```plaintext
BYE user123
```

---

## Features in Detail

### WebRTC Signaling

Handles SDP offer/answer exchange to establish media connections between clients.

- **Commands**:
  - `OFFER`: Initiates a call with an SDP offer.
  - `ANSWER`: Completes the signaling handshake with an SDP answer.

### Call Recording

- Records audio and/or video streams during active calls.
- Saves recordings as `call_<user_id>.mp4` in the server's directory.

### Session Ticket Persistence

- Associates session tickets with user IDs to enable persistent connections.
- Restores user state seamlessly when clients reconnect.

---

## Development

### Setup Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/quic-telephony.git
   cd quic-telephony
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

### Run Tests

Unit tests are located in the `tests/` directory. Use `pytest` to run them:

```bash
pytest
```

### Linting and Formatting

Ensure your code is formatted and follows PEP 8 guidelines:

```bash
black .
flake8 .
```

---

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes with clear messages.
4. Submit a pull request.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

---

## Contact

For questions or suggestions, contact **Your Name** at [your_email@example.com](mailto:your_email@example.com).

