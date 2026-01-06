import socket
import select
import time
import threading
from mqtt_packet import MqttPacket as mqtt

running = True

class CommunicationController:
    def __init__(self, host: str, port:int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.packet_type = None
        self.connected = False
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

    def connack(self):
        rl_bytes = bytearray()
        while True:
            try:
                b = self.sock.recv(1)
            except BlockingIOError:
                print("CONNACK: Exceptie la citirea remaining length")
                break
            rl_bytes.append(b[0])
            if (b[0] & 0x80) == 0:
                break

        remaining_length, _ = mqtt.decode_varint(bytes(rl_bytes))
        body = bytearray()
        while len(body) < remaining_length:
            try:
                chunk = self.sock.recv(remaining_length - len(body))
            except BlockingIOError:
                print("CONNACK: Exceptie la citirea body")
            body.extend(chunk)

        reason_code = body[1]
        if reason_code == 0x00:
            self.connected = True
        elif reason_code != 0x00:
            raise RuntimeError(f"CONNACK: Eroare, reason={reason_code}")
        print("Packet type:", self.packet_type, "RL:", remaining_length, "Body hex:", body.hex(" "))
        
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
        

    def publish_message(self, topic: str, message: str, qos: int = 0):
        if not self.connected:
            raise RuntimeError("Nu sunt conectat la broker.")
        
        packet = self.pkt.publish_packet(topic, message, qos)
        self.sock.sendall(packet)
        print(f"[COMM] Mesaj publicat pe topicul '{topic}': {message}")