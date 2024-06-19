import logging
import time
from pubsub import pub
import meshtastic
from meshtastic.tcp_interface import TCPInterface

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# The chatbot logic
class ChatBot:
    def __init__(self, interface):
        self.interface = interface

    def generate_response(self, message, is_dm):
        if is_dm:
            # If it's a DM, just reverse the message
            return message[::-1]
        else:
            # If it's a channel message, reverse the message without the "@nara" part
            command_prefix = "@nara"
            if message.startswith(command_prefix):
                return message[len(command_prefix):].strip()[::-1]
            return None

def onReceive(packet, interface):
    """Callback invoked when a packet arrives"""
    try:
        d = packet.get("decoded")
        if d is not None and "text" in d:
            msg = d["text"]
            sender = packet["from"]
            destination = packet["to"]

            is_dm = destination == interface.myInfo.my_node_num

            logger.info(f"Received message: {msg} from {sender}")

            response = chatbot.generate_response(msg, is_dm)
            if response:
                if is_dm:
                    # Send reply directly to the sender
                    logger.info(f"Sending reply: {response} to {sender}")
                    interface.sendText(response, destinationId=sender)
                else:
                    # Send reply to the group channel
                    logger.info(f"Sending reply: {response} to the group")
                    interface.sendText(response)
            else:
                logger.info(f"No valid command found in message: {msg}")
    except Exception as ex:
        logger.error(f"Error processing packet: {ex}")

def onConnected(interface):
    """Callback invoked when we connect to a radio"""
    logger.info("Connected to Meshtastic server")
    global chatbot
    chatbot = ChatBot(interface)  # Initialize the chatbot

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Connect to the Meshtastic device using TCP
    try:
        host = "localhost"  # Change this to your Meshtastic server's IP or hostname
        client = TCPInterface(host)
    except Exception as ex:
        logger.error(f"Error connecting to {host}: {ex}")
        return

    # Subscribe to the receive message topic
    pub.subscribe(onReceive, "meshtastic.receive")

    # Call onConnected to initialize the chatbot
    onConnected(client)

    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")

if __name__ == "__main__":
    main()
