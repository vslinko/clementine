#!/usr/bin/python

import threading
import time
import csv
import re
import operator
import os
import sys
import tailer
import termcolor


class LoopThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False

    def stop(self):
        self.kill_received = True


class Reader(LoopThread):
    def __init__(self):
        LoopThread.__init__(self)
        self.url_re = re.compile(r"\d+")
        self.collectors = []

    def run(self):
        for line in csv.reader(tailer.follow(open("/var/log/nginx/paragraph.log")), delimiter=' '):
            if self.kill_received:
                break

            for collector in self.collectors:
                collector.add(self.parse(line))

    def parse(self, line):
        return {
            "connection": int(line[0]),
            "msec": float(line[1]),
            "request_time": float(line[2]),
            "remote_addr": line[3],
            "request_method": line[4],
            "url": self.url_re.sub("{x}", line[5]),
            "status": int(line[6]),
            "request_length": int(line[7]) if line[7] != '-' else None,
            "bytes_sent": int(line[8])
        }


class Printer(LoopThread):
    def __init__(self):
        LoopThread.__init__(self)
        self.collectors = []

    def run(self):
        while not self.kill_received:
            os.system("clear")
            for collector in self.collectors:
                sys.stdout.write(str(collector))
            time.sleep(1.0)


class Collector(LoopThread):
    NAME = "Collector"

    def __init__(self, limit=10):
        LoopThread.__init__(self)
        self.top = {}
        self.sorted_top = []
        self.limit = limit

    def add(self, line):
        key = self.make_key(line)

        if not key:
            return

        if key in self.top:
            self.top[key] += 1
        else:
            self.top[key] = 1

    def make_key(self, line):
        return False

    def run(self):
        count = 0
        while not self.kill_received:
            count += 1
            self.sorted_top = sorted(self.top.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.limit]
            time.sleep(1.0)
            if count == 300: # 5 minutes
                self.top = {}
                count = 0

    def format(self, key, count):
        return str((key, count))

    def __str__(self):
        string = termcolor.colored("{0:80}".format(self.NAME), 'cyan', 'on_magenta', attrs=['bold'])
        string += "\n"
        lines = 0
        for key, count in self.sorted_top:
            string += self.format(key, count)
            string += "\n"
            lines += 1
        for i in range(self.limit - lines):
            string += "\n"
        return string


class SplitCollector():
    def __init__(self, first_collector, second_collector, limit=10):
        self.first_collector = first_collector
        self.second_collector = second_collector
        self.first_collector.limit = limit
        self.second_collector.limit = limit
        self.limit = limit

    def add(self, line):
        self.first_collector.add(line)
        self.second_collector.add(line)

    def start(self):
        self.first_collector.start()
        self.second_collector.start()

    def stop(self):
        self.first_collector.stop()
        self.second_collector.stop()

    def __str__(self):
        string = termcolor.colored("{0:45}{1:35}".format(self.first_collector.NAME, self.second_collector.NAME), 'cyan', 'on_magenta', attrs=['bold'])
        string += "\n"
        for i in range(self.limit):
            if self.first_collector.sorted_top:
                first_line = self.first_collector.format(*self.first_collector.sorted_top.pop(0))
            else:
                first_line = ""
            if self.second_collector.sorted_top:
                second_line = self.second_collector.format(*self.second_collector.sorted_top.pop(0))
            else:
                second_line = ""

            string += "{0:35}          {1:35}".format(first_line[:40], second_line[:40])
            string += "\n"
        return string


class TopQueriesByIPAddress(Collector):
    NAME = "TOP QUERIES BY IP ADDRESS"

    def make_key(self, line):
        if line['remote_addr'] == "83.229.185.11":
            return False

        return (line['remote_addr'], line['url'])

    def format(self, key, count):
        return "{0:16}{1:58}{2:6}".format(key[0], key[1][:58], count)


class TopQueries(Collector):
    NAME = "TOP QUERIES"

    def make_key(self, line):
        return line['url']

    def format(self, key, count):
        return "{0:74}{1:6}".format(key[:74], count)


class TopIPAddresses(Collector):
    NAME = "TOP IP ADDRESSES"

    def make_key(self, line):
        return line['remote_addr']

    def format(self, key, count):
        return "{0:25}{1:10}".format(key, count)


class TopStatuses(Collector):
    NAME = "TOP STATUSES"

    def make_key(self, line):
        return line['status']

    def format(self, key, count):
        return "{0:20}{1:15}".format(str(key), count)


def main():
    collectors = [TopQueriesByIPAddress(8), TopQueries(8), SplitCollector(TopIPAddresses(), TopStatuses(), 4)]

    reader = Reader()
    reader.collectors = collectors
    reader.start()

    for collector in collectors:
        collector.start()

    printer = Printer()
    printer.collectors = collectors
    printer.start()

    while True:
        try:
            time.sleep(0.01)
        except:
            reader.stop()
            printer.stop()
            for collector in collectors:
                collector.stop()
            break


if __name__ == "__main__":
    main()
