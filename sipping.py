#!/usr/bin/env python
import re
import socket
import sys
from argparse import ArgumentParser
import time

class SipPing:
    def __init__(self, dest_addr, dest_port=5060, src_ip='', src_port=55220, udp=True, timeout=1):
        self.dest_addr = dest_addr
        self.dest_port = dest_port
        self.src_ip = src_ip
        self.src_port = src_port
        self.udp = udp
        self.timeout = timeout

        if (len(self.src_ip) > 0):
            sip_src_host = self.src_ip
        else:
            sip_src_host = "dummy.com"

        # set up sip options header
        self.sip_options = '''\
OPTIONS sip:{dest_addr}:{dest_port} SIP/2.0
Via: SIP/2.0/UDP {sip_src_host}:{src_port}
Max-Forwards: 70
From: "Test" <sip:test@{sip_src_host}>;tag=98765
To: <sip:dummy@{dest_addr}:{dest_port}>
Contact: <sip:dummy@{sip_src_host}:{src_port}>
Call-ID: 1234567@{sip_src_host}
CSeq: 1 OPTIONS
Accept: application/sdp
Content-Length: 0
'''.format(sip_src_host=sip_src_host, src_port=self.src_port, dest_addr=self.dest_addr, dest_port=self.dest_port)

        # check formatting
        #print('"' + self.sip_options + '"')


    def ping_once(self):
        # keep track of a timeout
        timeout = False

        # TCP
        if (not self.udp):
            # Create an IPv4 TCP socket.  Set REUSEADDR so that the port can be
            # reused without waiting for the TIME_WAIT state to pass.
            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP
            )
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else: # UDP
            # Create an IPv4 UDP socket.
            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
                socket.IPPROTO_UDP
            )

        # If no source address or source port is provided, the socket module
        # assigns this automatically.
        s.bind((self.src_ip, self.src_port))
        s.settimeout(self.timeout)

        # record the start time for latency metrics
        startTime = int(round(time.time() * 1000))

        # connect and send response
        try:
            s.connect((self.dest_addr, self.dest_port))
            s.send(str.encode(self.sip_options))
            response = s.recv(65535)

        except socket.timeout:
            timeout = True

        finally:
            endTime = int(round(time.time() * 1000))
            try:
                # Regardless of what happened, try to gracefully close down the
                # socket.
                s.shutdown(1)
                s.close()
            except UnboundLocalError:
                # Socket has not been assigned.
                pass

        # -1 means timeout
        if (timeout):
            return -1

        return (endTime - startTime)

    # do many pings one after another
    def ping(self, count):
        results = []

        for x in range(5):
            # ping once
            results.append(self.ping_once())

        return results

#sipping = SipPing("10.1.2.3", 5060)

#print(sipping.ping_once())
#print(sipping.ping(3))
