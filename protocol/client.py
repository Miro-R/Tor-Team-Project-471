import requests
import os
import sys
from flask import Flask, render_template
import logging
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

parameters = dh.generate_parameters(generator=2, key_size=512) # dh key exchange docs: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/dh/

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
    dh_private_keys = []
    dh_shared_keys = []
    hkdf_list = []
    fernets = []

    def generate_dh_private_key(self):
        private_key = parameters.generate_private_key() #  dh key exchange docs: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/dh/
        self.dh_private_keys.append(private_key)
    
        return private_key


# Flaks App Info
class FlaskApp:
    app = None
    client = None

    def __init__(self, name, the_client: Client):
        self.app = Flask(name)
        self.client = the_client
        self.app.route("/")(self.index)
        self.app.route("/index")(self.index)
        #self.app.route("/connect")(self.connection_test)

    def run(self):
        self.connection_test(0) # I dont think this is sending from the correct port/host?? Might be fine if we are running it in a docker container
        self.app.run(host=self.client.host_ip, port=self.client.port)

    def index(self):
        return render_template("clientHome.html", host=self.client.host_ip, port=self.client.port)
    
    # convert DHpublickey to an integer so we can send it in a packet to relay.py
    # Cryptography Docs: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
    def get_pub_dh_as_integer(self, pub_key):
        numeric_key=pub_key.public_numbers() # public_numberes returns a DHParameterNumbers object. y is the feild that holds the actual integer
        return numeric_key.y
    
    def assemble_dh_pub_key(self, int_key, relay_num):
        # Construct a DHParameterNumbers
        dh_param_numbers = parameters.parameter_numbers() # generates a DHParameterNumbers
        
        shared_dh_numbers = dh.DHPublicNumbers(int_key,dh_param_numbers)
        shared_pub_key = shared_dh_numbers.public_key()
        shared_key = self.client.dh_private_keys[relay_num].exchange(shared_pub_key) # Combine public and private key
        self.client.dh_shared_keys.append(shared_key)
        
        return shared_key
    

    # Build connect Cell in a HTTP packet
    # relay_num == starts at 0 
    # Exchange DH keys
    def connection_test(self,relay_num: int):
        dest_ip = self.client.relay_list[relay_num][IP_ADDRESS]
        dest_port = self.client.relay_list[relay_num][PORT]

        dh_private_key=self.client.generate_dh_private_key()
        client_pub_key = dh_private_key.public_key()
        pub_numbers = self.get_pub_dh_as_integer(client_pub_key)

        self.app.logger.info('Client public key: %s ', (str (client_pub_key)))
        self.app.logger.info('Client pub numbers: %d ', ((pub_numbers)))
        
        res = requests.get(f'http://{dest_ip}:{dest_port}/create', params={"dh_public": pub_numbers})

        self.app.logger.info('Response Content: %s ', (res.content))
        self.app.logger.info('Response Int Content: %d ', int(res.content))

        pub_key = self.assemble_dh_pub_key(int(res.content), relay_num)
        self.app.logger.info('Client Shared key: %s ', ((pub_key)))

        # derive HKDF key 
        self.client.hkdf_list.append( HKDF( # HKDF Docs: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.hkdf.HKDF
            algorithm=hashes.SHA256(),
            length = 32,
            salt = None,
            info = b'handshake data',
        ).derive(self.client.dh_shared_keys[relay_num]))

        self.app.logger.info('Derived key: %s ', self.client.hkdf_list[relay_num])

        #self.client.fernets.append( Fernet(self.client.hkdf_list[relay_num]))

        return
    
    # relay_dest_num == the relay_num this message is intended for
    def encrypt_msg(self, msg, relay_dest_num):
        


        return

    # Sends the multi-layer 
    def send_onion(self, message, relay_num):


        return
        



    def get_relay_cell(self):
        return




# Pass command line argumets as follows:
# sys.argv[1] = host_ip
# sys.argv[2] = port_number
# sys.argv[3] = port_number
def main():
    logging.basicConfig(filename='logs/record.log', level=logging.DEBUG)
    logging.basicConfig(filename='logs/info.log', level=logging.INFO)
    client = Client(sys.argv[1], sys.argv[2])
    flaskApp = FlaskApp(__name__, client)
    flaskApp.run()
    print("client STARTING @ PORT: " + client.port)

    

    return

if __name__ == "__main__":
    main()