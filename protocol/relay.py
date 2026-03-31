import requests
import os
import sys
import scapy
from flask import Flask, render_template, request



# Relay Info
class Relay:
    def __init__(self,the_host_pi,the_port):
        self.host_ip = the_host_pi
        self.port = the_port

    id_key = ""
    onion_key = ""
    host_ip = ""
    port = -1


# Flaks App Info
class FlaskApp:
    app = None
    relay = None

    def __init__(self, name, the_relay: Relay):
        self.app = Flask(name)
        self.relay = the_relay
        self.app.route("/")(self.index)
        self.app.route("/index", methods=['GET', 'POST'] )(self.index)
        self.app.route("/create")(self.create)

    def run(self):
        self.app.run(host=self.relay.host_ip, port=self.relay.port)

    def index(self):

        return render_template("index.html", host=self.relay.host_ip, port=self.relay.port, is_requested= "depreicated" )

    def create(self):

        return "creating"

# Pass command line argumets as follows:
# sys.argv[1] = host_ip
# sys.argv[2] = port_number
# sys.argv[3] = port_number
def main():
    relay = Relay(sys.argv[1], sys.argv[2])
    flaskApp = FlaskApp(__name__, relay)
    flaskApp.run()
    print("RELAY STARTING @ PORT: " + relay.port)
    


    return

if __name__ == "__main__":
    main()