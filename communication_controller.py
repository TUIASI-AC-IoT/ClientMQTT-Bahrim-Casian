import socket
import select
import time
import threading
from mqtt_packet import MqttPacket as mqtt
import psutil

running = True

class CommunicationController:
    def __init__(self, host: str, port:int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.packet_type = None
        self.connected = False
        self.packet_id=0
        self.pkt = mqtt()

    def receive_function(self):
        global running
        while running:
            r, _, _ = select.select([self.sock], [], [], 1)
            if not r:
                continue
            
            try:
                self.packet_type = self.sock.recv(1)
            except BlockingIOError:
                print("RECEIVE FUNCTION: Exceptie la citirea packet type")
                break
            
            if self.packet_type == b'\x20':
                self.connack()
            if self.packet_type == b'\xd0':
                self.pingresp()
            if self.packet_type == b'\x40':
                self.puback()
            if self.packet_type == b'\x50':
                self.pubrec()
            if self.packet_type == b'\x70':
                self.pubcomp()
            
    def connack(self):
    
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)

        reason_code = packet[1]
        if reason_code == 0x00:
            self.connected = True
        elif reason_code != 0x00:
            raise RuntimeError(f"CONNACK: Eroare, reason={reason_code}")
        print("Packet type:", self.packet_type, "RL:", rl, "Body hex:", packet.hex())
        
    def connect_to_server(self, client_id: str, username: str, password: str, will_topic: str, will_message: str = None, will_qos: int = 0):
        self.sock.connect((self.host, self.port))
        self.sock.sendall(self.pkt.connect_packet(client_id, keep_alive=60, clean_start=True, username=username,
                                                   password=password, will_topic=will_topic, will_message=will_message, will_qos=will_qos))
        
        threading.Thread(target=self.receive_function, daemon=True).start()

        time.sleep(1)
        if self.connected == True:
            print("[COMM] Conectat cu succes la broker.")
            threading.Thread(target=self.pingreq, daemon=True).start()
        

    def pingreq(self):
        while self.connected:
            print("PINGREQ trimis catre broker.")
            self.sock.sendall(self.pkt.pingreq_packet())
            time.sleep(10)

    def pingresp(self):
        print("PINGRESP primit de la broker.")
        

    def publish_message(self, topic: str, qos: int = 0):
        if not self.connected:
            raise RuntimeError("Nu sunt conectat la broker.")

        if qos>=1:
            self.packet_id += 1
        if topic == "CPU Frequency":
            message = "CPU Frequency: " + str(psutil.cpu_freq().current)+ " MHz"
        if topic == "CPU Usage":
            message = "CPU Usage: " + str(psutil.cpu_percent())+ " %"
        if topic == "Memory Usage":
            message = "Memory Usage: " + str(psutil.virtual_memory().percent)+ " %"
        packet = self.pkt.publish_packet(self.packet_id, topic, message, qos)
        self.sock.sendall(packet)
        print(f"[COMM] Mesaj cu id-ul {self.packet_id} publicat pe topicul '{topic}': {message}")

    def puback(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[2].to_bytes(1, byteorder="big")
        print(f"PUBACK cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")

    def pubrec(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[0].to_bytes(1, byteorder="big")
        print(f"PUBREC cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")
        if reason_code == b'\x00':
            self.sock.sendall(self.pkt.pubrel_packet(packet_id))
            print(f"PUBREL cu id-ul {packet_id} trimis catre broker.")
    
    def pubcomp(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[0].to_bytes(1, byteorder="big")
        print(f"PUBCOMP cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")
