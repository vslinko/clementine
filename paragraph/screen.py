import curses
import time
import math
from paragraph.thread import LoopThread
from paragraph.reports import OneLineReport


__all__ = ["Screen"]


class Screen(LoopThread):
    MARGIN = 3

    def __init__(self, reports):
        LoopThread.__init__(self)

        self.reports = reports
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

            for inline_reports in self.reports:
                for report in inline_reports:
                    report.window.refresh()

    def update_screen(self):
        reports_len = len(self.reports)
        screen_lines = self.lines

        for inline_reports in self.reports:
            if self.is_inline(inline_reports):
                reports_len -= 1
                screen_lines -= 1

        lines = int(math.floor(screen_lines / reports_len))
        line = 0

        for inline_reports in self.reports:
            total_lines = lines

            if line == 0:
                total_lines += screen_lines - (lines * reports_len)

            if self.is_inline(inline_reports):
                total_lines = 1

            cols = int(math.floor(self.cols / len(inline_reports)))
            col = 0

            for report in inline_reports:
                total_cols = cols

                if col == 0:
                    total_cols += self.cols - (cols * len(inline_reports)) + self.MARGIN

                window = self.screen.subwin(total_lines, total_cols - self.MARGIN, line, col)
                report.update_window(total_lines, total_cols - self.MARGIN, window)

                col += total_cols

            line += total_lines

    def is_inline(self, reports):
        return all([isinstance(report, OneLineReport) for report in reports])
