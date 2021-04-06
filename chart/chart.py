#!/usr/bin/env python3
# coding: utf-8


import matplotlib.pyplot as plt
import matplotlib.lines as lines

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
        if len(self.lst) == self._maxsize:
            self.lst.pop(0)
        self.lst.append(element)
        return self.lst

    def get(self):
        return self.lst


# for testing only
def multi_line(lines: int):
    ret = []
    with open(f"{beacon}-plot.txt", 'r') as f:
        for i in range(lines):
            ret.append(next(f).strip().split(":"))
        return ret


def last_line():
    with open(f"{beacon}-plot.txt", 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        return f.readline().decode()[:-1].split(":")


if __name__ == "__main__":
    d = {37: SizedList(XSIZE), 38: SizedList(XSIZE), 39: SizedList(XSIZE)}
    beacon = 2
    if len(sys.argv) > 1:
        beacon = sys.argv[1]
    # КОЛ-ВО ЭЛЕМЕНТОВ НА ГРАФИКЕ
    lst = SizedList(XSIZE)

    #m = multi_line(3)
    #sys.exit()

    plt.ion()
    new_counter = 0
    old_counter = 0
    while True:
        line = last_line()
        #for line in multi_line(3):
        new_counter = int(line[3])
        if old_counter != new_counter:
            #print(f"[{old_counter}] != [{new_counter}]")
            old_counter = new_counter
            d[int(line[1])].push(int(line[2]))
            print(f"{int(line[1])} added: {d[int(line[1])].get()}")
        plt.title(f'{beacon} beacon')
        plt.xlim(0, XSIZE)
        plt.ylim(-100, -10)
        #print(d[37].get())
        plt.plot(d[37].get(), color='green')
        plt.plot(d[38].get(), color='red')
        plt.plot(d[39].get(), color='blue')
        plt.pause(0.1)
        plt.show()
