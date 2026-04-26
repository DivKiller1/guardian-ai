import socket
import logging

class HAProxyController:
    def __init__(self, host='haproxy-lb1', port=9999):
        self.host = host
        self.port = port
        self.timeout = 2

    def send_command(self, command):
        """Sends a command to the HAProxy Runtime API via TCP socket."""
        if not command.endswith('\n'):
            command += '\n'
            
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.sendall(command.encode())
                response = b""
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    response += data
                return response.decode()
        except Exception as e:
            logging.error(f"Failed to communicate with HAProxy at {self.host}:{self.port} - {e}")
            return None

    def set_rate_limit(self, ip, limit=100):
        """
        Sets a rate limit for a specific IP in the ddos_protection stick-table.
        Command: set table <table_name> entry <key> data.<field> <value>
        """
        # Note: 'ddos_protection' must be defined in haproxy.cfg
        command = f"set table ddos_protection key {ip} data.conn_rate {limit}"
        return self.send_command(command)

    def clear_table(self):
        """Clears the ddos_protection table."""
        return self.send_command("clear table ddos_protection")

    def get_stats(self):
        """Retrieves table stats."""
        return self.send_command("show table ddos_protection")
