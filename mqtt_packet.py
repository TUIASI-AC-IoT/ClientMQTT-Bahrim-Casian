import struct

class MqttPacket:
    def __init__(self, packetType=None, packetFlags=0, remainingLength=0):
        self.packet_type = packetType
        self.flags = packetFlags
        self.remaining_length = remainingLength

    @staticmethod
    def encode_varint(value: int) -> bytes:
        out = bytearray()
        while True:
            byte = value % 128
            value //= 128
            if value > 0:
                byte |= 0x80
            out.append(byte)
            if value == 0:
                break
        return bytes(out)

    @staticmethod
    def decode_varint(buf: bytes, offset: int = 0):
        multiplier = 1
        value = 0
        consumed = 0
        while True:
            byte = buf[offset + consumed]
            consumed += 1
            value += (byte & 0x7F) * multiplier
            if (byte & 0x80) == 0:  
                break
            multiplier *= 128
        return value, consumed

    @staticmethod
    def encode_string(s) -> bytes:
        if isinstance(s, (bytes, bytearray)):
            data = bytes(s)
        else:
            data = str(s).encode("utf-8")
        return struct.pack("!H", len(data)) + data

    def connect_packet(self, client_id: str, keep_alive: int = 60, clean_start: bool = True, 
                       username: str = None, password: str = None, will_topic: str = None, will_message: str = None, will_qos=0) -> bytes:
        
        vh = bytearray()
        vh += self.encode_string("MQTT")   
        vh.append(0x05)                    

        connect_flags = 0
        if clean_start:
            connect_flags |= 0x02          
        if username:
            connect_flags |= 0x80
        if password:
            connect_flags |= 0x40
        if will_message:
            connect_flags |= 0x04
        if will_qos==1:
            connect_flags |= 0x08
        if will_qos==2:
            connect_flags |= 0x10    
        vh.append(connect_flags)

        vh += struct.pack("!H", keep_alive) 

        vh.append(0x00)

        payload = bytearray()
        payload += self.encode_string(client_id)
        if connect_flags & 0x04:  
            payload.append(0x00)
            payload += self.encode_string(will_topic)
            payload += self.encode_string(will_message)
        if username:
            payload += self.encode_string(username)
        if password:
            payload += self.encode_string(password)

        remaining = len(vh) + len(payload)

        fixed = bytearray()
        fixed.append(0x10)                
        fixed += self.encode_varint(remaining)

       
        self.packet_type = 0x01          
        self.flags = 0
        self.remaining_length = remaining

        return bytes(fixed + vh + payload)

    def subscribe_packet(self, packet_id: int, topic: str, qos:int =0) ->bytes:

        vh =bytearray()
        vh+= packet_id.to_bytes(2, "big")

        vh.append(0x00)

        payload = bytearray()

        payload+= self.encode_string(topic)
        payload.append(qos & 0x03)
    
        remaining = len(vh)+len(payload)

        fixed = bytearray()
        fixed.append(0x82)

        fixed +=self.encode_varint(remaining)

        return bytes(fixed + vh + payload)
    
    def publish_packet(self, packet_id: int, topic:str, payload: bytes, qos: int=0) -> bytes:
        vh = bytearray()
        vh += self.encode_string(topic)

        flags = 0x00
        if qos==1:
            flags = 0x02
        elif qos==2:
            flags = 0x04

        if qos > 0:
            vh += packet_id.to_bytes(2, "big")

        vh += self.encode_varint(0)
        
        if isinstance(payload, (bytes, bytearray)):
            payload_bytes = bytes(payload)
        else:
            payload_bytes = str(payload).encode("utf-8")

        remaining = len(vh) + len(payload_bytes)

        fixed = bytearray()
        fixed.append(0x30 | flags)
        fixed += self.encode_varint(remaining)

        return bytes(fixed + vh + payload_bytes)


    def pingreq_packet(self) -> bytes:
        fixed = bytearray()
        fixed.append(0xC0)  
        fixed.append(0x00)  
        return bytes(fixed)
    
    def pubrel_packet(self, packet_id: int) -> bytes:
        vh = bytearray()
        vh += packet_id.to_bytes(2, "big")
        vh.append(0x00)
        
        remaining = len(vh)

        fixed = bytearray()
        fixed.append(0x62)  
        fixed += self.encode_varint(remaining)

        return bytes(fixed + vh)