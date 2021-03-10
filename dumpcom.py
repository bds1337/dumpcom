#!/usr/bin/env python3 
#coding: utf-8

import serial, json, threading, sys, os, glob
import time
from time import sleep

import select
import socket
import queue

# tcp port
HOST = '127.0.0.1' 
#HOST = '192.168.36.137' 

# serial/com
SERIALPORT = '/dev/ttyACM0'
BAUDRATE = 115200
DELAY = 0.1

# defines
T_PULSE = 1
T_PRESSURE = 2
T_RSSI = 3

send_queue = queue.Queue()

class Dumpcom:
    def __init__(self, serialport: str, baudrate: int, delay: float):
        self.serialport = serialport
        self.baudrate = baudrate
        self.delay = delay
        self.listen_com_thread = False
        self.socket_send_thread = False
        self.thread = None
        self.com = serial.Serial(self.serialport, self.baudrate, timeout=self.delay, rtscts=True)
        self.com.reset_input_buffer()

    def __del__(self):
        self.com.close()

    def listen_com(self):
        self.listen_com_thread = True
        # logging.info("UART console saving to file: " + self.logfilename)
        self.thread = threading.Thread(target=self._listen, args=())
        self.thread.start()

    def listen_com_stop(self):
        self.listen_com_thread = False

    def make_json(self, msg: dict) -> str:
        return json.dumps(msg)

    def _unique_lines(self, lines: list) -> list:
        return [list(x) for x in set(tuple(x) for x in lines)]

    def _parse(self, lines: list):
        if (lines is None):
            return
        buff = []
        for line in lines:
            if (len(line) < 6):
                return
            ret = {}
            if (line[2] == T_PULSE and len(line) == 6):
                ret['tag_id']        = int(f"{int(hex(line[3])+hex(line[4])[2:], 16)}")
                ret['pulse']         = line[5]
            elif (line[2] == T_PRESSURE and len(line) == 7):
                ret['tag_id']        = int(f"{int(hex(line[3])+hex(line[4])[2:], 16)}")
                ret['pressure_up']   = line[5]
                ret['pressure_down'] = line[6]
            elif (line[2] == T_RSSI and len(line) == 8):
                ret['beacon_id']     = int(f"{int(hex(line[3])+hex(line[4])[2:], 16)}")
                ret['rssi']          = line[5] - (1 << 8) # if line[5] & (1 << (8-1)):
                ret['tag_id']        = int(f"{int(hex(line[6])+hex(line[7])[2:], 16)}")
                #ret['tag_id']        = int(f"{line[6]}{line[7]}")
            if (ret):
                buff.append(ret)
        return buff

    def _make_lines(self, lines: list, unique=False):
        if (lines is None):
            return
        buff = []
        while (len(lines) > 0):
            #if (lines[1] != 138):
            #    print("error")
            buff.append(lines[:lines[0] + 1])
            del lines[:lines[0] + 1]
        if (unique):
            # remove same lines
            buff = (self._unique_lines(buff))
        #print(f"buff {buff}")
        return buff

    def _listen(self):
        while (self.listen_com_thread):
            #data = self._read_com()
            for pkt in self._read_com_yi():
                print(f"data: {pkt}")
            if (False):
                print(f"data: {data}")
                continue
                parsed_list =  self._parse( self._make_lines(data) ) 
                if (parsed_list is None):
                    #print("error None")
                    continue
                for dct in parsed_list:
                    '''
                    if "pressure_up" in dct:
                        print(dct)
                    if "pulse" in dct:
                        print(dct)
                    '''
                    print(dct)
                    #print("parsed!")
                    send_queue.put( ( self.make_json( dct ) ) )

    def _read_com_yi(self):
        tmp = bytearray([])
        while True:
            tmp += bytearray(self.com.read())
            tmp_len = len(tmp)
            if tmp_len > 0:
                pkt_len = tmp[0]
                if tmp_len > pkt_len:
                    data = tmp[:pkt_len+1]
                    yield data
                    tmp = tmp[pkt_len+1:]

    def _read_com(self) -> list:
        buff = []
        data = ''
        byte = ''
        prevbyte = ''
        package_size = 0
        while (self.com.in_waiting > 0):
            prevbyte = byte
            byte = self.com.read(1).hex()
            print(f"BYTE {len(byte)} {byte}")
            if ( byte == '8a' ):
                package_size = int(prevbyte, 16)
                print(f"package_size {len(package_size)} {package_size}")
                #data += data
            time.sleep(0.01)
            data += byte
            if (len(data) > package_size):
                print(f"FULL DATA {data}")
                break
        buff = (list(data))
        #print(buff)
        buff = b''
        if (len(buff) > 0):
            return buff 

    def _read_com_line(self) -> list:
        buff = []
        data = b''
        while (self.com.in_waiting > 0):
            try:
                data = self.com.readline()
                #time.sleep(0.01)
            except Exception as ex:
                print(ex)
                continue
            buff = (list(data))
        if (len(buff) > 0):
            return buff         

def send(soc, jsn):
    if (jsn == 'null' or jsn == '{}'):
        return
    out = b''
    try:
        #soc.settimeout(3)
        soc.sendall( jsn.encode() )
    except socket.error as err:
        print(f'{err}')
    #finally:
    #   soc.close()

if __name__ == '__main__':
    ser = SERIALPORT
    host = HOST
    if ( len(sys.argv) > 1 ):
        ser = sys.argv[1]
        if ( len(sys.argv) > 2 ):
            host = sys.argv[2]
    if ( not glob.glob(ser) ):
        print(f"\tTry another port, \"{ser}\" not exist")
        print("\tUsage:\n\tpython3 dumpcom.py /dev/ttyACM0 127.0.0.1")
        exit()
    
    #serial thread for UART listener and parser
    com = Dumpcom(ser, BAUDRATE, DELAY)
    com.listen_com()

    #main thread for tcp connections
    while (True):
        a = send_queue.get()
        if (a):
            if (a == 'null' or a == '{}'):
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:   
                    sock.setblocking(False)
                    sock.settimeout(3)
                    sock.connect(( host, 9090))
                    #print(f"sending {a}")
                    sock.sendall( a.encode() )
            except socket.error as err:
                print(f'{err}')
