import time
from paragraph.parser import *
from paragraph.screen import *
from paragraph.server import *
from paragraph.reports import *


def serve(file="/var/log/nginx/access.log", parser_class=Parser, report_classes=None):
    if not report_classes:
        report_classes = [
            TopQueriesByIPAddressReport,
            SuspiciousIPReport,
            TopQueriesReport,
            TopIPAddressesReport,
            TopStatusesReport,
            LastConnectionNumberReport,
            MegabytesSentReport
        ]

    screen = Screen(report_classes)
    screen.start()

    parser = parser_class(screen.reports, file)
    parser.start()

    for report in screen.reports:
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

            for report in screen.reports:
                report.stop()

            break
