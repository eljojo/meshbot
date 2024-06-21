import logging
import time
import os
from pubsub import pub
import meshtastic
from meshtastic.tcp_interface import TCPInterface
from datetime import datetime

from node_stats import NodeStats
from conversation import ChatBot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MeshBot:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, 'storage.db')
        self.node_stats = NodeStats(self.db_path)
        self.chatbot = None

    def main(self):
        logging.basicConfig(level=logging.INFO)

        # Connect to the Meshtastic device using TCP
        try:
            host = "localhost"
            interface = TCPInterface(host)
        except Exception as ex:
            logger.error(f"Error connecting to {host}: {ex}")
            return

        # Subscribe to the receive message topic
        pub.subscribe(self.onReceive, "meshtastic.receive")

        logger.info("Connected to Meshtastic server")
        self.chatbot = ChatBot(interface, self.node_stats)

        try:
            while True:
                self.node_stats.snapshot_nodes(interface)
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Exiting...")

    def onReceive(self, packet, interface):
        """Callback invoked when a packet arrives"""
        try:
            pfrom = packet["from"]
            pfromId = packet["fromId"]
            pto = packet["to"]
            ptoId = packet["toId"]
            phops = packet.get("hopLimit", "unknown")
            prxTime = packet["rxTime"]
            pid = packet["id"]
            prxSnr = packet.get("rxSnr", "unknown")
            priority = packet.get("priority", "unknown")
            d = packet.get("decoded")
            portnum = d.get("portnum")
            if d is not None:
                if "text" in d:
                    msg = d["text"]
                    sender = packet["from"]
                    destination = packet["to"]
                    is_dm = destination == interface.myInfo.my_node_num

                    logger.info(f"Packet from {pfromId} to {ptoId} hops={phops} id={pid} rxSnr={prxSnr} priority=#{priority} portnum={portnum}")
                    logger.info(f"Received message: {msg} from {sender}")

                    try:
                        response = self.chatbot.generate_response(msg, is_dm)
                    except Exception as ex:
                        response = f"Problem with bot: {ex}"

                    if response:
                        if is_dm:
                            logger.info(f"Sending reply: {response} to {sender}")
                            interface.sendText(response, destinationId=sender, wantAck=True)
                        else:
                            logger.info(f"Sending reply: {response} to the group")
                            interface.sendText(response, wantAck=True)
                    else:
                        logger.info(f"No valid command found in message: {msg}")
                # else:
                    # logger.info(f"Received non-text packet: {d}")
                    # Here you can parse other types of packets, such as telemetry packets
                    # self.parse_non_text_packet(d, packet)
        except Exception as ex:
            logger.error(f"Error processing packet: {ex}")

    def parse_non_text_packet(self, data, packet):
        """Parse non-text packets, such as telemetry packets"""
        try:
            if "position" in data:
                position = data["position"]
                latitude = position.get("latitude")
                longitude = position.get("longitude")
                altitude = position.get("altitude")
                logger.info(f"Telemetry packet - Latitude: {latitude}, Longitude: {longitude}, Altitude: {altitude}")
            else:
                logger.info(f"Unknown non-text packet type: {data}")
        except Exception as ex:
            logger.error(f"Error parsing non-text packet: {ex}")

if __name__ == "__main__":
    bot = MeshBot()
    bot.main()
