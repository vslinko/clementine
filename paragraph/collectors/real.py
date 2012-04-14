import operator
import curses
from paragraph.collectors.base import *


__all__ = ['TopQueriesByIPAddress', 'SuspiciousIP', 'TopQueries', 'TopIPAddresses', 'TopStatuses',
           'LastConnectionNumber', 'MegabytesSent']


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
        self.sorted_top = sorted(suspicious, key=operator.itemgetter(1), reverse=True)[:self.LIMIT]

    def format(self, key, count):
        string = TopQueriesByIPAddress.format(self, key, count)
        return string


class TopQueries(Collector):
    NAME = "TOP QUERIES"

    def make_key(self, line):
        return line['url']

    def format(self, key, count):
        return "{0:74}{1:6}".format(key[:74], count)


class TopIPAddresses(Collector):
    NAME = "TOP IP ADDRESSES"
    LIMIT = 6
    LINES = 7

    def dump(self):
        self.sort() # why?!
        return Collector.dump(self)

    def make_key(self, line):
        return line['remote_addr']

    def format(self, key, count):
        return "{0:25}{1:10}".format(key, count)


class TopStatuses(Collector):
    NAME = "TOP STATUSES"
    LIMIT = 6
    LINES = 7

    def dump(self):
        self.sort() # why?!
        return Collector.dump(self)

    def make_key(self, line):
        return line['status']

    def format(self, key, count):
        return "{0:20}{1:15}".format(str(key), count)


class LastConnectionNumber(FakeCollector):
    NAME = "LAST CONNECTION NUMBER"
    LINES = 1

    def __init__(self):
        self.last = 0

    def add(self, line):
        self.last = line['connection']

    def write(self, window, x=0, width=80):
        window.addstr(0, x, ("{0:" + str(width) + "}").format("{0:25}{1:10}".format(self.NAME, self.last)), curses.color_pair(1))
        window.refresh()

    def dump(self):
        return {"name": "LAST CONNECTION NUMBER", "data": self.last}


class MegabytesSent(FakeCollector):
    NAME = "MEGABYTES SENT"
    LINES = 1

    def __init__(self):
        self.sent = 0

    def add(self, line):
        self.sent += line['bytes_sent']

    def write(self, window, x=0, width=80):
        window.addstr(0, x, ("{0:" + str(width) + "}").format("{0:25}{1:10}".format(self.NAME, self.sent / 1024 / 1024)), curses.color_pair(1))
        window.refresh()

    def dump(self):
        return {"name": "BYTES SENT", "data": self.sent}

    def clear(self):
        self.sent = 0
