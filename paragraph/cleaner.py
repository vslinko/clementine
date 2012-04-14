import time
from paragraph.thread import LoopThread


__all__ = ['Cleaner']


class Cleaner(LoopThread):
    def __init__(self):
        LoopThread.__init__(self)
        self.collectors = []

    def run(self):
        count = 0
        while not self.kill_received:
            time.sleep(1.0)
            count += 1
            if count == 300: # 5 minutes
                for collector in self.collectors:
                    collector.clear()
                count = 0
