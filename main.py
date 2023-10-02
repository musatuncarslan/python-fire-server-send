#!/usr/bin/python3

from client import Client
import argparse
import logging
import sys
import os
import signal

defaults = {
    'host':           '0.0.0.0',
    'port':           9002,
}

# TODO: ADD SEND DATA
def main(args):
    # Create a multi-threaded dispatcher to handle incoming connections
    client = Client(args.host, args.port, args.senddatafile)

    # Trap signal interrupts (e.g. ctrl+c, SIGTERM) and gracefully stop
    def handle_signals(signum, frame):
        print("Received signal interrupt -- stopping server")
        client.socket.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signals)
    signal.signal(signal.SIGINT,  handle_signals)

    # Start server
    client.serve()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Example server for MRD streaming format',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port',            type=int,            help='Port')
    parser.add_argument('-H', '--host',            type=str,            help='Host')
    parser.add_argument('-v', '--verbose',         action='store_true', help='Verbose output.')
    parser.add_argument('-l', '--logfile',         type=str,            help='Path to log file')
    parser.add_argument('-f', '--senddatafile',    type=str,            help='Path to saved data files')
    parser.add_argument('-r', '--crlf',            action='store_true', help='Use Windows (CRLF) line endings')

    parser.set_defaults(**defaults)

    args = parser.parse_args()

    if args.crlf:
        fmt='%(asctime)s - %(message)s\r'
    else:
        fmt='%(asctime)s - %(message)s'

    if args.logfile:
        print("Logging to file: ", args.logfile)

        if not os.path.exists(os.path.dirname(args.logfile)):
            os.makedirs(os.path.dirname(args.logfile))

        logging.basicConfig(filename=args.logfile, format=fmt, level=logging.WARNING)
    else:
        print("No logfile provided")
        logging.basicConfig(format=fmt, level=logging.WARNING)

    if args.senddatafile:
        print("Sending  file: ", args.senddatafile)

        if not os.path.exists(os.path.dirname(args.senddatafile)):
            os.makedirs(os.path.dirname(args.senddatafile))

        logging.basicConfig(filename=args.senddatafile, format=fmt, level=logging.WARNING)
    else:
        print("No data folder provided")
        logging.basicConfig(format=fmt, level=logging.WARNING)

    if args.verbose:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    main(args)
