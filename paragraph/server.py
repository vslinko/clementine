import threading
import BaseHTTPServer
import json


__all__ = ["Server"]


class Server(threading.Thread):
    def __init__(self, reports):
        threading.Thread.__init__(self)

        self.reports = reports
        self.httpd = None

    def run(self):
        if self.httpd:
            try:
                self.httpd = BaseHTTPServer.HTTPServer(("", 8080), ServerHandler)
                self.httpd.timeout = 1.0
                self.httpd.thread = self
                self.httpd.serve_forever()
            except:
                pass

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()


class ServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        res = {}
        for report in self.server.thread.reports:
            res[report.NAME] = report.dump()

        self.wfile.write(json.dumps(res, indent=4))

    def log_message(self, format, *args):
        pass
