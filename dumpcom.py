#!/usr/bin/env python3 
#coding: utf-8

import threading
import time
import queue
import socket
import sys

import serial
import serial.tools.list_ports as list_ports

import parser

HOST = '127.0.0.1' 
#HOST = '192.168.0.22' 
#HOST = '192.168.36.137' 
PORT = '/dev/ttyACM0'
TIMEOUT = 0.1

send_queue = queue.Queue()
send_queue.maxsize = 300

def greeter():
    print("Доступные устройства:")
    for port in list_ports.comports():
        print(f"\t{port.device}")

class Client(threading.Thread):
    def __init__(self): # **kwargs
        threading.Thread.__init__(self)
    
    def run(self):
        while(True):
            jsn = send_queue.get()
            if (jsn == 'null' or jsn == '{}'):
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:   
                sock.setblocking(False)
                sock.settimeout(TIMEOUT)
                try:
                    sock.connect(( HOST, 9090 ))
                    sock.sendall( jsn.encode() )
                    #print(jsn)
                    #print(f'msgs in queue: {send_queue.qsize()}')
                except socket.error as err:
                    print(err)
                    #print(f'{err}, msgs in queue: {send_queue.qsize()}')

class Uart(threading.Thread):
    def __init__(self, port=None, baudrate=None):
        threading.Thread.__init__(self)
        self.ser = None
        try:
            self.ser = serial.Serial(
                port = port,
                baudrate= 115200,
                rtscts=True
            )
        except serial.SerialException as e:
            if ( self.ser != None ):
                self.ser.close()
                self.ser = None
            raise

        self.die = False

    def stop(self):
        send_queue.put(None)
        if (self.ser):
            self.ser.close()
            self.ser = None

    def __del__(self):
        self.stop()

    """ uart thread """
    def run(self):
        self.ser.reset_input_buffer()
        for pkt in self._get_packet_from_uart():
            if len(pkt) < 2:
                print(f"Invalid pkt size: {pkt}")
                continue
            if (pkt[1] != 0x8A):
                print(f"Invalid pkt type: {pkt}")
                continue
            parsed_list = parser.parse( parser.make_lines(pkt) ) 
            #print(f"{parsed_list}")
            if (parsed_list is None):
                continue
            for dct in parsed_list:
                try:
                    send_queue.put_nowait( parser.make_json(dct) )
                except queue.Full:
                    continue

    def _get_packet_from_uart(self):
        tmp = bytearray([])
        while (True):
            try:
                tmp += bytearray(self.ser.read())
            except serial.serialutil.SerialException as e:
                print(f"lost connection with com-device: {e}")
                self.stop()
                break
            tmp_len = len(tmp)
            if tmp_len > 0:
                pkt_len = tmp[0]
                if tmp_len > pkt_len:
                    data = tmp[:pkt_len+1]
                    yield data
                    tmp = tmp[pkt_len+1:]

if __name__ == '__main__': 
    greeter()
    port = PORT
    if ( len(sys.argv) > 1 ):
        port = sys.argv[1]
    try:
        u = Uart(port)
        t = Client()
        u.setDaemon(True)
        t.setDaemon(True)
        u.start()
        t.start()
        """ Check both threads is alive """
        while (u.is_alive() and t.is_alive()):
            time.sleep(2)
    except Exception as e:
        print(f"error {e}")
        sys.exit()