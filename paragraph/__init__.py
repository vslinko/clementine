import time
from paragraph.parser import *
from paragraph.screen import *
from paragraph.server import *
from paragraph.reports import *


def serve(file_path="/var/log/nginx/access.log", parser=None, reports=None):
    if not reports:
        reports = [
            [TopQueriesByIPAddressReport()],
            [SuspiciousIPReport()],
            [TopQueriesReport()],
            [TopIPAddressesReport(), TopStatusesReport()],
            [LastConnectionNumberReport(), MegabytesSentReport()]
        ]

    screen = Screen(reports)
    screen.start()

    if not parser:
        parser = Parser(file_path)
    parser.reports = reports
    parser.start()

    for inline_reports in screen.reports:
        for report in inline_reports:
            report.start()

    server = Server(screen.reports)
    server.start()

    while True:
        try:
            time.sleep(0.1)
        except:
            server.stop()
            screen.stop()
            parser.stop()

            for inline_reports in screen.reports:
                for report in inline_reports:
                    report.stop()

            break
