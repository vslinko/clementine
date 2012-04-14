import time
import paragraph.reader
import paragraph.printer
import paragraph.cleaner
import paragraph.server
from paragraph.collectors import *


__all__ = ['serve']


def serve():
    collectors = [
        TopQueriesByIPAddress(),
        #TopQueries(),
        SuspiciousIP(),
        SplitCollector(TopIPAddresses(), TopStatuses()),
        SplitCollector(LastConnectionNumber(), MegabytesSent())
    ]

    reader = paragraph.reader.Reader()
    reader.collectors = collectors
    reader.start()

    for collector in collectors:
        collector.start()

    printer = paragraph.printer.Printer()
    printer.collectors = collectors
    printer.start()

    cleaner = paragraph.cleaner.Cleaner()
    cleaner.collectors = collectors
    cleaner.start()

    server = paragraph.server.Server()
    server.collectors = collectors
    server.start()

    while True:
        try:
            time.sleep(0.1)
        except:
            server.stop()
            printer.stop()
            reader.stop()
            cleaner.stop()
            for collector in collectors:
                collector.stop()
            break
