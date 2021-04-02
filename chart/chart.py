#!/usr/bin/env python3
#coding: utf-8

import matplotlib.pyplot as plt
import matplotlib.lines as lines
import numpy as np

import random
import sys, os

XSIZE = 100

plt.style.use('ggplot')

class SizedList:
    def __init__(self, size):
        self._maxsize = size
        self.lst = []
    
    def maxsize(self):
        return self._maxsize

    def push(self, element):
        if (len(self.lst) == self._maxsize):
            self.lst.pop(0)
        self.lst.append(element)

    def getlist(self):
        return self.lst

if __name__ == "__main__":
    beacon = 2
    rssi = 0
    new_counter = 0
    old_counter = 0
    if ( len(sys.argv) > 1 ):
        beacon = sys.argv[1]
    # КОЛ-ВО ЭЛЕМЕНТОВ НА ГРАФИКЕ
    lst = SizedList(XSIZE)
    plt.ion()
    while(True):
        with open(f"{beacon}-plot.txt", 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        #lst.push(random.randrange(10))
        rssi = int(last_line[2:6])
        new_counter = int(last_line[7:-1])
        if (old_counter != new_counter):
            print(f"[{old_counter}] != [{new_counter}]")
            old_counter = new_counter
            lst.push(rssi)
        plt.title(f'{beacon} beacon')
        plt.xlim(0, XSIZE)
        plt.ylim(-100, -10)
        plt.plot(lst.getlist(), 'o-',color='green', scaley=True)
        plt.pause(0.1)
        plt.clf()
    plt.show()