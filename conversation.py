from datetime import datetime, timedelta

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
                recent_nodes.append(node['user'].get('longName', 'Unknown'))
        if recent_nodes:
            return f"{len(recent_nodes)} nodes have been seen in the last hour."
        else:
            return "No nodes have been active in the last hour."
