import socket

from http_parser import HttpParser


class Listener:
    def __init__(self):
        self.server = None
        self.http_parser = HttpParser()

    def listen(self, address, port, connections=1):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((address, port))
        server.listen(connections)
        self.server = server
        return server

    def accept_connection(self):
        client, addr = self.server.accept()

        data_encoded = client.recv(65536)
        request = self.http_parser.parse_http_request(data_encoded)

        print(request.headers['Host'])
        addr, port = request.headers['Host'].split(':')

        dest_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest_socket.connect((addr, int(port)))
        dest_socket.sendall()

        client.shutdown(1)
        client.close()
