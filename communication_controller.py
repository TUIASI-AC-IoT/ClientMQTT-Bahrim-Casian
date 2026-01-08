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
        self.first_byte = None
        self.connected = False
        self.packet_id=0
        self.pkt = mqtt()
        self.stop_event = threading.Event()
        self.rx_thread = None
        self.received_message = None
        self.received_topic = None

    def receive_function(self):
        global running
        while running:
            try:
                r, _, _ = select.select([self.sock], [], [], 1)
            except (OSError, ValueError):
                break

            if not r:
                continue
            
            try:
                self.first_byte = self.sock.recv(1)
            except BlockingIOError:
                print("RECEIVE FUNCTION: Exceptie la citirea packet type")
                break
            
            self.packet_type = self.first_byte[0] >> 4 

            if self.packet_type == 0x02:
                self.connack()
            if self.packet_type == 0x0D:
                self.pingresp()
            if self.packet_type == 0x04:
                self.puback()
            if self.packet_type == 0x05:
                self.pubrec()
            if self.packet_type == 0x07:
                self.pubcomp()
            if self.packet_type == 0x09:
                self.suback()
            if self.packet_type == 0x03:
                self.receive_publish()
            if self.packet_type == 0x06:
                self.pubrel()
            if self.packet_type == 0x0B:
                self.unsuback()

        self.connected = False


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

        self.disconnect()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.sendall(self.pkt.connect_packet(client_id, keep_alive=15, clean_start=True, username=username,
                                                   password=password, will_topic=will_topic, will_message=will_message, will_qos=will_qos))
        
        self.rx_thread = threading.Thread(target=self.receive_function, daemon=True)
        self.rx_thread.start()

        time.sleep(0.5)
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
        if qos>=1:
            print(f"[COMM] Mesaj cu id-ul {self.packet_id} publicat pe topicul '{topic}': {message}")
        else:
            print(f"[COMM] Mesaj publicat pe topicul '{topic}': {message}")

    def puback(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[0].to_bytes(1, byteorder="big")
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

    def subscribe_topic(self, topic: str, qos: int = 0):
        if not self.connected:
            raise RuntimeError("Nu sunt conectat la broker.")

        self.packet_id += 1
        packet = self.pkt.subscribe_packet(self.packet_id, topic, qos)
        self.sock.sendall(packet)
        print(f"[COMM] Cerere de subscribe cu id-ul {self.packet_id} trimisa pentru topicul '{topic}' cu QoS-ul maxim {qos}.")

    def suback(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[2].to_bytes(1, byteorder="big")
        print(f"SUBACK cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")

    def disconnect(self):
        self.stop_event.set()

        if self.sock:
            try:
                if self.connected:
                    try:
                        self.sock.sendall(self.pkt.disconnect_packet())
                    except OSError:
                        pass

                self.connected = False

                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

                self.sock.close()
            finally:
                self.sock = None

        print("[COMM] Deconectat de la broker.")

    def receive_publish(self):
        first_byte = self.first_byte[0]
        publish_qos = (first_byte & 0x06) >> 1
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        topic_length = int.from_bytes(packet[0:2], "big")
        self.received_topic = packet[2:topic_length+2].decode('utf-8')
        if publish_qos > 0:
            packet_id = packet[topic_length+2:topic_length+4]
            
            self.received_message = packet[5+topic_length:rl+1].decode('utf-8')
            print(f"[COMM] Mesaj cu id-ul {packet_id}, qos {publish_qos} publicat primit pe topicul '{self.received_topic}': {self.received_message}")

            if publish_qos==1:
                self.sock.sendall(self.pkt.puback_packet(int.from_bytes(packet_id, "big")))
                print(f"Trimis PUBACK pentru mesajul {self.received_message} cu id-ul {packet_id}")

            elif publish_qos==2:
                self.sock.sendall(self.pkt.pubrec_packet(int.from_bytes(packet_id, "big")))
                print(f"Trimis PUBREC pentru mesajul {self.received_message} cu id-ul {packet_id}")
            
        if publish_qos==0:
            self.received_message = packet[3+topic_length:rl].decode('utf-8')
            print(f"[COMM] Mesaj publicat cu qos {publish_qos} primit pe topicul '{self.received_topic}': {self.received_message}")
    
    def pubrel(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[0].to_bytes(1, byteorder="big")
        if reason_code == b'\x00':
            self.sock.sendall(self.pkt.pubcomp_packet(packet_id))
            print(f"Trimis PUBCOMP pentru mesajul {self.received_message} cu id-ul {packet_id}")
        print(f"PUBREL cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")

    def unsubscribe_topic(self, topic: str):
        if not self.connected:
            raise RuntimeError("Nu sunt conectat la broker.")

        self.packet_id += 1
        packet = self.pkt.unsubscribe_packet(self.packet_id, topic)
        self.sock.sendall(packet)
        print(f"[COMM] Cerere de unsubscribe cu id-ul {self.packet_id} trimisa pentru topicul '{topic}'.")


    def unsuback(self):
        remaining_length = self.sock.recv(1)
        rl = int.from_bytes(remaining_length, byteorder="big")
        packet = self.sock.recv(rl)
        packet_id = packet[1]
        reason_code = packet[2].to_bytes(1, byteorder="big")
        print(f"UNSUBACK cu id-ul {packet_id}, reason code {reason_code} primit de la broker.")