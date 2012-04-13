#!/usr/bin/python

import threading
import time
import csv
import re
import operator
import os
import sys
import BaseHTTPServer
import json
import tailer
import termcolor


def title(string):
    return termcolor.colored("{0:80}".format(string), 'cyan', 'on_magenta', attrs=['bold'])


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
        for line in csv.reader(tailer.follow(open("/var/log/nginx/access.log")), delimiter=' '):
            if self.kill_received:
                break

            parsed_line = self.parse(line)

            if not parsed_line or parsed_line["request_uri"] == "-" or parsed_line["url"] == "http://agency.pegast.ru/block.php":
                continue

            for collector in self.collectors:
                collector.add(parsed_line)

    def parse(self, line):
        if len(line) != 11:
            return False

        return {
            "connection": int(line[0]),
            "msec": float(line[1]),
            "request_time": float(line[2]),
            "remote_addr": line[3],
            "request_method": line[4],
            "scheme": line[5],
            "host": line[6],
            "request_uri": line[7],
            "status": int(line[8]),
            "request_length": int(line[9]) if line[9] != '-' else None,
            "bytes_sent": int(line[10]),
            "url": self.url_re.sub("{x}", "{0}://{1}{2}".format(line[5], line[6], line[7]))
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


class Cleaner(LoopThread):
    def __init__(self):
        LoopThread.__init__(self)
        self.collectors = []

    def run(self):
        count = 0
        while not self.kill_received:
            time.sleep(1.0)
            count += 1
            if count == 300: # 5 minutes
                for collector in self.collectors:
                    collector.clear()
                count = 0


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.collectors = []
        self.httpd = BaseHTTPServer.HTTPServer(('', 8080), ServerHandler)
        self.httpd.timeout = 1.0

    def run(self):
        self.httpd.thread = self
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()


class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        res = []
        for collector in self.server.thread.collectors:
            if isinstance(collector, SplitCollector):
                res.append(collector.first_collector.dump())
                res.append(collector.second_collector.dump())
            else:
                res.append(collector.dump())
        self.wfile.write(json.dumps(res, indent=4))

    def log_message(self, format, *args):
        pass


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

    def sort(self):
        self.sorted_top = sorted(self.top.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.limit]

    def run(self):
        while not self.kill_received:
            self.sort()
            time.sleep(1.0)

    def format(self, key, count):
        return str((key, count))

    def clear(self):
        self.top = {}

    def dump(self):
        return {"name": self.NAME, "data": self.sorted_top}

    def __str__(self):
        string = title(self.NAME)
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

    def clear(self):
        self.first_collector.clear()
        self.second_collector.clear()

    def __str__(self):
        string = title("{0:45}{1:35}".format(self.first_collector.NAME, self.second_collector.NAME))
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
        if line["remote_addr"] == "83.229.185.11" or line["remote_addr"] == "83.229.211.229":
            return False

        return (line['remote_addr'], line['url'])

    def format(self, key, count):
        return "{0:16}{1:58}{2:6}".format(key[0], key[1][:58], count)


class SuspiciousIP(TopQueriesByIPAddress):
    NAME = "SUSPICIOUS IP"

    def sort(self):
        suspicious = [x for x in self.top.iteritems() if "samo" in x[0][1] and "andromeda" not in x[0][1] and x[1] > 10]
        self.sorted_top = sorted(suspicious, key=operator.itemgetter(1), reverse=True)[:self.limit]

    def format(self, key, count):
        string = TopQueriesByIPAddress.format(self, key, count)
        if count > 100:
            string = termcolor.colored(string, 'red')
        return string


class TopQueries(Collector):
    NAME = "TOP QUERIES"

    def make_key(self, line):
        return line['url']

    def format(self, key, count):
        return "{0:74}{1:6}".format(key[:74], count)


class TopIPAddresses(Collector):
    NAME = "TOP IP ADDRESSES"

    def dump(self):
        self.sort() # why?!
        return Collector.dump(self)

    def make_key(self, line):
        return line['remote_addr']

    def format(self, key, count):
        return "{0:25}{1:10}".format(key, count)


class TopStatuses(Collector):
    NAME = "TOP STATUSES"

    def dump(self):
        self.sort() # why?!
        return Collector.dump(self)

    def make_key(self, line):
        return line['status']

    def format(self, key, count):
        return "{0:20}{1:15}".format(str(key), count)


class FakeCollector():
    NAME = "FAKE COLLECTOR"

    def add(self, line):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def clear(self):
        pass

    def dump(self):
        pass

    def __str__(self):
        return ""


class LastConnectionNumber(FakeCollector):
    NAME = "LAST CONNECTION NUMBER"

    def __init__(self):
        self.last = 0

    def add(self, line):
        self.last = line['connection']
        self.NAME = "{0:25}{1:10}".format("LAST CONNECTION NUMBER", self.last)

    def dump(self):
        return {"name": "LAST CONNECTION NUMBER", "data": self.last}


class MegabytesSent(FakeCollector):
    NAME = "MEGABYTES SENT"

    def __init__(self):
        self.sent = 0

    def add(self, line):
        self.sent += line['bytes_sent']
        self.NAME = "{0:25}{1:10}".format("MEGABYTES SENT", self.sent / 1024 / 1024)

    def dump(self):
        return {"name": "BYTES SENT", "data": self.sent}

    def clear(self):
        self.sent = 0


def main():
    collectors = [
        TopQueriesByIPAddress(7),
        #TopQueries(7),
        SuspiciousIP(7),
        SplitCollector(TopIPAddresses(), TopStatuses(), 5),
        SplitCollector(LastConnectionNumber(), MegabytesSent(), 0)
    ]

    reader = Reader()
    reader.collectors = collectors
    reader.start()

    for collector in collectors:
        collector.start()

    printer = Printer()
    printer.collectors = collectors
    printer.start()

    cleaner = Cleaner()
    cleaner.collectors = collectors
    cleaner.start()

    server = Server()
    server.collectors = collectors
    server.start()

    while True:
        try:
            time.sleep(0.1)
        except:
            server.stop()
            printer.stop()
            reader.stop()
            cleaner.stop()
            for collector in collectors:
                collector.stop()
            break


if __name__ == "__main__":
    main()
