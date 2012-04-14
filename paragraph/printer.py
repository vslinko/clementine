import curses
import time
from paragraph.thread import LoopThread


__all__ = ['Printer']


class Printer(LoopThread):
    def __init__(self):
        LoopThread.__init__(self)
        self.collectors = []
        self.windows = {}
        self.lines = 0

    def run(self):
        try:
            curses.initscr()
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_MAGENTA)
            while not self.kill_received:
                for collector in self.collectors:
                    if collector not in self.windows:
                        # line+1 because curses can't write last character
                        self.windows[collector] = curses.newwin(collector.LINES + 1, 80, self.lines, 0)
                        self.lines += collector.LINES
                    collector.write(self.windows[collector])
                time.sleep(1.0)
        finally:
            curses.endwin()
