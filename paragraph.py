#!/usr/bin/python

import csv
import os
import tailer
import re
import operator
import threading
import time


class Printer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False

    def run(self):
        global sorted_top
        while not self.kill_received:
            os.system("clear")
            for line in sorted_top:
                print "{0:20}{1:50}{2:10}".format(line[0][0], line[0][1][:50], line[1])
            time.sleep(1.0)


class Reader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False

    def run(self):
        global top
        url_re = re.compile(r"\d+")
        for line in csv.reader(tailer.follow(open("/var/log/nginx/paragraph.log")), delimiter=' '):
            if self.kill_received:
                break

            connection = int(line[0])
            msec = float(line[1])
            request_time = float(line[2])
            remote_addr = line[3]
            request_method = line[4]
            url = url_re.sub("{x}", line[5])
            status = int(line[6])
            request_length = int(line[7]) if line[7] != '-' else None
            bytes_sent = int(line[8])

            key = (remote_addr, url)
            if key in top:
                top[key] += 1
            else:
                top[key] = 1


class Sorter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False

    def run(self):
        global top, sorted_top
        count = 0
        while not self.kill_received:
            count += 1
            time.sleep(1.0)
            sorted_top = sorted(top.iteritems(), key=operator.itemgetter(1), reverse=True)[:24]
            if count == 300: # 5 minutes
                top = {}
                count = 0

top = {}
sorted_top = []

reader = Reader()
reader.start()

printer = Printer()
printer.start()

sorter = Sorter()
sorter.start()

while True:
    try:
        time.sleep(1.0)
    except:
        reader.kill_received = True
        printer.kill_received = True
        sorter.kill_received = True
        break
