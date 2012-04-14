import time
import curses
from paragraph.thread import LoopThread


__all__ = ["TopQueriesByIPAddressReport", "SuspiciousIPReport", "TopQueriesReport", "TopIPAddressesReport",
           "TopStatusesReport", "LastConnectionNumberReport", "MegabytesSentReport"]


class Report(LoopThread):
    NAME = "REPORT"
    REFRESH_TIME = 1.0
    MIN_COLS = 1

    def __init__(self, lines, cols, window):
        LoopThread.__init__(self)

        self.lines = lines
        self.cols = cols
        self.window = window

    def run(self):
        while self.launched():
            time.sleep(self.REFRESH_TIME)

            if self.cols < self.MIN_COLS:
                continue

            self.refresh()

    def update_window(self, lines, cols, y):
        self.lines = lines
        self.cols = cols
        self.window.resize(lines, cols)
        self.window.mvwin(y, 0)

    def add(self, record):
        pass

    def dump(self):
        pass

    def refresh(self):
        pass


class TopReport(Report):
    MAX_SIZE = 10000

    def __init__(self, lines, cols, window):
        Report.__init__(self, lines, cols, window)

        self.top = {}

        self.update_title()
        self.window.refresh()

    def add(self, record):
        key = self.make_key(record)

        if key in self.top:
            self.top[key] += 1
        else:
            self.top[key] = 1

    def refresh(self):
        sorted_top = self.sort()[:self.lines - 1]

        self.window.clear()
        self.update_title()

        line = 1
        for key, count in sorted_top:
            self.window.move(line, 0)
            self.window.insstr(self.format(key, count))
            line += 1

        self.window.refresh()

        if len(self.top) > self.MAX_SIZE:
            self.top = {}

    def sort(self):
        return sorted(self.top.iteritems(), key=lambda x: x[1], reverse=True)

    def dump(self):
        return self.sort()[:10]

    def update_window(self, lines, cols, y):
        Report.update_window(self, lines, cols, y)

        self.update_title()
        self.window.refresh()

    def update_title(self):
        self.window.insstr(("{0:" + str(self.cols) + "}").format(self.NAME), curses.color_pair(1))

    def make_key(self, record):
        pass

    def format(self, key, count):
        pass


class TopQueriesByIPAddressReport(TopReport):
    NAME = "TOP QUERIES BY IP ADDRESS"
    MIN_COLS = 32

    def make_key(self, record):
        return (record["remote_addr"], record["url"])

    def format(self, key, count):
        ip, url = key

        url_field_size = self.cols - 16 - 6
        url = url[:url_field_size - 1]

        return ("{0:16}{1:" + str(url_field_size) + "}{2:6}").format(ip, url, count)


class SuspiciousIPReport(TopQueriesByIPAddressReport):
    NAME = "SUSPICIOUS IP"

    def sort(self):
        suspicious = [x for x in self.top.iteritems() if "samo" in x[0][1] and "andromeda" not in x[0][1] and x[1] > 10]
        return sorted(suspicious, key=lambda x: x[1], reverse=True)


class TopQueriesReport(TopReport):
    NAME = "TOP QUERIES"
    MIN_COLS = 16

    def make_key(self, record):
        return record["url"]

    def format(self, url, count):
        url_field_size = self.cols - 6
        url = url[:url_field_size - 1]

        return ("{0:" + str(url_field_size) + "}{1:6}").format(url, count)


class TopIPAddressesReport(TopReport):
    NAME = "TOP IP ADDRESSES"
    MIN_COLS = 22

    def make_key(self, record):
        return record["remote_addr"]

    def format(self, key, count):
        return ("{0:16}{1:" + str(self.cols - 16) + "}").format(key, count)


class TopStatusesReport(TopReport):
    NAME = "TOP STATUSES"
    MIN_COLS = 10

    def make_key(self, record):
        return str(record["status"])

    def format(self, key, count):
        return ("{0:4}{1:" + str(self.cols - 4) + "}").format(key, count)


class OneLineReport(Report):
    def __init__(self, lines, cols, window):
        Report.__init__(self, lines, cols, window)
        self.refresh()

    def refresh(self):
        name_col = len(self.NAME) + 1
        count_col = self.cols - name_col

        dump = self.dump()

        if len(str(dump)) > count_col or name_col + count_col > self.cols:
            return

        self.window.clear()
        self.window.insstr(("{0:" + str(name_col) + "}{1:" + str(count_col) + "}").format(self.NAME, dump), curses.color_pair(1))
        self.window.refresh()


class LastConnectionNumberReport(OneLineReport):
    NAME = "LAST CONNECTION NUMBER"

    def __init__(self, lines, cols, window):
        self.last = 0
        OneLineReport.__init__(self, lines, cols, window)

    def add(self, record):
        self.last = record["connection"]

    def dump(self):
        return self.last


class MegabytesSentReport(OneLineReport):
    NAME = "MEGABYTES SENT"

    def __init__(self, lines, cols, window):
        self.sent = 0
        OneLineReport.__init__(self, lines, cols, window)

    def add(self, record):
        self.sent += record["bytes_sent"]

    def dump(self):
        return self.sent / 1024 / 1024
