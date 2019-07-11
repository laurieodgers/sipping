#!/usr/local/bin/python3
import argparse
import sys
import os
import time
import signal
from sipping import SipPing

#######################################
appName = "sipping_cli"
version = "0.1.0"
#######################################
# get the filename and directory of this app
appFilename = os.path.basename(__file__)
appDirectory = os.path.dirname(os.path.realpath(__file__))

# get an argparser object
argParser = argparse.ArgumentParser(
    description='''SIP OPTIONS Ping on command line''',
    epilog="Example:\n  " + appFilename + " -l warning",
    formatter_class=argparse.RawDescriptionHelpFormatter
)

argParser.add_argument('-c', '--count', help='The number of pings to send', type=int, default=3)
argParser.add_argument('-p', '--dst_port', help='The destination port to send the pings to', type=int, default=5060)
argParser.add_argument('-i', '--interval', help='Interval between pings', type=float, default=1)
argParser.add_argument('-t', '--timeout', help='Ping timeout', type=float, default=3)
argParser.add_argument('dst_ip', type=str, help='Destination ip address to ping')
# parse args
args = argParser.parse_args()

#######################################

def handle_sigint(sig, frame):
    print()
    show_stats()
    sys.exit(0)

def show_stats():
    end_time = time.time()
    num_received = 0
    num_timed_out = 0

    total_latency = 0
    min_latency = (args.timeout * 1000) + 1
    max_latency = 0

    for result in results:
        if (result is None):
            num_timed_out = num_timed_out + 1
        else:
            num_received = num_received + 1
            total_latency = total_latency + result

            if (result < min_latency):
                min_latency = result

            if (result > max_latency):
                max_latency = result

    packetloss_percentage = (num_timed_out / len(results)) * 100

    if (num_received > 0):
        # calculate the avg latency
        avg_latency = total_latency / num_received

    time_result = round((end_time - start_time) * 1000, 3)

    print("--- " + args.dst_ip + " ping statistics ---")
    print(str(len(results)) + " packets transmitted, " + str(num_received) + " packets received, " + str(packetloss_percentage) + "% packet loss")

    if (num_received > 0):
        print("round-trip min/avg/max = " + str(round(min_latency*1000,3)) + '/' + str(round(avg_latency*1000,3)) + '/' + str(round(max_latency*1000,3)) + ' ms')


sipping = SipPing(args.dst_ip, args.dst_port)

results = []

print("SIP OPTIONS " + args.dst_ip)

start_time = time.time()

# catch ctrl-c
signal.signal(signal.SIGINT, handle_sigint)

while (True):
    result = sipping.ping_once()
    results.append(result)

    if (result is None):
        print("Request timed out")
    else:
        print('Reply from ' + args.dst_ip + ': time=' + str(round(result*1000, 3)) + ' ms')

    if (len(results) == args.count):
        show_stats()
        sys.exit(0)
    else:
        time.sleep(args.interval)
