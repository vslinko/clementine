import re
import csv
import tailer
import time
from random import randint, choice, random
from paragraph.thread import LoopThread


__all__ = ["Parser", "FakeParser"]


class Parser(LoopThread):
    def __init__(self, reports):
        LoopThread.__init__(self)

        self.reports = reports
        self.url_re = re.compile(r"\d+")

    def run(self):
        for line in csv.reader(tailer.follow(open("/var/log/nginx/access.log")), delimiter=" "):
            if self.kill_received:
                break

            record = self.parse(line)

            if not record or record["request_uri"] == "-" or record["url"] == "http://agency.pegast.ru/block.php":
                continue

            for report in self.reports:
                report.add(record)

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
            "request_length": int(line[9]) if line[9] != "-" else None,
            "bytes_sent": int(line[10]),
            "url": self.url_re.sub("{x}", "{0}://{1}{2}".format(line[5], line[6], line[7]))
        }


class FakeParser(Parser):
    IPS = ["{0}.{1}.{2}.{3}".format(randint(1, 255), randint(1, 255), randint(1, 255), randint(1, 255))
           for i in range(50)]

    URIS = ["/" + "".join([choice("qwertyuiopasdfghjklzxcvbnm") for x in range(0, randint(1, 100))])
            for i in range(50)]

    def __init__(self, reports):
        Parser.__init__(self, reports)

        self.connection = randint(10000, 100000)

    def run(self):
        while not self.kill_received:
            time.sleep(0.01)

            for report in self.reports:
                report.add(self.random_record())

    def random_record(self):
        self.connection += 1
        record = {
            "connection": self.connection,
            "msec": random() * randint(0, 10),
            "request_time": time.time(),
            "remote_addr": choice(self.IPS),
            "request_method": choice(["GET", "POST"]),
            "scheme": "http",
            "host": "pegast.ru",
            "request_uri": choice(self.URIS),
            "status": choice([200, 201, 203, 300, 301, 302, 400, 401, 402, 500, 501, 502]),
            "request_length": randint(100, 10000),
            "bytes_sent": randint(100, 100000)
        }
        record["url"] = "{0}://{1}{2}".format(record["scheme"], record["host"], record["request_uri"])
        return record
