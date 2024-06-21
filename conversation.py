from datetime import datetime, timedelta
import re

class ChatBot:
    def __init__(self, interface, node_stats):
        self.interface = interface
        self.node_stats = node_stats

    def generate_response(self, message, is_dm):
        command_prefix = "@nara"
        responses = []
        if is_dm or message.startswith(command_prefix):
            if not is_dm:
                message = message[len(command_prefix):].strip()
            if message.lower().strip() == "summary":
                responses.append(self.summary())
            elif message.lower().strip() == "nodes":
                responses.append(self.nodes())
            elif message.lower().startswith("stats"):
                time_filter = self.parse_time_filter(message)
                responses.extend(self.stats(time_filter))
            else:
                responses.append(message[::-1])
        return responses

    def parse_time_filter(self, message):
        match = re.search(r'stats (\d+)([hm])', message.lower())
        if match:
            value, unit = match.groups()
            if unit == 'h':
                return timedelta(hours=int(value))
            elif unit == 'm':
                return timedelta(minutes=int(value))
        return timedelta(hours=6)

    def summary(self):
        node_count = self.node_stats.get_node_count()
        return f"There are currently {node_count} nodes known by the bot in the mesh."

    def nodes(self):
        one_hour_ago = timedelta(hours=1)
        recent_nodes = self.node_stats.get_recent_nodes(one_hour_ago)
        if recent_nodes:
            return f"{len(recent_nodes)} nodes have been seen in the last hour."
        else:
            return "No nodes have been active in the last hour."

    def stats(self, time_filter):
        stats_responses = []
        unique_nodes = {}

        highest_snr_nodes = self.node_stats.get_top_nodes_by_metric('snr', 1, time_filter)
        highest_channel_util_nodes = self.node_stats.get_top_nodes_by_metric('channel_util', 1, time_filter)
        highest_tx_air_util_nodes = self.node_stats.get_top_nodes_by_metric('tx_air_util', 1, time_filter)

        for node in highest_snr_nodes + highest_channel_util_nodes + highest_tx_air_util_nodes:
            unique_nodes[node.node_id] = node

        for node_id, node in unique_nodes.values():
            stats_responses.append(f"Node {node.node_id}: SNR={node.snr}, Channel Util={node.channel_util}, TX Air Util={node.tx_air_util}")

        return stats_responses
