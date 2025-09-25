# 🔌 WebSocket STOMP Client

A simple WebSocket STOMP client written in Python that supports both secure (WSS) and insecure (WS) connections to STOMP message brokers like ActiveMQ.

## ✨ Features

- 🔗 WebSocket (WS) and Secure WebSocket (WSS) support
- 📡 STOMP protocol implementation
- 🧦 SockJS protocol support
- 🔐 SSL certificate verification bypass for self-signed certificates
- 📤 Message publishing and subscription
- 📋 JSON message formatting
- 💓 Heartbeat mechanism
- 🐳 Docker support

## 📦 Installation

### 📋 Prerequisites

- Python 3.7+
- pip

### 🐍 Setup Virtual Environment (Recommended)

It's recommended to use a virtual environment to avoid conflicts with system packages:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 🌍 Alternative: Global Installation

If you prefer to install dependencies globally:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install websocket-client>=1.1.0 stomp.py>=7.0.0 stompest>=2.3.0
```

### 🚀 Running the Script

After setting up the virtual environment, make sure it's activated before running the script:

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Run the script
python wss-stomp-client.py [OPTIONS]
```

## 💻 Usage

### 🎯 Command Line Arguments

```bash
python wss-stomp-client.py [OPTIONS]
```

#### ⚡ Required Arguments

- `--host HOST` - 🖥️ ActiveMQ host (e.g., `activemq.example.com`)
- `--topic TOPIC` - 📝 STOMP topic name (e.g., `/topic/your.topic.name`)
- `--username USERNAME` - 👤 ActiveMQ username
- `--password PASSWORD` - 🔑 ActiveMQ password

#### ⚙️ Optional Arguments

- `--port PORT` - 🔌 ActiveMQ port (default: 61614)
- `--ssl` - 🔒 Enable SSL (WSS). If not set, use plain TCP (WS)
- `--sockjs` - 🧦 Use SockJS protocol
- `--insecure` - ⚠️ Accept self-signed certificates (disable SSL verification)
- `--send SEND` - 📤 Send a message to the topic and exit (optional)
- `--json` - 📋 Format --send payload as JSON (key1=value1 key2=value2)
- `--heartbeat HEARTBEAT` - 💓 Heartbeat interval in seconds (default: 10)
- `--debug` - 🐛 Enable WebSocket debug traces

### 📝 Examples

#### 🔗 Basic Connection (Plain WS)

```bash
python wss-stomp-client.py \
  --host localhost \
  --port 61613 \
  --topic /topic/test \
  --username admin \
  --password admin
```

#### 🔒 Secure Connection (WSS)

```bash
python wss-stomp-client.py \
  --host activemq.example.com \
  --port 61614 \
  --topic /topic/notifications \
  --username myuser \
  --password mypass \
  --ssl
```

#### ⚠️ Connection with Self-Signed Certificate

```bash
python wss-stomp-client.py \
  --host localhost \
  --port 61614 \
  --topic /topic/test \
  --username admin \
  --password admin \
  --ssl \
  --insecure
```

#### 🧦 SockJS Connection

```bash
python wss-stomp-client.py \
  --host localhost \
  --port 8080 \
  --topic /topic/test \
  --username admin \
  --password admin \
  --sockjs
```

#### 📤 Send a Message and Exit

```bash
python wss-stomp-client.py \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --send "Hello, World!"
```

#### 📋 Send JSON Message

```bash
python wss-stomp-client.py \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --send "name=John age=30 city=Paris active=true" \
  --json
```

This will send:

```json
{"name": "John", "age": 30, "city": "Paris", "active": true}
```

## 🐳 Docker Usage

The application is available as a Docker image at [fxrobin/wss-stomp-client:v3](https://hub.docker.com/layers/fxrobin/wss-stomp-client/v3).

### 📥 Pull the Image

```bash
docker pull fxrobin/wss-stomp-client:v3
```

### 🚀 Run with Docker

**Important**: Use `--network host` to allow the container to access network services on the host.

#### 🔗 Basic Docker Usage

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host localhost \
  --port 61613 \
  --topic /topic/test \
  --username admin \
  --password admin
```

#### 🔒 Docker with SSL

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host activemq.example.com \
  --port 61614 \
  --topic /topic/notifications \
  --username myuser \
  --password mypass \
  --ssl
```

#### ⚠️ Docker with Self-Signed Certificate

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host localhost \
  --port 61614 \
  --topic /topic/test \
  --username admin \
  --password admin \
  --ssl \
  --insecure
```

#### 📤 Docker Send Message

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --send "Hello from Docker!"
```

#### 📋 Docker with JSON Message

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --send "service=docker status=running port=8080 timestamp=1640995200" \
  --json
```

This will send:

```json
{"service": "docker", "status": "running", "port": 8080, "timestamp": 1640995200}
```

#### 🐛 Docker with Debug Mode

```bash
docker run --network host fxrobin/wss-stomp-client:v3 \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --debug
```

### 📜 Docker Compose Example

```yaml
version: '3.8'
services:
  stomp-client:
    image: fxrobin/wss-stomp-client:v3
    network_mode: host
    command: >
      --host localhost
      --port 61614
      --topic /topic/monitoring
      --username admin
      --password admin
      --ssl
      --insecure
    restart: unless-stopped
```

## 🔐 Security Considerations

⚠️ **Warning**: The `--insecure` flag disables SSL certificate verification and should only be used:

- In development environments
- With self-signed certificates in controlled environments
- When you understand and accept the security risks

Never use `--insecure` in production with untrusted networks or servers.

## 🔧 Troubleshooting

### 🚨 Common Issues

1. **🚫 Connection Refused**: Check if the STOMP broker is running and accessible
2. **🔒 SSL Certificate Errors**: Use `--insecure` flag for self-signed certificates
3. **❌ Authentication Failed**: Verify username and password
4. **📝 Topic Not Found**: Ensure the topic exists and you have permission to access it

### 🐛 Debug Mode

Enable WebSocket debug traces by using the `--debug` flag:

```bash
python wss-stomp-client.py \
  --host localhost \
  --topic /topic/test \
  --username admin \
  --password admin \
  --debug
```

This will output detailed WebSocket communication logs to help troubleshoot connection issues.

## 📄 License

This project is licensed under the terms specified in the LICENSE file.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
