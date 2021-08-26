#!/usr/bin/env python3 
# coding: utf-8

import threading
import time
import queue
import socket
import sys
import os
import serial
import serial.tools.list_ports as list_ports

import datetime
import csv

import msg_parser


# HOST = '127.0.0.1'
HOST = '192.168.36.137'
PORT = '/dev/ttyACM0'
TIMEOUT = 0.5

send_queue = queue.Queue()
send_queue.maxsize = 100

def csv_smartband_parse(msg):
    now = datetime.datetime.now()
    with open(f"tracker/{msg['tag_id']}.csv", "a", newline="") as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow([now.strftime('%d.%m.%Y %H:%M:%S') 
                        , msg['pulse']
                        , msg['pressure_up']
                        , msg['pressure_down']])


def find_server():
    for port in list_ports.comports():
        if os.name == "nt":
            return port[0]
        else:
            if port[1].startswith("J-Link"):
                return port[0]
    return None


class Client(threading.Thread):
    def __init__(self, host):  # **kwargs
        threading.Thread.__init__(self)
        self.host = host
        self.is_running = True

    def stop(self):
        self.is_running = False
        send_queue.put(None)

    def __del__(self):
        self.stop()

    def run(self):
        while self.is_running:
            jsn = send_queue.get()
            if jsn is None or jsn == 'null' or jsn == '{}':
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setblocking(False)
                sock.settimeout(TIMEOUT)
                try:
                    sock.connect((self.host, 9090))
                    sock.sendall(jsn.encode())
                    # print(f'{jsn} queue: {send_queue.qsize()}')
                except socket.error as err:
                    # print(err)
                    # print(f'{err}, msgs in queue: {send_queue.qsize()}')
                    continue


class Uart(threading.Thread):
    def __init__(self, port=None):
        threading.Thread.__init__(self)
        self.ser = None
        self.is_running = True
        self.tidmap = {}
        self.write_counter = 0
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=115200,
                rtscts=True
            )
        except serial.SerialException:
            if self.ser:
                self.ser.close()
                self.ser = None
            raise

    def stop(self):
        send_queue.put(None)
        self.is_running = False
        if self.ser:
            self.ser.close()
            self.ser = None

    def write_log(self, parsed, channel):
        try:
            with open(f"chart/{parsed['beacon_id']}-plot.txt", "a") as f:
                f.write(f"{parsed['beacon_id']}:{channel}:{parsed['rssi']}:{self.write_counter}\n")
                self.write_counter += 1
        except KeyError:
            pass

    def __del__(self):
        self.stop()

    """ uart thread """

    def run(self):
        ch = 37
        self.ser.reset_input_buffer()
        for pkt in self._get_packet_from_uart():
            if len(pkt) < 2:
                print(f"Invalid pkt size: {pkt}")
                continue
            if pkt[1] != 0x8A:
                print(f"Invalid pkt type: {len(list(pkt))} {list(pkt)}")
                continue
            parsed, ch = msg_parser.parse(pkt, self.tidmap)
            if not parsed:
                continue
            try:
                send_queue.put_nowait(msg_parser.make_json(parsed))
            except queue.Full:
                continue
            if ch:
                print(f"{parsed}, ch: {ch}, tid: {self.tidmap[parsed['beacon_id']]}, queue: {send_queue.qsize()}")
            else:
                print(f"{parsed}, queue: {send_queue.qsize()}")
            # try:
            #     if parsed['pulse']:
            #         csv_smartband_parse(parsed)
            # except KeyError:
            #     continue

    def _get_packet_from_uart(self):
        tmp = bytearray([])
        while self.is_running:
            try:
                tmp += bytearray(self.ser.read())
            except serial.serialutil.SerialException as e:
                print(f"lost connection with a device: {e}")
                self.stop()
                # break
            tmp_len = len(tmp)
            if tmp_len > 0:
                pkt_len = tmp[0]
                if tmp_len > pkt_len:
                    data = tmp[:pkt_len + 1]
                    yield data
                    tmp = tmp[pkt_len + 1:]

if __name__ == '__main__':
    port = find_server()
    host = HOST
    if len(sys.argv) > 1:
        port = sys.argv[1]
        if len(sys.argv) > 2:
            host = sys.argv[2]
    print("Searching for device...")
    t = None
    u = None
    while True:
        if port:
            try:
                u = Uart(port)
                t = Client(host)
                u.setDaemon(True)
                t.setDaemon(True)
                u.start()
                t.start()
                print(f"Configured. Serial port: {port}, server: {host}\n")
                """ Check both threads is alive """
                while u.is_alive() and t.is_alive():
                    time.sleep(2)
            except KeyboardInterrupt:
                sys.exit()
            except serial.serialutil.SerialException:
                print(f"Disconnected from {port}\nSearching for device...")
                port = None
                if t:
                    t.stop()
                    t.join()
                if u:
                    u.stop()
                    u.join()
                continue
        port = find_server()
        time.sleep(2)
