import logging
import time
import os
from pubsub import pub
import meshtastic
from meshtastic.tcp_interface import TCPInterface
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
Base = declarative_base()

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'storage.db')

engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)
session = Session()

class NodeSnapshot(Base):
    __tablename__ = 'node_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String)
    user = Column(String)
    aka = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    battery = Column(Float)
    channel_util = Column(Float)
    tx_air_util = Column(Float)
    snr = Column(Float)
    channel = Column(String)
    lastheard = Column(DateTime)
    timestamp = Column(DateTime, default=func.now())

# Create the table
Base.metadata.create_all(engine)

def data_changed(session, node_data):
    latest_snapshot = session.query(NodeSnapshot).filter_by(node_id=node_data['node_id']).order_by(NodeSnapshot.timestamp.desc()).first()
    if latest_snapshot:
        return (latest_snapshot.user != node_data['user'] or
                latest_snapshot.aka != node_data['aka'] or
                latest_snapshot.latitude != node_data['latitude'] or
                latest_snapshot.longitude != node_data['longitude'] or
                latest_snapshot.altitude != node_data['altitude'] or
                latest_snapshot.battery != node_data['battery'] or
                latest_snapshot.channel_util != node_data['channel_util'] or
                latest_snapshot.tx_air_util != node_data['tx_air_util'] or
                latest_snapshot.snr != node_data['snr'] or
                latest_snapshot.channel != node_data['channel'] or
                latest_snapshot.lastheard != node_data['lastheard'])
    return True

def insert_node_data(session, node_data):
    if data_changed(session, node_data):
        new_snapshot = NodeSnapshot(
            node_id=node_data['node_id'],
            user=node_data['user'],
            aka=node_data['aka'],
            latitude=node_data['latitude'],
            longitude=node_data['longitude'],
            altitude=node_data['altitude'],
            battery=node_data['battery'],
            channel_util=node_data['channel_util'],
            tx_air_util=node_data['tx_air_util'],
            snr=node_data['snr'],
            channel=node_data['channel'],
            lastheard=node_data['lastheard']
        )
        session.add(new_snapshot)
        session.commit()

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

def snapshot_nodes(interface, session):
    for node in interface.nodes.values():
        node_data = {
            'node_id': node['num'],
            'user': node['user'].get('longName', 'Unknown'),
            'aka': node['user'].get('shortName', 'Unknown'),
            'latitude': node.get('position', {}).get('latitude', None),
            'longitude': node.get('position', {}).get('longitude', None),
            'altitude': node.get('position', {}).get('altitude', None),
            'battery': node.get('batteryLevel', None),
            'channel_util': node.get('channelUtilization', None),
            'tx_air_util': node.get('txAirUtilization', None),
            'snr': node.get('snr', None),
            'channel': node.get('channel', None),
            'lastheard': datetime.utcfromtimestamp(int(node.get("lastHeard", 0)))
        }
        insert_node_data(session, node_data)

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
            snapshot_nodes(interface, session)
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Exiting...")

if __name__ == "__main__":
    main()
