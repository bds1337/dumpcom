#!/usr/bin/env python3 
#coding: utf-8

import serial, json, threading, sys, glob
from time import sleep

import select
import socket
import queue
import binascii

# tcp port
#HOST = '127.0.0.1' 
HOST = '192.168.36.137' 

# TCP timeout
TIMEOUT = 0.1

# serial/com
SERIALPORT  = '/dev/ttyACM0'
BAUDRATE    = 115200
DELAY       = 0.0001

# defines
T_PULSE         = 1
T_PRESSURE      = 2
T_SATURATION    = 4
T_ALL           = 5
T_RSSI          = 3

send_queue = queue.Queue()
send_queue.maxsize = 30

class Dumpcom:
    def __init__(self, serialport, baudrate=BAUDRATE, delay=DELAY):
        self.serialport = serialport
        self.baudrate = baudrate
        self.delay = delay
        self.listen_com_thread = False
        self.socket_send_thread = False
        self.thread = None
        self.com = serial.Serial(self.serialport, self.baudrate, timeout=self.delay, rtscts=True)
        self.com.reset_input_buffer()

    def __del__(self):
        self.listen_com_stop()
        self.com.close()

    def listen_com(self):
        self.listen_com_thread = True
        self.thread = threading.Thread(target=self._listen, args=())
        self.thread.start()

    def listen_com_stop(self):
        send_queue.put(None)
        self.listen_com_thread = False

    def listen_com_is_running(self):
        return self.listen_com_thread

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
                ret['tag_id']        = (line[3] << 8)+(line[4])
                ret['pulse']         = line[5]
            elif (line[2] == T_PRESSURE and len(line) == 7):
                ret['tag_id']        = (line[3] << 8)+(line[4])
                ret['pressure_up']   = line[5]
                ret['pressure_down'] = line[6]
            elif (line[2] == T_SATURATION and len(line) == 6):
                ret['tag_id']        = (line[3] << 8)+(line[4])
                ret['saturation']         = line[5]
            elif (line[2] == T_ALL and len(line) == 9):
                ret['tag_id']        = (line[3] << 8)+(line[4])
                ret['pulse']         = line[5]
                ret['saturation']    = line[6]
                ret['pressure_up']   = line[7]
                ret['pressure_down'] = line[8]
            elif (line[2] == T_RSSI and len(line) == 8):
                ret['beacon_id']     = (line[3] << 8)+(line[4])
                ret['rssi']          = line[5] - (1 << 8) # if line[5] & (1 << (8-1)):
                ret['tag_id']        = (line[6] << 8)+(line[7])
            if (ret):
                buff.append(ret)
        return buff

    def _make_lines(self, lines: list, unique=True):
        if (lines is None):
            return
        buff = []
        while (len(lines) > 0):
            buff.append(lines[:lines[0] + 1])
            del lines[:lines[0] + 1]
        if (unique):
            # remove same lines
            buff = (self._unique_lines(buff))
        return buff

    def _listen(self):
        while (self.listen_com_thread):
            for pkt in self._read_com_yi():
                #print(f"data: {pkt}")
                if len(pkt) < 2:
                    print(f"Invalid pkt size: {pkt}")
                    continue
                if (pkt[1] != 0x8A):
                    print(f"Invalid pkt type: {pkt}")
                    continue
                parsed_list = self._parse( self._make_lines(pkt) ) 
                if (parsed_list is None):
                    continue
                for dct in parsed_list:
                    print(dct)
                    try:
                        send_queue.put_nowait( ( self.make_json( dct ) ) )
                    except queue.Full:
                        #print("queue is full!")
                        continue

    def _read_com_yi(self):
        tmp = bytearray([])
        tmp2 = b''
        while True:
            try:
                tmp += bytearray(self.com.read())
            except serial.serialutil.SerialException as e:
                print(f"lost connection with com-device: {e}")
                self.listen_com_stop()
                break
            tmp_len = len(tmp)
            if tmp_len > 0:
                #print(f"[{tmp}]")
                pkt_len = tmp[0]
                if tmp_len > pkt_len:
                    data = tmp[:pkt_len+1]
                    yield data
                    tmp = tmp[pkt_len+1:]      

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
    com = Dumpcom(ser)
    com.listen_com()

    #main thread for tcp connections
    while (com.listen_com_is_running()):
        a = send_queue.get()
        if (a):
            if (a == 'null' or a == '{}'):
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:   
                sock.setblocking(False)
                sock.settimeout(TIMEOUT)
                try:
                    sock.connect(( host, 9090))
                    sock.sendall( a.encode() )
                except socket.error as err:
                    #print(f'{err}, msgs in queue: {send_queue.qsize()}')
                    print(err)