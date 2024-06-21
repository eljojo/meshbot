import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

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

class NodeStats:
    def __init__(self, db_path):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def data_changed(self, session, node_data):
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

    def insert_node_data(self, session, node_data):
        if self.data_changed(session, node_data):
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

    def snapshot_nodes(self, interface):
        session = self.Session()
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
            self.insert_node_data(session, node_data)
        session.close()
