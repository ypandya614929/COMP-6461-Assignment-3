#!/usr/bin/python
# -*- coding: utf-8 -*-

# ./routers/macos/router --port=3000 --drop-rate=0.2 --seed 2387230234324
# ./routers/macos/router --port=3000 --max-delay=100ms --seed 2387230234324
# ./routers/macos/router --port=3000 --drop-rate=0.2 --max-delay=100ms --seed 2387230234324

# python3 httpfs.py -arq -v -p 8080 -d .

# python3 httpc.py get -arq -v -p 8080 "http://localhost/"
# python3 httpc.py get -arq -v -p 8080 "http://localhost/random.json"
# python3 httpc.py get -arq -p 8080 -o "output.json" "http://localhost/random.json"
# python3 httpc.py post -arq -v -p 8080 --h Content-Type:application/json -d "some text here" "http://localhost/demo.txt"
# python3 httpc.py post -arq -v -p 8080 -o "output.json" --h Content-Type:application/json -d "some text here" "http://localhost/demo.txt"
# python3 httpc.py get -arq -v -p 8080 --h Content-Disposition:inline "http://localhost/random.json"
# python3 httpc.py get -arq -v -p 8080 --h Content-Disposition:attachment "http://localhost/demo.txt"

import socket
import time
import ipaddress
from numpy import uint32 as uint
from threading import Timer
from constants import *


class UDPPacket:

    def __init__(self, packet_type, sequence, ip, port, payload):
        self.packet_type = int(packet_type)
        self.ip = ip
        self.port = int(port)
        self.sequence = int(sequence)
        self.payload = payload
        self.is_send = False

    def __str__(self):
        return "sequence : {} | ip : {} | port : {} | size : {}".format(self.sequence, self.ip, self.port, len(self.payload))

    @staticmethod
    def create_packet(ip, port, sequence=0, type=DATA_BIT_VAL, payload=""):
        if not payload:
            payload = "".encode("utf-8")
        return UDPPacket(
            packet_type=type, sequence=sequence, ip=ip,
            port=port, payload=payload
        )

    @staticmethod
    def data_package(ip, port, content, stop, sequence=0):
        res_dict = {}
        package = []
        chunk_data_list = [
            content[i:i + MINIMUM_LEN] for i in range(
                0, len(content), MINIMUM_LEN
            )
        ]
        for chunk_data in chunk_data_list:
            package.append(UDPPacket.create_packet(
                ip, port, sequence, payload=chunk_data))
            sequence = UDPPacket.generate_sequence(sequence, 1)
        if stop:
            package.append(UDPPacket.create_packet(ip, port, sequence))
            sequence = UDPPacket.generate_sequence(sequence, 1)
        res_dict.update({'package': package})
        res_dict.update({'sequence': sequence})
        return res_dict

    @staticmethod
    def generate_sequence(curr_sequence, next_seq=None):
        if ((next_seq == 0) or (next_seq != None)):
            new_sequence = uint(curr_sequence) + uint(next_seq)
            if new_sequence < curr_sequence:
                new_sequence = new_sequence + uint(1)
        else:
            new_sequence = uint(curr_sequence) - uint(1)
            if new_sequence == 0:
                new_sequence = new_sequence - uint(1)
        return new_sequence

    def convert_data_into_bytes(self):
        byte_list = bytearray()
        byte_list.extend(self.packet_type.to_bytes(1, byteorder='big'))
        byte_list.extend(self.sequence.to_bytes(4, byteorder='big'))
        byte_list.extend(self.ip.packed)
        byte_list.extend(self.port.to_bytes(2, byteorder='big'))
        try:
            byte_list.extend(self.payload)
        except Exception as e:
            byte_list.extend(self.payload.encode("utf-8"))
        return byte_list

    @staticmethod
    def generate_packet_from_bytes(data):
        if (len(data) < MINIMUM_LEN) or (len(data) > MAXIMUM_LEN):
            raise ValueError(
                "UDPPacket is with size {} bytes is not allowed.".format(len(data)))
        packet = UDPPacket.create_packet(
            ipaddress.ip_address(data[5:9]), int.from_bytes(
                data[9:11], byteorder='big'),
            int.from_bytes(data[1:5], byteorder='big'), int.from_bytes(
                data[0:1], byteorder='big'),
            data[11:]
        )
        return packet


class udpsocket():

    def __init__(self, router=('localhost', 3000)):
        self.router = router
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receiver = None
        self.sequence = uint(0)
        self.timer_mgmt = [False, False, 0]

    def hand_shaking(self, address, sequence):
        ip = ipaddress.ip_address(socket.gethostbyname(address[0]))
        self.conn.connect(self.router)
        for i in range(0, 15):
            try:
                self.conn.sendall(UDPPacket.create_packet(
                    ip, address[1], sequence, SYN_BIT_VAL).convert_data_into_bytes())
                self.conn.settimeout(HANDSHAKE_TIME_OUT)
                data, route = self.conn.recvfrom(FRAME_SIZE)
                packet = UDPPacket.generate_packet_from_bytes(data)
                self.conn.sendall(UDPPacket.create_packet(
                    packet.ip, packet.port, sequence, SYN_ACK_BIT_VAL).convert_data_into_bytes())
                return (packet.ip, packet.port)
            except Exception as e:
                pass
            time.sleep(1)
        raise Exception("Time out while Handshaking!")

    def connect(self, address):
        try:
            self.receiver = self.hand_shaking(address, self.sequence)
            self.sequence = UDPPacket.generate_sequence(self.sequence, 1)
        except Exception as e:
            raise e

    def get_sequence_no(self, sliding_window, comp_sequence):
        for s_no, sequence_or_packet in enumerate(sliding_window):
            if (sequence_or_packet == comp_sequence) or \
                (isinstance(sequence_or_packet, UDPPacket) and
                    sequence_or_packet.sequence == comp_sequence):
                return s_no

    def reset_sliding_window(self, sliding_window):
        for sequence_or_packet in sliding_window:
            if isinstance(sequence_or_packet, UDPPacket):
                return False
        return True

    def generate_sliding_window_list(self, sequence):
        sliding_window = []
        for i in range(0, SLIDING_WINDOW_SIZE):
            sliding_window.append(
                int(UDPPacket.generate_sequence(sequence, i)))
        return sliding_window

    def updatetimer(self):
        self.timer_mgmt[0] = True
        self.timer_mgmt[1] = False

    def resettimer(self):
        self.timer_mgmt[0] = False
        self.timer_mgmt[1] = True

    def sendto(self, data, stop=True):
        start_time = time.time()
        timer = None
        self.timer_mgmt = [False, False, 0]
        sliding_window = self.generate_sliding_window_list(self.sequence)
        res_data_dict = UDPPacket.data_package(self.receiver[0], self.receiver[
                                               1], data, stop, self.sequence)
        packet_list = res_data_dict.get('package', [])
        self.sequence = res_data_dict.get('sequence', 0)
        temp_packet = packet_list.copy()
        while len(packet_list) != 0 or not self.reset_sliding_window(sliding_window):
            while not isinstance(sliding_window[0], UDPPacket):
                if len(packet_list) <= 0:
                    break
                sliding_window[0] = packet_list.pop(0)
                sliding_window.append(sliding_window.pop(0))
            for i in range(0, len(sliding_window)):
                if isinstance(sliding_window[i], UDPPacket):
                    if sliding_window[i].is_send == False:
                        self.conn.sendall(
                            sliding_window[i].convert_data_into_bytes())
                        sliding_window[i].is_send = True
                    elif self.timer_mgmt[0]:
                        self.conn.sendall(
                            sliding_window[i].convert_data_into_bytes())
            if not self.timer_mgmt[1]:
                timer = Timer(RECIEVER_TIME_OUT, self.updatetimer)
                self.resettimer()
                timer.start()

            while not self.reset_sliding_window(sliding_window):
                self.conn.settimeout(SLIDE_TIME)
                try:
                    data, route = self.conn.recvfrom(FRAME_SIZE)
                    p1 = UDPPacket.generate_packet_from_bytes(data)
                    if p1.packet_type == BYE_BIT_VAL and p1.sequence == UDPPacket.generate_sequence(self.sequence):
                        if timer:
                            timer.cancel()
                        self.conn.settimeout(HANDSHAKE_TIME_OUT)
                        for i in range(0, 5 + int(((time.time() - start_time) / len(temp_packet)) * HANDSHAKE_TIME_OUT)):
                            self.conn.sendall(
                                UDPPacket.create_packet(
                                    self.receiver[0], self.receiver[1]
                                ).convert_data_into_bytes(), BYE_BIT_VAL)
                        return
                    elif p1.packet_type == ACK_BIT_VAL:
                        window_index = self.get_sequence_no(
                            sliding_window, p1.sequence)
                        if not window_index == None:
                            sliding_window[window_index] = int(
                                UDPPacket.generate_sequence(p1.sequence, SLIDING_WINDOW_SIZE))
                    elif p1.packet_type == NAK_BIT_VAL:
                        if p1.sequence in sliding_window:
                            window_index = self.get_sequence_no(
                                sliding_window, p1.sequence)
                            self.conn.sendall(
                                sliding_window[window_index].convert_data_into_bytes())
                except Exception as e:
                    break
            while not isinstance(sliding_window[0], UDPPacket):
                if len(packet_list) <= 0:
                    break
                sliding_window[0] = packet_list.pop(0)
                sliding_window.append(sliding_window.pop(0))
            if not self.timer_mgmt[0]:
                continue
            else:
                if not len(packet_list):
                    self.timer_mgmt[2] += 1
                    if self.timer_mgmt[2] == 5 + int(2 * ((time.time() - start_time) / len(temp_packet)) / RECIEVER_TIME_OUT):
                        return
        if timer:
            timer.cancel()

    def listen(self, port):
        pass
        
    def recvfrom(self):
        start_time = time.time()
        packages = 0
        byte_data_list = bytearray()
        sliding_window = self.generate_sliding_window_list(self.sequence)
        self.conn.settimeout(15 * RECIEVER_TIME_OUT)
        while True:
            if isinstance(sliding_window[0], UDPPacket):
                single_packet = sliding_window[0]
                if len(single_packet.payload) == 0:
                    self.conn.settimeout(HANDSHAKE_TIME_OUT)
                    for i in range(0, 5 + int(((time.time() - start_time) / packages) * HANDSHAKE_TIME_OUT)):
                        self.conn.sendall(
                            UDPPacket.create_packet(
                                self.receiver[0], self.receiver[1], UDPPacket.generate_sequence(self.sequence), BYE_BIT_VAL
                            ).convert_data_into_bytes())
                        try:
                            data = self.conn.recv(FRAME_SIZE)
                        except Exception as e:
                            continue
                        received_packet = UDPPacket.generate_packet_from_bytes(
                            data)
                        if received_packet.packet_type == BYE_BIT_VAL:
                            break
                    return byte_data_list
            data = self.conn.recv(FRAME_SIZE)
            received_packet = UDPPacket.generate_packet_from_bytes(data)
            if not (received_packet.ip == self.receiver[0] and received_packet.port == self.receiver[1]):
                continue
            if not received_packet.packet_type == DATA_BIT_VAL:
                continue
            else:
                if received_packet.sequence in sliding_window:
                    window_index = self.get_sequence_no(
                        sliding_window, received_packet.sequence)
                    sliding_window[window_index] = received_packet
                    packages = packages + 1
                while (isinstance(sliding_window[0], UDPPacket)):
                    single_packet = sliding_window[0]
                    if len(single_packet.payload) == 0:
                        self.sequence = UDPPacket.generate_sequence(
                            single_packet.sequence, 1)
                        break
                    p1 = sliding_window.pop(0)
                    self.sequence = UDPPacket.generate_sequence(p1.sequence, 1)
                    temp_sequence = None
                    if isinstance(sliding_window[len(sliding_window) - 1], UDPPacket):
                        temp_sequence = sliding_window[
                            len(sliding_window) - 1].sequence
                    else:
                        temp_sequence = sliding_window[len(sliding_window) - 1]
                    sliding_window.append(
                        UDPPacket.generate_sequence(
                            temp_sequence, 1
                        )
                    )
                    byte_data_list.extend(p1.payload)
                self.conn.sendall(
                    UDPPacket.create_packet(
                        self.receiver[0], self.receiver[1],
                        received_packet.sequence, ACK_BIT_VAL).convert_data_into_bytes()
                    )

    def bind(self, ip):
        self.conn.bind(ip)

    def accept(self):
        try:
            data, router = self.conn.recvfrom(MAXIMUM_LEN)
            packet = UDPPacket.generate_packet_from_bytes(data)
            if packet.packet_type == SYN_BIT_VAL:
                udp_sock = udpsocket()
                udp_sock.conn.sendto(UDPPacket.create_packet(
                    packet.ip, packet.port, packet.sequence, SYN_ACK_BIT_VAL
                ).convert_data_into_bytes(), self.router)
                udp_sock.receiver = (packet.ip, packet.port)
                udp_sock.sequence = UDPPacket.generate_sequence(
                    packet.sequence, 1)
                udp_sock.conn.connect(self.router)
                print("Router: ", router)
                print("UDPPacket: ", packet)
                return udp_sock, (packet.ip, packet.port)
            else:
                return None, None
        except Exception as e:
            return None, None

    def close(self):
        self.conn.close()
