import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload

Base = declarative_base()

class NodeInfo(Base):
    __tablename__ = 'node_info'
    node_id = Column(Integer, primary_key=True)
    user = Column(String)
    aka = Column(String)
    last_heard = Column(DateTime)
    hw_model = Column(String)

    snapshots = relationship("NodeSnapshot", back_populates="node_info")

    __table_args__ = (
        Index('idx_last_heard', 'last_heard'),
    )

class NodeSnapshot(Base):
    __tablename__ = 'node_snapshots'
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey('node_info.node_id'), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    battery = Column(Float)
    voltage = Column(Float)
    channel_util = Column(Float)
    tx_air_util = Column(Float)
    snr = Column(Float)
    timestamp = Column(DateTime, default=func.now())

    node_info = relationship("NodeInfo", back_populates="snapshots")

    __table_args__ = (
        Index('idx_node_id', 'node_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )

class NodeStats:
    def __init__(self, db_path):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def data_changed(self, session, node_data):
        latest_snapshot = session.query(NodeSnapshot).filter_by(node_id=node_data['node_id']).order_by(NodeSnapshot.timestamp.desc()).first()
        if latest_snapshot:
            return (latest_snapshot.latitude != node_data['latitude'] or
                    latest_snapshot.longitude != node_data['longitude'] or
                    latest_snapshot.altitude != node_data['altitude'] or
                    latest_snapshot.battery != node_data['battery'] or
                    latest_snapshot.voltage != node_data['voltage'] or
                    latest_snapshot.channel_util != node_data['channel_util'] or
                    latest_snapshot.tx_air_util != node_data['tx_air_util'] or
                    latest_snapshot.snr != node_data['snr'])
        return True

    def update_node_info(self, session, node_data):
        node_info = session.query(NodeInfo).filter_by(node_id=node_data['node_id']).first()
        if not node_info:
            node_info = NodeInfo(
                node_id=node_data['node_id'],
                user=node_data['user'],
                aka=node_data['aka'],
                last_heard=node_data['last_heard'],
                hw_model=node_data.get('hw_model', 'Unknown')
            )
            session.add(node_info)
        else:
            node_info.user = node_data['user']
            node_info.aka = node_data['aka']
            node_info.last_heard = node_data['last_heard']
            node_info.hw_model = node_data.get('hw_model', 'Unknown')
            session.commit()

    def insert_node_data(self, session, node_data):
        self.update_node_info(session, node_data)
        if self.data_changed(session, node_data):
            new_snapshot = NodeSnapshot(
                node_id=node_data['node_id'],
                latitude=node_data['latitude'],
                longitude=node_data['longitude'],
                altitude=node_data['altitude'],
                battery=node_data['battery'],
                voltage=node_data['voltage'],
                channel_util=node_data['channel_util'],
                tx_air_util=node_data['tx_air_util'],
                snr=node_data['snr']
            )
            session.add(new_snapshot)
            session.commit()

    def snapshot_nodes(self, interface):
        session = self.Session()
        for node in interface.nodes.values():
            device_metrics = node.get('deviceMetrics', {})
            node_data = {
                'node_id': node['num'],
                'user': node['user'].get('longName', 'Unknown'),
                'aka': node['user'].get('shortName', 'Unknown'),
                'latitude': node.get('position', {}).get('latitude', None),
                'longitude': node.get('position', {}).get('longitude', None),
                'altitude': node.get('position', {}).get('altitude', None),
                'battery': device_metrics.get('batteryLevel', node.get('batteryLevel', None)),
                'voltage': device_metrics.get('voltage', None),
                'channel_util': device_metrics.get('channelUtilization', node.get('channelUtilization', None)),
                'tx_air_util': device_metrics.get('airUtilTx', node.get('txAirUtilization', None)),
                'snr': node.get('snr', None),
                'last_heard': datetime.utcfromtimestamp(int(node.get("lastHeard", 0))),
                'hw_model': node.get('hwModel', 'Unknown')
            }
            self.insert_node_data(session, node_data)
        session.close()

    def get_node_count(self):
        session = self.Session()
        count = session.query(func.count(func.distinct(NodeInfo.node_id))).scalar()
        session.close()
        return count

    def get_recent_nodes(self, time_delta):
        session = self.Session()
        recent_time = datetime.utcnow() - time_delta

        recent_nodes = (
            session.query(NodeInfo)
            .filter(NodeInfo.last_heard >= recent_time)
            .all()
        )

        session.close()
        return recent_nodes

    def get_top_nodes_by_metric(self, metric, limit, time_filter):
        session = self.Session()
        recent_time = datetime.utcnow() - time_filter
        top_nodes = (
            session.query(NodeSnapshot)
            .filter(NodeSnapshot.timestamp >= recent_time)
            .options(joinedload(NodeSnapshot.node_info))
            .order_by(getattr(NodeSnapshot, metric).desc())
            .limit(limit)
            .all()
        )
        session.close()
        return top_nodes
