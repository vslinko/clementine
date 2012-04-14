import time
import paragraph.parser
import paragraph.screen
import paragraph.server
import paragraph.reports


def serve(report_classes=None, parser_class=paragraph.parser.Parser):
    if not report_classes:
        report_classes = [
            paragraph.reports.TopQueriesByIPAddressReport,
            paragraph.reports.SuspiciousIPReport,
            paragraph.reports.TopQueriesReport,
            paragraph.reports.TopIPAddressesReport,
            paragraph.reports.TopStatusesReport,
            paragraph.reports.LastConnectionNumberReport,
            paragraph.reports.MegabytesSentReport
        ]

    screen = paragraph.screen.Screen(report_classes)
    screen.start()

    parser = parser_class(screen.reports)
    parser.start()

    for report in screen.reports:
        report.start()
        time.sleep(0.1)

    server = paragraph.server.Server(screen.reports)
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
