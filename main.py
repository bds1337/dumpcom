#!/usr/bin/env python3 
#coding: utf-8

import serial, json, socket, threading 
from time import sleep
import time

# tcp port
PORT = 9090
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


def send(jsn):
    if (jsn == 'null' or jsn == '{}'):
        return
    out = b''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(2)
        s.connect((HOST, PORT))
        s.sendall( jsn.encode())
        #while True:
        #out = s.recv(1024)
        #if (len(out)):
            #print(f"out: {out}")
    except socket.error as err:
        print(f'{err}')
    s.close

def parse(msg_p, alen):
    ret = {}
    #alen += 2
    try:
        print(f"alen_p {alen}")
        print(f"alen_p + {int(msg_p[2 + alen], 16)}")
        if (int(msg_p[2 + alen], 16) == T_PULSE):
            print(f"PULSE {msg_p}")
            ret['tag_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
            ret['pulse'] = int(msg_p[5 + alen], 16)
        elif (int(msg_p[2 + alen], 16) == T_PRESSURE):
            print(f"PRESSURE {msg_p}")
            ret['tag_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
            ret['pressure_up'] = int(msg_p[5 + alen], 16)
            ret['pressure_down'] = int(msg_p[6 + alen], 16)
        elif (int(msg_p[2 + alen], 16) == T_RSSI):
            ret['beacon_id'] = int(msg_p[3 + alen]+msg_p[4 + alen], 16)
            ret['rssi'] = int.from_bytes(bytes.fromhex(msg_p[5 + alen]), byteorder='little', signed=True) 
            ret['tag_id'] = int(msg_p[6 + alen]+msg_p[7 + alen], 16)
        return ret
    except IndexError:
        print("err")
        return

with serial.Serial(SERIALPORT, BAUDRATE, timeout=0) as ser:
    while (1):
        #sleep(DELAY)
        msg_p = []
        msglen = b''
        msg = []
        a = ""
        exec_start = time.time()
        while (ser.inWaiting() > 0):
            out = (ser.read(1)).hex()
            if (len(out) and not msglen):
                msglen = out
            msg.append(out)
        if (len(msg) > 3):
            ret = {}
            print(f"___{msg}")
            if (not int(msg[2], 16) == 0xBE or not int(msg[3], 16) == 0xAF):
                #continue
                for i in range(2, len(msg)-1):
                    if (int(msg[i], 16) == 0xBE and int(msg[i+1], 16) == 0xAF):
                        msg = msg[i-2:]
                        break
            msg_p = msg[0:int(msg[0], 16)+1]
            alen = 0
            blen = len(msg)
            #print(msg[alen])
            #print(msg)
            #print(f"blen {blen}")
            while True:
                #print(f"aa {alen}")
                if (alen >= blen):
                    break
                jsn = json.dumps(parse(msg,alen))
                a = jsn
                print(jsn) 
                alen = alen + int(msg[alen], 16) + 1
                send(jsn)
        exec_end = time.time()
        if (len(a) > 0):
            print(a)
            print(f"TOTAL PARSE TIME: {exec_end - exec_start}")
