import operator
import time
import curses
from paragraph.thread import LoopThread


__all__ = ['Collector', 'FakeCollector', 'SplitCollector']


class Collector(LoopThread):
    NAME = "COLLECTOR"
    LIMIT = 7
    LINES = 8

    def __init__(self):
        LoopThread.__init__(self)
        self.top = {}
        self.sorted_top = []

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
        self.sorted_top = sorted(self.top.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.LIMIT]

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

    def write(self, window, x=0, width=80):
        y = 0
        window.addstr(y, x, ("{0:" + str(width) + "}").format(self.NAME), curses.color_pair(1))
        for key, count in self.sorted_top[:self.LIMIT]:
            y += 1
            window.addstr(y, x, self.format(key, count))
        y += 1
        window.refresh()


class SplitCollector():
    def __init__(self, first_collector, second_collector):
        self.first_collector = first_collector
        self.second_collector = second_collector
        self.LIMIT = max(self.first_collector.LIMIT, self.second_collector.LIMIT)
        self.LINES = self.LIMIT + 1

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

    def write(self, window, x=0, width=80):
        self.first_collector.write(window, 0, 45)
        self.second_collector.write(window, 45, 35)


class FakeCollector():
    NAME = "FAKE COLLECTOR"
    LINES = 0
    LIMIT = 0

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

    def write(self, window, x=0, width=80):
        pass
