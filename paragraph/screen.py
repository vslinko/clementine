import curses
import time
import math
from paragraph.thread import LoopThread


__all__ = ["Screen"]


class Screen(LoopThread):
    def __init__(self, report_classes):
        LoopThread.__init__(self)

        self.reports = []
        self.screen = curses.initscr()

        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_MAGENTA)

        self.lines, self.cols = self.screen.getmaxyx()
        self.init_screen(report_classes)

    def __del__(self):
        curses.endwin()

    def run(self):
        while self.launched():
            time.sleep(0.1)

            lines, cols = self.screen.getmaxyx()

            if self.lines != lines or self.cols != cols:
                self.lines = lines
                self.cols = cols
                self.update_screen()

    def init_screen(self, report_classes):
        self._calculate_size(report_classes, self._init_report)

    def update_screen(self):
        self._calculate_size(self.reports, self._update_report)

    def _init_report(self, report_class, lines, cols, line):
        window = self.screen.subwin(lines, cols, line, 0)
        self.reports.append(report_class(lines, cols, window))

    def _update_report(self, report, lines, cols, line):
        report.update_window(lines, cols, line)

    def _calculate_size(self, items, fun):
        lines = int(math.floor(self.lines / len(items)))
        line = 0
        for item in items:
            total_lines = lines

            if line == 0:
                total_lines += self.lines - (lines * len(items))

            fun(item, total_lines, self.cols, line)

            line += total_lines
