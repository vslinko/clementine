import time
import curses
from paragraph.thread import LoopThread

try:
    from collections import Counter
except ImportError:
    from paragraph.counter import Counter


__all__ = ["TopQueriesByIPAddressReport", "SuspiciousIPReport", "TopQueriesReport", "TopIPAddressesReport",
           "TopStatusesReport", "LastConnectionNumberReport", "MegabytesSentReport"]


class Report(LoopThread):
    NAME = "REPORT"
    REFRESH_TIME = 1.0
    MIN_COLS = 1
    RESET_COUNT = 300

    def __init__(self):
        LoopThread.__init__(self)
        self.lines = 0
        self.cols = 0
        self.window = None

    def run(self):
        count = 0
        while self.launched():
            time.sleep(self.REFRESH_TIME)

            if self.cols < self.MIN_COLS:
                self.window.clear()
                continue

            self.refresh()

            count += 1
            if count == self.RESET_COUNT:
                self.reset()
                count = 0

    def update_window(self, lines, cols, window):
        if self.window:
            self.window.clear()
            self.window.refresh()

        self.lines = lines
        self.cols = cols
        self.window = window

    def setup(self):
        pass

    def add(self, record):
        pass

    def dump(self):
        pass

    def refresh(self):
        pass

    def reset(self):
        pass


class TopReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.reset()

    def add(self, record):
        key = self.make_key(record)

        if not key:
            return

        self.top[key] += 1

    def refresh(self):
        sorted_top = self.sort(self.lines - 1)

        self.window.clear()
        self.window.insstr(("{0:" + str(self.cols) + "}").format(self.NAME), curses.color_pair(1))

        line = 1
        for key, count in sorted_top:
            self.window.move(line, 0)
            self.window.insstr(self.format(key, count))
            line += 1

    def sort(self, length):
        return self.top.most_common(length)

    def dump(self):
        return self.sort(10)

    def update_window(self, lines, cols, window):
        Report.update_window(self, lines, cols, window)
        self.update_format()

    def reset(self):
        self.format_string = ""
        self.string_size = 0
        self.top = Counter()

    def make_key(self, record):
        pass

    def format(self, key, count):
        pass

    def update_format(self):
        pass


class TopQueriesByIPAddressReport(TopReport):
    NAME = "TOP QUERIES BY IP ADDRESS"
    MIN_COLS = 32

    def make_key(self, record):
        if record["remote_addr"] == "83.229.211.229" or record["remote_addr"] == "83.229.185.11":
            return False

        return (record["remote_addr"], record["url"])

    def format(self, key, count):
        ip, url = key

        return self.format_string.format(ip, url[:self.string_size], count)

    def update_format(self):
        url_field_size = self.cols - 16 - 6
        self.format_string = "{0:16}{1:" + str(url_field_size) + "}{2:6}"
        self.string_size = url_field_size - 1


class SuspiciousIPReport(TopQueriesByIPAddressReport):
    NAME = "SUSPICIOUS IP"

    def sort(self, length):
        result = []
        count = 0
        for key, value in self.top:
            if "samo" in key[1] and "andromeda" not in key[1] and value > 10:
                result.append((key, value))

                count += 1
                if count == length:
                    break

        return result


class TopQueriesReport(TopReport):
    NAME = "TOP QUERIES"
    MIN_COLS = 16

    def make_key(self, record):
        return record["url"]

    def format(self, url, count):
        return self.format_string.format(url[:self.string_size], count)

    def update_format(self):
        url_field_size = self.cols - 6
        self.format_string = "{0:" + str(url_field_size) + "}{1:6}"
        self.string_size = url_field_size - 1


class TopIPAddressesReport(TopReport):
    NAME = "TOP IP ADDRESSES"
    MIN_COLS = 22

    def make_key(self, record):
        return record["remote_addr"]

    def format(self, key, count):
        return self.format_string.format(key, count)

    def update_format(self):
        self.format_string = "{0:16}{1:" + str(self.cols - 16) + "}"


class TopStatusesReport(TopReport):
    NAME = "TOP STATUSES"
    MIN_COLS = 10

    def make_key(self, record):
        return str(record["status"])

    def format(self, key, count):
        return self.format_string.format(key, count)

    def update_format(self):
        self.format_string = "{0:4}{1:" + str(self.cols - 4) + "}"


class OneLineReport(Report):
    def refresh(self):
        name_col = len(self.NAME) + 1
        count_col = self.cols - name_col

        dump = self.dump()

        self.window.clear()

        if len(str(dump)) > count_col or name_col + count_col > self.cols:
            return

        self.window.insstr(("{0:" + str(name_col) + "}{1:" + str(count_col) + "}").format(self.NAME, dump),
            curses.color_pair(1))


class LastConnectionNumberReport(OneLineReport):
    NAME = "LAST CONNECTION NUMBER"

    def __init__(self):
        OneLineReport.__init__(self)
        self.last = 0

    def add(self, record):
        self.last = record["connection"]

    def dump(self):
        return self.last


class MegabytesSentReport(OneLineReport):
    NAME = "MEGABYTES SENT"

    def __init__(self):
        OneLineReport.__init__(self)
        self.sent = 0

    def add(self, record):
        self.sent += record["bytes_sent"]

    def dump(self):
        return self.sent / 1024 / 1024

    def reset(self):
        self.sent = 0
