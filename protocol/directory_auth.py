import requests
import os
import sys
from scapy import send, IP, TCP, HTTPRequest
from flask import Flask, render_template
import json

PORT = 1
IP_ADDRESS = 0

RELAY_1 = ["0.0.0.0", 8001]
RELAY_2 = ["0.0.0.0", 8002]

# directory_auth Info
class DirectoryAuth:
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
    directory_auth = None

    def __init__(self, name, the_directory_auth: DirectoryAuth):
        self.app = Flask(name)
        self.directory_auth = the_directory_auth
        self.app.route("/")(self.index)
        self.app.route("/index")(self.index)
        self.app.route("/directories")(self.get_directories)
        self.app.route("/add-relay")(self.add_relay)

    def run(self):
        self.app.run(host=self.directory_a.host_ip, port=self.directory_auth.port)

    def index(self):
        return render_template("directoryAuthHome.html", host=self.directory_auth.host_ip, port=self.directory_auth.port)
    
    def add_relay(self):
        
        # with open('data/directoriesList.json', 'w') as f:
        #     json.dump(data, f)

        return "adding Relay"
    
    def get_directories(self):

        return 



# Pass command line argumets as follows:
# sys.argv[1] = host_ip
# sys.argv[2] = port_number
# sys.argv[3] = port_number
def main():
    directory_auth = directory_auth(sys.argv[1], sys.argv[2])
    flaskApp = FlaskApp(__name__, directory_auth)
    flaskApp.run()
    print("directory_auth STARTING @ PORT: " + directory_auth.port)

    # Get info of first relay


    

    return

if __name__ == "__main__":
    main()