import curses
import time
import math
from paragraph.thread import LoopThread


__all__ = ["Screen"]


class Screen(LoopThread):
    def __init__(self, report_classes):
        LoopThread.__init__(self)

        self.reports = [report_class() for report_class in report_classes]
        self.screen = curses.initscr()

        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_MAGENTA)

        self.lines, self.cols = self.screen.getmaxyx()
        self.update_screen()

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

            for report in self.reports:
                report.window.refresh()

    def update_screen(self):
        lines = int(math.floor(self.lines / len(self.reports)))
        line = 0
        for report in self.reports:
            total_lines = lines

            if line == 0:
                total_lines += self.lines - (lines * len(self.reports))

            window = self.screen.subwin(total_lines, self.cols, line, 0)
            report.update_window(total_lines, self.cols, window)

            line += total_lines
