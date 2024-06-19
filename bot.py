import logging
import time
from pubsub import pub
import meshtastic
from meshtastic.tcp_interface import TCPInterface
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(self, interface):
        self.interface = interface

    def generate_response(self, message, is_dm):
        command_prefix = "@nara"
        if is_dm or message.startswith(command_prefix):
            if not is_dm:
                message = message[len(command_prefix):].strip()
            if message.lower().strip() == "summary":
                return self.summary()
            elif message.lower().strip() == "nodes":
                return self.nodes()
            else:
                # If it's a DM, just reverse the message
                return message[::-1]
        return None

    def summary(self):
        node_count = len(self.interface.nodes.values())
        return f"There are currently {node_count} nodes known by the bot in the mesh."

    def nodes(self):
        recent_nodes = []
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        for node in self.interface.nodes.values():
            last_heard = int(node.get("lastHeard", 0))
            last_heard_time = datetime.utcfromtimestamp(last_heard)
            if last_heard_time >= one_hour_ago:
                # recent_nodes.append(f"Node ID: {node['num']}, User: {node['user'].get('longName', 'Unknown')}")
                recent_nodes.append(node['user'].get('longName', 'Unknown'))
        if recent_nodes:
            return f"{len(recent_nodes)} nodes have been seen in the last hour."
        else:
            return "No nodes have been active in the last hour."

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

            try:
              response = chatbot.generate_response(msg, is_dm)
            except Exception as ex:
              response = f"Problem with bot: {ex}"

            if response:
                if is_dm:
                    # Send reply directly to the sender
                    logger.info(f"Sending reply: {response} to {sender}")
                    interface.sendText(response, destinationId=sender, wantAck=True)
                else:
                    # Send reply to the group channel
                    logger.info(f"Sending reply: {response} to the group")
                    interface.sendText(response, wantAck=True)
            else:
                logger.info(f"No valid command found in message: {msg}")
    except Exception as ex:
        logger.error(f"Error processing packet: {ex}")

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Connect to the Meshtastic device using TCP
    try:
        host = "localhost"  # TODO: make customizable
        interface = TCPInterface(host)
    except Exception as ex:
        logger.error(f"Error connecting to {host}: {ex}")
        return

    # Subscribe to the receive message topic
    pub.subscribe(onReceive, "meshtastic.receive")

    logger.info("Connected to Meshtastic server")
    global chatbot
    chatbot = ChatBot(interface)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")

if __name__ == "__main__":
    main()
