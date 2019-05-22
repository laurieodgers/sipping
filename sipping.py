#!/usr/bin/env python
import re
import socket
import sys
import time
import random

class SipPing:
    def __init__(self, dest_addr, dest_port=5060, src_ip='', src_port=None, udp=True, timeout=1):
        self.dest_addr = dest_addr
        self.dest_port = dest_port
        self.src_ip = src_ip
        self.udp = udp
        self.timeout = timeout

        # generate a random port if src_port is None
        if (src_port is None):
            # randomly generate a port betewen 1024 and 65535
            self.src_port = random.randint(1024, 65535)
        else:
            self.src_port = src_port

        # set something that the sip options header can use as a src
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

    # run a single ping with the options received in the constructor
    # returns seconds as float
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
        startTime = time.time()

        # connect and send response
        try:
            s.connect((self.dest_addr, self.dest_port))
            s.send(str.encode(self.sip_options))
            response = s.recv(65535)

        except socket.timeout:
            timeout = True

        finally:
            endTime = time.time()

            try:
                # Regardless of what happened, try to gracefully close down the
                # socket.
                s.shutdown(1)
                s.close()
            except UnboundLocalError:
                # Socket has not been assigned.
                pass

        # None means timeout
        if (timeout):
            return None

        return (endTime - startTime)

    # do many pings one after another
    # returns list of seconds as list of float
    def ping(self, count, delay=0):
        results = []

        for x in range(count):
            # ping once
            results.append(self.ping_once())

            # delay before next loop if we havent reached the end of the loop
            if (x < (count-1)):
                time.sleep(delay)

        return results

# examples
#sipping = SipPing("10.1.2.3", 5060)

# just 1 ping
#print(sipping.ping_once())

# many pings with time between
#print(sipping.ping(3, 1))
