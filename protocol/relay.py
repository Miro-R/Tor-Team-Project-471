import requests
import os
import sys
import scapy
import logging
from flask import Flask, render_template, request
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

parameters = dh.generate_parameters(generator=2, key_size=512) # TYPE = DHParameters

# Relay Info
class Relay:
    def __init__(self,the_host_pi,the_port):
        self.host_ip = the_host_pi
        self.port = the_port

    id_key = ""
    onion_key = ""
    host_ip = ""
    port = -1
    dh_private_key = None
    client_shared_key = None
    hkdf = None


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
        self.app.route("/relay-begin")(self.create)

    def run(self):
        self.app.run(host=self.relay.host_ip, port=self.relay.port)

    def index(self):

        return render_template("index.html", host=self.relay.host_ip, port=self.relay.port, is_requested= "depreicated")

    # Expects a dh pubic key ingeger as "dh_public" argument to request

    def get_pub_dh_as_integer(self):
        if(self.relay.dh_private_key == None):
            self.app.logger.info('ASSERT TRIGGERED')
            assert False #issue the key hasnt been generated!


        relay_pub_key = self.relay.dh_private_key.public_key()
        numeric_key = relay_pub_key.public_numbers() # public_numberes returns a DHParameterNumbers object. y is the feild that holds the actual integer

        return numeric_key.y

    def assemble_dh_pub_key(self, int_key):
        # Construct a DHParameterNumbers
        dh_param_numbers = parameters.parameter_numbers() # generates a DHParameterNumbers
        
        shared_dh_numbers = dh.DHPublicNumbers(int_key,dh_param_numbers)

        return shared_dh_numbers.public_key() # takes  (int, DHParameterNumbers) ==> returns DHPublicKey

    def create(self):
        self.relay.dh_private_key = parameters.generate_private_key() # Create new DH private key for this particular connection
        self.app.logger.info('Request data: %s ', (request.data)) 
        self.app.logger.info('Request: %s ', (request))

        # Convert dh integer back into
        client_pub_dh_key = self.assemble_dh_pub_key(int(request.args.get("dh_public")))
        self.relay.client_shared_key = self.relay.dh_private_key.exchange(client_pub_dh_key) # Exchange takes a DHPublicKey
        
        self.app.logger.info('Shared Key Relay: %s ',(self.relay.client_shared_key))

        self.relay.hkdf = (HKDF( # HKDF Docs: https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.hkdf.HKDF
            algorithm=hashes.SHA256(),
            length = 32,
            salt = None,
            info = b'handshake data',
        ).derive(self.relay.client_shared_key))

        self.app.logger.info('Derived key: %s ', self.relay.hkdf)

        return f'{self.get_pub_dh_as_integer()}'

# Pass command line argumets as follows:
# sys.argv[1] = host_ip
# sys.argv[2] = port_number
# sys.argv[3] = port_number
def main():
    relay = Relay(sys.argv[1], sys.argv[2])
    flaskApp = FlaskApp(__name__, relay)
    logging.basicConfig(filename='logs/record.log', level=logging.DEBUG)
    logging.basicConfig(filename='logs/info.log', level=logging.INFO)
    flaskApp.run()
    print("RELAY STARTING @ PORT: " + relay.port)
    


    return

if __name__ == "__main__":
    main()