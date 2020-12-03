from numpy import uint32 as unit
import ipaddress

MIN_LEN = 11
MAX_LEN = 1024

DATA = 0
ACK = 1
SYN = 2
SYN_ACK = 3
NAK = 4
BYE = 8


#  1        4       4     2        1013
# ------------------------------------------
# type | sequence | ip | port | sub-content
def control_package(type, peer_ip, peer_port, sequence=0):
    packet = Packet(
        packet_type=type,
        seq_num=sequence,
        peer_ip_addr=peer_ip,
        peer_port=peer_port,
        payload="".encode("utf-8")
    )
    return packet

def terminal_package(peer_ip, peer_port, sequence=0):
    packet = Packet(
        packet_type=DATA,
               seq_num=sequence,
               peer_ip_addr=peer_ip,
               peer_port=peer_port,
               payload="".encode("utf-8"))
    return packet

def data_package(peer_ip, peer_port, content, stop, sequence=0):
    p_list = list()
    c_byte = content#.encode("utf-8")
    while len(c_byte) != 0:
        p_list.append(c_byte[:10])
        c_byte = c_byte[10:]
    # print(p_list)
    package = list()
    for payload in p_list:
        p = Packet(packet_type=DATA,
                   seq_num=sequence,
                   peer_ip_addr=peer_ip,
                   peer_port=peer_port,
                   payload=payload)
        package.append(p)
        sequence = grow_sequence(sequence, 1)
        print(p)
    if stop:
        p = terminal_package(peer_ip, peer_port, sequence)
        package.append(p)
        sequence = grow_sequence(sequence, 1)
    return package, sequence


def grow_sequence(sequence, add):
    se = unit(sequence) + unit(add)
    if se < sequence:
        se = se + unit(1)
    return se

def minus_sequence(sequence):
    se = unit(sequence) - unit(1)
    if se == 0:
        se = se - unit(1)
    return se

class Packet:
    """
    Packet represents a simulated UDP packet.
    """

    def __init__(self, packet_type, seq_num, peer_ip_addr, peer_port, payload):
        self.packet_type = int(packet_type)
        self.seq_num = int(seq_num)
        self.peer_ip_addr = peer_ip_addr
        self.peer_port = int(peer_port)
        self.payload = payload
        self.send = False

    def to_bytes(self):
        """
        to_raw returns a bytearray representation of the packet in big-endian order.
        """
        buf = bytearray()
        buf.extend(self.packet_type.to_bytes(1, byteorder='big'))
        buf.extend(self.seq_num.to_bytes(4, byteorder='big'))
        buf.extend(self.peer_ip_addr.packed)
        buf.extend(self.peer_port.to_bytes(2, byteorder='big'))

        buf.extend(self.payload)

        return buf

    def __repr__(self, *args, **kwargs):
        return "#%d, peer=%s:%s, size=%d" % (self.seq_num, self.peer_ip_addr, self.peer_port, len(self.payload))

    @staticmethod
    def from_bytes(raw):
        if len(raw) < MIN_LEN:
            raise ValueError("packet is too short: {} bytes".format(len(raw)))
        if len(raw) > MAX_LEN:
            raise ValueError("packet is exceeded max length: {} bytes".format(len(raw)))

        curr = [0, 0]

        def nbytes(n):
            curr[0], curr[1] = curr[1], curr[1] + n
            return raw[curr[0]: curr[1]]

        packet_type = int.from_bytes(nbytes(1), byteorder='big')
        seq_num = int.from_bytes(nbytes(4), byteorder='big')
        peer_addr = ipaddress.ip_address(nbytes(4))
        peer_port = int.from_bytes(nbytes(2), byteorder='big')
        payload = raw[curr[1]:]

        return Packet(packet_type=packet_type,
                      seq_num=seq_num,
                      peer_ip_addr=peer_addr,
                      peer_port=peer_port,
                      payload=payload)
