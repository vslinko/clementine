import re
import csv
import tailer
import time
import random
from paragraph.thread import LoopThread


__all__ = ['Reader', 'FakeReader']


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


class FakeReader(Reader):
    IPS = ["{0}.{1}.{2}.{3}".format(random.randint(1, 255), random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)) for i in range(50)]
    URIS = ["/" + "".join([random.choice('qwertyuiopasdfghjklzxcvbnm') for i in range(0, random.randint(1, 100))]) for i in range(50)]

    def __init__(self):
        Reader.__init__(self)
        self.connection = random.randint(10000, 100000)

    def run(self):
        while not self.kill_received:
            time.sleep(0.01)

            for collector in self.collectors:
                collector.add(self.random())

    def random(self):
        self.connection += 1
        line = {
            "connection": self.connection,
            "msec": random.random() * random.randint(0, 10),
            "request_time": time.time(),
            "remote_addr": self.IPS[random.randint(0, 49)],
            "request_method": ["GET", "POST"][random.randint(0, 1)],
            "scheme": "http",
            "host": "pegast.ru",
            "request_uri": self.URIS[random.randint(0, 49)],
            "status": [200, 201, 203, 300, 301, 302, 400, 401, 402, 500, 501, 502][random.randint(0, 11)],
            "request_length": random.randint(100, 10000),
            "bytes_sent": random.randint(100, 100000)
        }
        line["url"] = "{0}://{1}{2}".format(line["scheme"], line["host"], line["request_uri"])
        return line
