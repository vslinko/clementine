import threading
import BaseHTTPServer
import json
from paragraph.collectors import SplitCollector


__all__ = ['Server']


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.collectors = []
        try:
            self.httpd = BaseHTTPServer.HTTPServer(('', 8080), ServerHandler)
            self.httpd.timeout = 1.0
        except:
            self.httpd = False

    def run(self):
        if self.httpd:
            self.httpd.thread = self
            self.httpd.serve_forever()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()


class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        res = []
        for collector in self.server.thread.collectors:
            if isinstance(collector, SplitCollector):
                res.append(collector.first_collector.dump())
                res.append(collector.second_collector.dump())
            else:
                res.append(collector.dump())
        self.wfile.write(json.dumps(res, indent=4))

    def log_message(self, format, *args):
        pass