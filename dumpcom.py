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

#HOST = '127.0.0.1' 
#HOST = '192.168.0.22' 
HOST = '192.168.36.137' 
PORT = '/dev/ttyACM0'
TIMEOUT = 0.5

send_queue = queue.Queue()
send_queue.maxsize = 300

def find_server():
    for port in list_ports.comports():
        if port[1].startswith("J-Link"):
            return port[0]
    return None
   
class Client(threading.Thread):
    def __init__(self, host): # **kwargs
        threading.Thread.__init__(self)
        self.host = host
        self.is_running = True

    def stop(self):
        self.is_running = False
        send_queue.put(None)

    def __del__(self):
        self.stop()

    def run(self):
        while(self.is_running):
            #print("client")
            #continue
            jsn = send_queue.get()
            if (jsn == None or jsn == 'null' or jsn == '{}'):
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:   
                sock.setblocking(False)
                sock.settimeout(TIMEOUT)
                try:
                    sock.connect(( self.host, 9090 ))
                    sock.sendall( jsn.encode() )
                    #print(jsn)
                    #print(f'{jsn} queue: {send_queue.qsize()}')
                except socket.error as err:
                    print(err)
                    #print(f'{err}, msgs in queue: {send_queue.qsize()}')

class Uart(threading.Thread):
    def __init__(self, port=None, baudrate=None):
        threading.Thread.__init__(self)
        self.ser = None
        self.tidmap = {}
        try:
            self.ser = serial.Serial(
                port = port,
                baudrate= 115200,
                rtscts=True
            )
        except serial.SerialException:
            if ( self.ser != None ):
                self.ser.close()
                self.ser = None
            raise

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
            #print(pkt)
            parsed = parser.parse_bytes(pkt, self.tidmap)
            '''
            parsed_list = parser.parse( parser.make_lines(pkt) ) 
            #print(f"{parsed_list}")
            if (parsed_list is None):
                continue
            '''
            if (not parsed):
                continue
            try:
                print(f"{parsed}, tid: {self.tidmap}")
                send_queue.put_nowait( parser.make_json(parsed) )
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
    port = find_server()
    host = HOST
    if ( len(sys.argv) > 1 ):
        port = sys.argv[1]
        if ( len(sys.argv) > 2 ):
            host = sys.argv[2]
    print("Searching for device...")
    while (True):
        if (not port):
            time.sleep(2)
            port = find_server()
            continue
        try:
            u = Uart(port)
            t = Client(host)
            u.setDaemon(True)
            t.setDaemon(True)
            u.start()
            t.start()
            print(f"Configured. Serial port: {port}, server: {host}\n")
            """ Check both threads is alive """
            while (u.is_alive() and t.is_alive()):
                time.sleep(2)
        except KeyboardInterrupt:
            sys.exit()
        except serial.serialutil.SerialException:
            print(f"Disconnected from {port}\nSearching for device...")
            port = None
            t.stop()
            u.stop()
            t.join()
            u.join()
            continue