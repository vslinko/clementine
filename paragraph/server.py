import threading
import http.server
import json


__all__ = ["Server"]


class Server(threading.Thread):
    def __init__(self, reports):
        threading.Thread.__init__(self)

        self.reports = reports
        self.httpd = None

    def run(self):
        try:
            self.httpd = http.server.HTTPServer(("", 8080), ServerHandler)
            self.httpd.timeout = 1.0
            self.httpd.thread = self
            self.httpd.serve_forever()
        except:
            pass

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()


class ServerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        res = {}
        for inline_reports in self.server.thread.reports:
            for report in inline_reports:
                res[report.NAME] = report.dump()

        self.wfile.write(json.dumps(res, indent=4).encode("utf-8"))

    def log_message(self, format, *args):
        pass
