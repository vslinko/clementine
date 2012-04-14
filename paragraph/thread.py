import threading


class LoopThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.kill_received = False

    def stop(self):
        self.kill_received = True
