#!/usr/bin/env python3 
#coding: utf-8

import serial, json, socket, threading 
from time import sleep

# tcp port
PORT = 9090
#HOST = '127.0.0.1' 
HOST = '192.168.36.137' 

# serial/com
SERIALPORT = '/dev/ttyACM0'
BAUDRATE = 115200
DELAY = 0.5

# defines
T_PULSE = 1
T_PRESSURE = 2
T_RSSI = 3


def send(jsn):
    out = b''
    print(jsn)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(1)
    try:
        s.sendall( jsn.encode())
        #while True:
        #out = s.recv(1024)
        #if (len(out)):
            #print(f"out: {out}")

    except socket.error:
        print('connection error')
    s.close

def parse(msg_p, alen):
    ret = {}
    print(f"alen_p {alen}")
    if (int(msg_p[2 + alen]) == T_PULSE):
        ret['tag_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
        ret['pulse'] = int(msg_p[5 + alen], 16)
    elif (int(msg_p[2 + alen]) == T_PRESSURE):
        ret['tag_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
        ret['pressure_up'] = int(msg_p[5 + alen], 16)
        ret['pressure_down'] = int(msg_p[6 + alen], 16)
    elif (int(msg_p[2 + alen]) == T_RSSI):
        ret['beacon_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
        ret['rssi'] = int.from_bytes(bytes.fromhex(msg_p[5 + alen]), byteorder='little', signed=True) 
        #ret['rssi'] = int(msg_p[5], 16) 
        ret['tag_id'] = int(msg_p[6 + alen]+msg_p[7 + alen], 16)
    return ret

while True:
    with open('json.json', "r") as f:
        for line in f:
            send(line)
            sleep(1)

