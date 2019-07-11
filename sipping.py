#!/usr/bin/env python
import re
import socket
import sys
import time
import random
import secrets

class SipPing:
    def __init__(self, dest_addr, dest_port=5060, src_ip='', src_port=None, udp=True, timeout=1):
        self.version = '0.1.0'
        self.dest_addr = dest_addr
        self.dest_port = dest_port
        self.src_ip = src_ip

        self.udp = udp
        self.timeout = timeout

        if (src_port is None):
            # randomly generate a port betewen 1024 and 65535
            self.src_port = random.randint(1024, 65535)
        else:
            self.src_port = src_port

        if (len(self.src_ip) > 0):
            sip_src_host = self.src_ip
        else:
            sip_src_host = "dummy.com"

        self.from_tag = secrets.token_hex(4)
        self.call_id = random.randint(1000000000,9999999999)

        # set up sip options header
        self.sip_options = '''\
OPTIONS sip:nobody@{dest_addr}:{dest_port} SIP/2.0
Via: SIP/2.0/UDP {sip_src_host}:{src_port};branch={{branch}};rport;alias
From: sip:sipping@{sip_src_host}:{src_port};tag={from_tag}
To: sip:nobody@{dest_addr}:{dest_port}
Call-ID: {call_id}@{sip_src_host}
CSeq: 1 OPTIONS
Contact: sip:sipping@{sip_src_host}:{src_port}
Content-Length: 0
Max-Forwards: 70
User-Agent: sipping {version}
Accept: text/plain

'''.format(
    sip_src_host=sip_src_host,
    src_port=self.src_port,
    dest_addr=self.dest_addr,
    dest_port=self.dest_port,
    from_tag=self.from_tag,
    call_id=self.call_id,
    version=self.version
)

        # check formatting
        #print('"' + self.sip_options + '"')

    def ping_once(self):
        # keep track of a timeout
        timeout = False

        # update the branch in sip options header as it needs to be unique
        # for each request. note that z9hG4bK indicates that this branch is
        # created in accordance with RFC 3261
        branch = 'z9hG4bK.' + secrets.token_hex(4)
        sip_options = self.sip_options.format(branch=branch)
        #print(sip_options)

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
            s.send(str.encode(sip_options))
            response = s.recv(65535)

        except socket.timeout:
            #print('timeout: ' + self.dest_addr + ':' + str(self.dest_port))
            timeout = True

        finally:
            # calculate how long this took
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
    def ping(self, count, delay=0):
        results = []

        for x in range(count):
            # ping once
            results.append(self.ping_once())

            if (x < (count-1)):
                time.sleep(delay)

        return results


#sipping = SipPing("10.1.2.3", 5060)

# just 1 ping
#print(sipping.ping_once())

# many pings with time between
#print(sipping.ping(3, 1))
