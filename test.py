#!/usr/bin/env python3 
#coding: utf-8

import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        #print(f"{self.client_address[0]} wrote: \n{self.data}")
        print(self.data)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9090 

    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()
