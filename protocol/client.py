import requests
import os
import sys
from scapy import send, IP, TCP, HTTPRequest
from flask import Flask, render_template

PORT = 1
IP_ADDRESS = 0

RELAY_1 = ["0.0.0.0", 8001]
RELAY_2 = ["0.0.0.0", 8002]

# client Info
class Client:
    def __init__(self,the_host_pi,the_port):
        self.host_ip = the_host_pi
        self.port = the_port

    id_key = ""
    onion_key = ""
    host_ip = ""
    port = -1
    relay_list = [RELAY_1, RELAY_2] 


# Flaks App Info
class FlaskApp:
    app = None
    client = None

    def __init__(self, name, the_client: Client):
        self.app = Flask(name)
        self.client = the_client
        self.app.route("/")(self.index)
        self.app.route("/index")(self.index)

    def run(self):
        self.app.run(host=self.client.host_ip, port=self.client.port)

    def index(self):
        return render_template("clientHome.html", host=self.client.host_ip, port=self.client.port)
    

    # Build connect Cell in a HTTP packet
    # relay_num == starts at 0 
    def get_create_cell(self,relay_num: Int):
        self.client.relay_list[relay_num][IP_ADDRESS]
        self.client.relay_list[relay_num][PORT]
        
        return IP(dst=self.client.relay_list[relay_num][IP_ADDRESS])/TCP(dport=self.client.relay_list[relay_num][PORT])/"GET /index.html HTTP/1.0 \n\n"

    def get_relay_cell(self):
        return




# Pass command line argumets as follows:
# sys.argv[1] = host_ip
# sys.argv[2] = port_number
# sys.argv[3] = port_number
def main():
    client = Client(sys.argv[1], sys.argv[2])
    flaskApp = FlaskApp(__name__, client)
    flaskApp.run()
    print("client STARTING @ PORT: " + client.port)

    # Get info of first relay


    

    return

if __name__ == "__main__":
    main()