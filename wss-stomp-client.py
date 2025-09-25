#!/usr/bin/env python3
"""
ActiveMQ WebSocket STOMP Consumer
Connects to ActiveMQ topic using WSS protocol and displays received messages in the console.
Uses the custom stomp_ws module for STOMP over WebSockets.
"""

import logging
import time
import json
from datetime import datetime
import argparse
import sys
import os
import threading

# Add the project root directory to the Python path to find stomp_ws module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stomp_ws.stomp import Stomp

# Configure logging (console only, no file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def message_handler(message):
    """
    Handler for incoming STOMP messages
    """
    if isinstance(message, bytes):
        message = message.decode('utf-8')
    
    timestamp = datetime.now().isoformat()
    try:
        # Try to parse as JSON
        payload = json.loads(message)
        formatted_payload = json.dumps(payload, indent=2)
    except json.JSONDecodeError:
        # If not JSON, use raw message
        formatted_payload = message
        
    logger.info(f"Message received at {timestamp}")
    logger.info(f"Payload: {formatted_payload}")
    logger.info("-" * 80)

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='ActiveMQ WebSocket STOMP Consumer')
    parser.add_argument('--host', required=True, help='ActiveMQ host (e.g., activemq.example.com)')
    parser.add_argument('--port', type=int, default=61614, help='ActiveMQ WSS port (default: 61614)')
    parser.add_argument('--topic', required=True, help='STOMP topic name (e.g., /topic/your.topic.name)')
    parser.add_argument('--username', required=True, help='ActiveMQ username')
    parser.add_argument('--password', required=True, help='ActiveMQ password')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL (WSS). If not set, use plain TCP (WS)')
    parser.add_argument('--sockjs', action='store_true', help='Use SockJS protocol')
    parser.add_argument('--send', help='Send a message to the topic and exit (optional)')
    parser.add_argument('--json', action='store_true', help='Format --send payload as JSON (key1=value1 key2=value2)')
    parser.add_argument('--heartbeat', type=int, default=10, help='Heartbeat interval in seconds (default: 10)')
    parser.add_argument('--insecure', action='store_true', help='Accept self-signed certificates (disable SSL verification)')
    parser.add_argument('--debug', action='store_true', help='Enable WebSocket debug traces')
    return parser.parse_args()


def format_json_payload(payload):
    """Format a space-separated key=value string into JSON"""
    try:
        # Parse key=value pairs into a dictionary
        pairs = [pair.strip() for pair in payload.split()]
        json_dict = {}
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                # Try to convert to numbers if applicable
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass
                json_dict[key] = value
        
        return json.dumps(json_dict)
    except Exception as e:
        logger.error(f"Failed to format as JSON: {str(e)}")
        return payload


def send_message(client, topic, payload, format_as_json=False):
    """Send a message and exit"""
    if format_as_json:
        payload = format_json_payload(payload)
        logger.info("Converted input to JSON format")
    
    client.send(topic, payload)
    logger.info(f"Message sent to topic: {topic}")
    logger.info(f"Payload: {payload}")
    time.sleep(1)  # Give some time for the message to be delivered


def listen_for_messages(client, topic):
    """Subscribe and listen for messages"""
    client.subscribe(topic, message_handler)
    logger.info(f"Subscribed to topic: {topic}")
    logger.info("Consumer started. Waiting for messages... (Press Ctrl+C to stop)")
    
    # Keep the main thread alive
    while True:
        time.sleep(1)


def send_heartbeat(client):
    """
    Send a single heartbeat
    
    Args:
        client: The STOMP client instance
    """
    if not (hasattr(client, 'connected') and client.connected):
        return

    logger.debug("Sending heartbeat...")
    
    # Send STOMP heartbeat
    if hasattr(client, 'dispatcher'):
        client.dispatcher.heartbeat()

def send_heartbeats(client, interval=10):
    """
    Start a thread that sends heartbeats periodically
    
    Args:
        client: The STOMP client instance
        interval: Seconds between heartbeats (default: 10)
    """
    logger.info(f"Starting heartbeat thread (interval: {interval}s)")
    
    def heartbeat_loop():
        while True:
            try:
                send_heartbeat(client)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in heartbeat thread: {str(e)}")
                time.sleep(interval)
    
    # Start heartbeat thread
    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()
    return thread


def main():
    """Main entry point of the program"""
    args = parse_args()

    # Format host with port
    host_with_port = f"{args.host}:{args.port}"

    # Log where we're going to connect to (protocol, host:port and sockjs usage)
    proto = 'wss' if args.ssl else 'ws'
    insecure_msg = " (accepting self-signed certificates)" if args.insecure and args.ssl else ""
    logger.info(f"Will connect using protocol={proto}, endpoint={host_with_port}, sockjs={args.sockjs}{insecure_msg}")

    # Warning for insecure mode
    if args.insecure and args.ssl:
        logger.warning("⚠️  SSL certificate verification is disabled. This is insecure and should only be used for testing!")
    
    # Initialize STOMP client
    client = Stomp(
        host=host_with_port, 
        sockjs=args.sockjs,
        wss=args.ssl,
        username=args.username, 
        password=args.password,
        insecure=args.insecure,
        debug=args.debug
    )

    # Start the heartbeat thread
    send_heartbeats(client, interval=10)

    try:
        # Connect to the STOMP server
        logger.info(f"Connecting to STOMP server at {'wss' if args.ssl else 'ws'}://{host_with_port}")
        connected = client.connect()
        
        if connected:
            logger.info("Successfully connected to STOMP server")
            
            # Start the heartbeat thread with the specified interval
            send_heartbeats(client, interval=args.heartbeat)
            
            # If we're just sending a message
            if args.send:
                send_message(client, args.topic, args.send, args.json)
                return
            
            # Otherwise, subscribe and listen
            listen_for_messages(client, args.topic)
        else:
            logger.error("Failed to connect to STOMP server")
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
    finally:
        try:
            client.disconnect()
            logger.info("Disconnected from STOMP server")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
        logger.info("STOMP client shutdown complete")

if __name__ == "__main__":
    main()
