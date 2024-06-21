from datetime import datetime, timedelta

class ChatBot:
    def __init__(self, interface, node_stats):
        self.interface = interface
        self.node_stats = node_stats

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
                return message[::-1]
        return None

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
