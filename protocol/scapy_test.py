
from scapy.all import send, IP, TCP

IP_DEST = "0.0.0.0"
PORT = 8001

pkt = IP(dst=IP_DEST)/TCP(dport=PORT)/"GET /create.html HTTP/1.0 \n\n"
res = send(pkt, return_packets=True)
res.show()