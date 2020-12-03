# python3 httpfs.py -arq -v -p 8080 -d .

# python3 httpc.py get -v -arq -p 8080 "http://localhost/"
# python3 httpc.py get -v -arq -p 8080 "http://localhost/random.json"
# python3 httpc.py get -arq -p 8080 -o "output.json" "http://localhost/random.json"

# python3 httpc.py post -arq -p 8080 -d "{"Assignment":"3"}" "http://localhost/bar.json"


# ./routers/macos/router --port=3000 --drop-rate=0.2 --max-delay=100ms --seed 2387230234324

import unittest
import socket
import logging
import time
from numpy import uint32
from threading import Timer

import ipaddress
import packet

WINDOW = 10
FRAME_SIZE = 1024
RECV_TIME_OUT = 5
HANDSHAKE_TIME_OUT = 2
SLIDE_TIME = 0.1

log = logging.getLogger('ARQ')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] >> %(message)s << %(funcName)s() %(asctime)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.setLevel(logging.DEBUG)
log.addHandler(fh)
log.addHandler(ch)


class TestSocketMethods(unittest.TestCase):
    def test_send(self):
        return

class HandShakeException(Exception):
    pass

class SocketException(Exception):
    pass

class FlushException(Exception):
    pass

class Singleton(object):
    _instance = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

class rsocket():#__socket.socket):

    def __init__(self, router=('localhost', 3000), sequence = 0):
        self.router = router
        self.sequence = uint32(sequence)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.remote = None
        self.shakeack = None
        self.data = list()
        self.control = list()
        self.client_list = list()

    def handshaking(self, address, sequence):
        peer_ip = ipaddress.ip_address(socket.gethostbyname(address[0]))
        # log.debug(peer_ip)
        self.conn.connect(self.router)
        for i in range(0, 20):
            try:
                # conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.conn.sendall(packet.control_package(packet.SYN, peer_ip, address[1], sequence).to_bytes())
                self.conn.settimeout(HANDSHAKE_TIME_OUT)
                data, route = self.conn.recvfrom(FRAME_SIZE)
                p = packet.Packet.from_bytes(data)
                # log.debug("Router:{}".format(route))
                # log.debug("Packet:{}".format(p))
                # log.debug("Payload:{}".format(p.payload.decode("utf-8")))

                # conn.sendto(control_package(packet.ACK, p.peer_ip_addr, p.peer_port, sequence), self.router)
                self.shakeack = packet.control_package(packet.SYN_ACK, p.peer_ip_addr, p.peer_port, sequence).to_bytes()
                self.conn.sendall(packet.control_package(packet.SYN_ACK, p.peer_ip_addr, p.peer_port, sequence).to_bytes())
                return (p.peer_ip_addr, p.peer_port)

            except Exception as e:
                log.error(e)
            time.sleep(1)
        raise HandShakeException("Hand shake timeout")

    def connect(self, address):

        try:
            self.remote = self.handshaking(address, self.sequence)
            self.sequence = packet.grow_sequence(self.sequence, 1)
        except HandShakeException as e:
            log.error(e)
            raise e

    def findIndex(self, window, se):
        for i in range(0, len(window)):
            if window[i] == se or (isinstance(window[i], packet.Packet) and window[i].seq_num == se):
                return i

    def getwindows(self, window):
        windows = [i for i in window]
        for i in range(0, len(windows)):
            if isinstance(windows[i], packet.Packet):
                windows[i] = str(windows[i].seq_num)
        return windows

    def flushwindow(self, window):
        for i in range(0, len(window)):
            if isinstance(window[i], packet.Packet):
                return False
        return True

    def sendall(self, data, stop=True):
        start = time.time()
        timer = None
        # mapping = {}
        # log.debug("init send sequence#:{}".format(self.sequence))
        window = [-i for i in range(1, WINDOW + 1)]
        for i in range(0, WINDOW):
            window[i] = int(packet.grow_sequence(self.sequence, i))
        package, self.sequence = packet.data_package(self.remote[0], self.remote[1], data, stop, self.sequence)
        original = package.copy()
        timeout = [False, False, 0]
        # log.debug("init widow:{}".format(window))
        while len(package) != 0 or not self.flushwindow(window):
            # fill the slot and slide
            while not isinstance(window[0], packet.Packet):
                if len(package) > 0:
                    window[0] = package.pop(0)
                    window.append(window.pop(0))
                else:
                    # log.debug("almost send all package!")
                    break
            #send window
            for i in range(0, len(window)):
                if isinstance(window[i], packet.Packet):
                    if not window[i].send:
                        # log.debug("send {} slot, package #{}".format(i, window[i].seq_num))
                        self.conn.sendall(window[i].to_bytes())
                        window[i].send = True
                    elif timeout[0]:
                        # log.debug("resend {} slot, package #{}".format(i, window[i].seq_num))
                        self.conn.sendall(window[i].to_bytes())
                    else:
                        log.debug("slot {} waiting for timeout".format(i))
            def out(timeout):
                # log.debug("receive time out")
                timeout[0] = True
                timeout[1] = False

            if not timeout[1]:
                timer = Timer(RECV_TIME_OUT, out, [timeout])
                timer.start()
                timeout[0] = False
                timeout[1] = True
            # print("[DEBUG] >> ")
            # log.debug("after send, widow:{}".format(self.getwindows(window)))
            # log.debug("receive from remote")
            #receive slot
            while not self.flushwindow(window):
                self.conn.settimeout(SLIDE_TIME)
                try:
                    data, route = self.conn.recvfrom(FRAME_SIZE)  # buffer size is 1024 bytes
                    p = packet.Packet.from_bytes(data)
                    # log.debug("Recv:{}".format(p))
                    if p.packet_type == packet.BYE and p.seq_num == packet.minus_sequence(self.sequence):#BYE-SYN
                        timer.cancel()
                        self.conn.settimeout(HANDSHAKE_TIME_OUT)
                        # for i in range(0, 2):
                        #     self.conn.sendall(
                        #         packet.control_package(packet.BYE, self.remote[0], self.remote[1],
                        #                                uint32(0)).to_bytes())
                        spend = time.time()-start
                        rate = spend/len(original)
                        # log.debug("resend {} times for BYE".format(int(rate * HANDSHAKE_TIME_OUT)))
                        for i in range(0, 5+int(rate * HANDSHAKE_TIME_OUT)):
                            #BYE-ACK
                            self.conn.sendall(
                                packet.control_package(packet.BYE, self.remote[0], self.remote[1],
                                                       uint32(0)).to_bytes())
                            # try:
                            #     data = self.conn.recv(FRAME_SIZE)
                            # except Exception as e:
                            #     continue
                            # recv_packet = packet.Packet.from_bytes(data)
                            # if recv_packet.packet_type == packet.BYE:#BYE-ACK2
                            #     break
                        return
                    elif p.packet_type == packet.DATA:
                        # log.debug("cache data package")
                        self.data.append(p)
                    elif p.packet_type == packet.ACK:
                        window_index = self.findIndex(window, p.seq_num)
                        if not window_index == None:
                            # log.debug("recv ACK {} for slot {}".format(p.seq_num, window_index))
                            # log.debug("old window:{}".format(self.getwindows(window)))
                            window[window_index] = int(packet.grow_sequence(p.seq_num, WINDOW))
                            # log.debug("new window:{}".format(self.getwindows(window)))
                        else:
                            log.debug("recv ACK {} but not belongs any window slot, drop!".format(p.seq_num))
                    elif p.packet_type == packet.NAK:
                        if p.seq_num in window:
                            window_index = self.findIndex(window, p.seq_num)
                            # log.debug("recv NAK {} for lot {}".format(p.seq_num, window_index))
                            self.conn.sendall(window[window_index].to_bytes())
                            # log.debug("resend {} slot, package #{}".format(window_index, p.seq_num))
                        else:
                            log.debug("recv NAK {} but not belongs any window slot, drop!".format(p.seq_num))
                    else:
                        print("UFO")
                except socket.timeout:
                    break
            while not isinstance(window[0], packet.Packet):
                if len(package) > 0:
                    # log.debug("slide window")
                    window[0] = package.pop(0)
                    window.append(window.pop(0))
                else:
                    # log.debug("almost send all package!")
                    break
            # log.debug("after slide widow:{}".format(self.getwindows(window)))
            if not timeout[0]:
                continue
            else:
                # if len(package) == len(original)-10:
                #     # for i in range(0, 10):
                #     #     #flood the router
                #     self.conn.sendall(self.shakeack)
                #     timeout[2] = timeout[2] + 1
                #     if timeout[2] == 10:
                #         raise SocketException("Connection exception, maybe the last handshake package being dropped")
                # el
                if len(package) == 0:#need flush buffer
                    spend = time.time() - start
                    rate = spend / len(original)
                    packs = len([w for w in window if isinstance(w, packet.Packet)])
                    # log.debug("resend {} packs packages {} times to flush data".format(packs, int(packs * rate / RECV_TIME_OUT)))
                    timeout[2] = timeout[2] + 1
                    if timeout[2] == 5 + int(2*rate / RECV_TIME_OUT):
                        return
                        # raise FlushException("Flush exception")
        timer.cancel()

    def recv_data_package(self, packet):
        index = 0
        timer = None
        # mapping = {}
        # log.debug("init recv sequence#:{}".format(self.sequence))
        # window = [-i for i in range(1, WINDOW + 1)]
        # for i in range(0, WINDOW):
        #     window[i] = -int(packet.grow_sequence(self.sequence, i))

    def recv_control_package(self, packet):
        self.control.append(packet)

    def recvall(self):#, buffersize):
        start = time.time()
        packages = 0
        cache = bytearray()
        # log.debug("init recv sequence#:{}".format(self.sequence))
        window = [-i for i in range(1, WINDOW + 1)]
        for i in range(0, WINDOW):
            window[i] = int(packet.grow_sequence(self.sequence, i))
        self.conn.settimeout(20*RECV_TIME_OUT)
        while True:
            if isinstance(window[0], packet.Packet):
                peek = window[0]
                if len(peek.payload) == 0:
                    # log.debug("pop terminate packet, se#{}".format(peek.seq_num))
                    # self.sequence = packet.grow_sequence(p.seq_num, 1)
                    self.conn.settimeout(HANDSHAKE_TIME_OUT)
                    spend = time.time()-start
                    rate = spend/packages
                    # log.debug("resend {} times for BYE".format(int(rate * HANDSHAKE_TIME_OUT)))
                    for i in range(0, 5+int(rate * HANDSHAKE_TIME_OUT)):
                        #BYE-SYN
                        self.conn.sendall(
                            packet.control_package(packet.BYE, self.remote[0], self.remote[1], packet.minus_sequence(self.sequence)).to_bytes())
                        try:
                           #BYE-ACK
                           data = self.conn.recv(FRAME_SIZE)
                        except Exception as e:
                           continue
                        recv_packet = packet.Packet.from_bytes(data)
                        if recv_packet.packet_type == packet.BYE:
                           break
                    # BYE-ACK2
                    # self.conn.sendall(
                    #     packet.control_package(packet.BYE, self.remote[0], self.remote[1],
                    #                            uint32(0)).to_bytes())

                    return cache
                # p = window.pop(0)
                # self.sequence = packet.grow_sequence(p.seq_num, 1)
                # log.debug("pop first slot, se#{}".format(p.seq_num))
                # last = window[len(window) - 1]
                # if isinstance(last, packet.Packet):
                #     window.append(packet.grow_sequence(last.seq_num, 1))
                # else:
                #     window.append(packet.grow_sequence(last, 1))
                # cache.extend(p.payload)

                # if len(cache) >= buffersize:
                #     data = cache[:buffersize]
                #     cache = cache[buffersize:]
                #     return data
            # if len(cache) > 0:
            #     return cache
            data = self.conn.recv(FRAME_SIZE)
            recv_packet = packet.Packet.from_bytes(data)
            # print("Router: ", route)
            # log.debug("Packet: {}".format(recv_packet))
            # print("Payload: ", p.payload.decode("utf-8"))

            # print("received message:" + data.decode("utf-8") + " addr:"+str(addr))
            if not (recv_packet.peer_ip_addr == self.remote[0] and recv_packet.peer_port == self.remote[1]):
                # log.debug("recv bad data from {}:{}".format(recv_packet.peer_ip_addr, recv_packet.peer_port))
                continue
            if not recv_packet.packet_type == packet.DATA:
                # log.debug("recv control packet, cache")
                self.recv_control_package(recv_packet)
            else:
                if recv_packet.seq_num in window:
                    window_index = self.findIndex(window, recv_packet.seq_num)
                    window[window_index] = recv_packet
                    # log.debug("slot {} recv data se#{}".format(window_index, recv_packet.seq_num))
                    packages = packages + 1
                else:
                    # if not possible to recv future expect se#
                    log.debug("recv out of expect or duplicate se#{}".format(recv_packet.seq_num))
                while (isinstance(window[0], packet.Packet)):
                    peek = window[0]
                    if len(peek.payload) == 0:
                        # log.debug("pop terminate packet, se#{}".format(peek.seq_num))
                        self.sequence = packet.grow_sequence(peek.seq_num, 1)
                        break
                    pop_packet = window.pop(0)
                    self.sequence = packet.grow_sequence(pop_packet.seq_num, 1)
                    # log.debug("pop first slot, se#{}".format(pop_packet.seq_num))
                    last = window[len(window) - 1]
                    if isinstance(last, packet.Packet):
                        window.append(packet.grow_sequence(last.seq_num, 1))
                    else:
                        window.append(packet.grow_sequence(last, 1))
                    cache.extend(pop_packet.payload)
                # log.debug("send ACK#{}".format(recv_packet.seq_num))
                # log.debug("new window:{}".format(self.getwindows(window)))
                self.conn.sendall(packet.control_package(packet.ACK, self.remote[0], self.remote[1], recv_packet.seq_num).to_bytes())
                # if len(cache) > 0:
                #     return cache
        # return self.conn.recv(buffersize)

    def bind(self, address):
        self.conn.bind(address)

    def listen(self, max):
        # self.conn.listen(max)
        self.MAX = max

    def accept(self):
        try:
            data, route = self.conn.recvfrom(1024)  # buffer size is 1024 bytes

            p = packet.Packet.from_bytes(data)
            # print("Router: ", route)
            # print("Packet: ", p)
            # print("Payload: ", p.payload.decode("utf-8"))
            if len(self.client_list) > self.MAX:
                return None, None
            if p.packet_type == packet.SYN:
                return self.accept_client(p)
        except socket.timeout as e:
            log.error(e)
            return None, None

    def accept_client(self, p):
        print("create a new thread")
        # peer_ip = ipaddress.ip_address(socket.gethostbyname(addr[0]))
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock = rsocket()
        sock.conn.sendto(packet.control_package(packet.SYN_ACK, p.peer_ip_addr, p.peer_port, p.seq_num).to_bytes(), self.router)
        # print("send SYN-ACK")
        # sock.sendto("SYNACK".encode("ascii"), addr)
        # sock.settimeout(15)
        # 等不等的意义不大了
        # data = sock.conn.recv(1024)  # buffer size is 1024 bytes
        # p = packet.Packet.from_bytes(data)

        recv_list = list()
        if p.packet_type == packet.SYN:
            sock.sequence = packet.grow_sequence(p.seq_num, 1)
            sock.remote = (p.peer_ip_addr, p.peer_port)
            sock.conn.connect(self.router)
            # print("receive ACK, sequence #:" + str(p.seq_num))
            # # print("Router: ", route)
            # print("Packet: ", p)
            # print("Payload: ", p.payload.decode("utf-8"))
            return sock, (p.peer_ip_addr, p.peer_port)
        return None, None
            # while True:
            #     data, route = sock.recvfrom(1024)  # buffer size is 1024 bytes
            #     p = Packet.from_bytes(data)
            #     print("Router: ", route)
            #     print("Packet: ", p)
            #     # print("Payload: ", p.payload.decode("utf-8"))
            #     if p.seq_num % 5 == 0:
            #         sock.sendto(packet.control_package(packet.ACK, peer_ip, peer_port, p.seq_num).to_bytes(), route)
            #     else:
            #         sock.sendto(packet.control_package(packet.ACK, peer_ip, peer_port, p.seq_num).to_bytes(), route)
            #     recv_list.append(p)
            #     if len(p.payload) == 0:
            #         deliver_msg(recv_list)

    def close(self):  # real signature unknown; restored from __doc__
        """
        close()

        Close the socket.  It cannot be used after this call.
        """
        self.conn.close()
        for c in self.client_list:
            c.close()

    def settimeout(self, timeout):
        pass

    def packageContent(self, type, sequence, ip, port, content):

        return []

if __name__ == '__main__':
    unittest.main()
