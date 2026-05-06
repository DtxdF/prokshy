#!/usr/bin/env python

import argparse
import socket
import sys
import tempfile
import traceback

DEFAULT_TIMEOUT = 1
DEFAULT_BUFSIZE = 1048576

LOG_STDERR = sys.stderr

def main():
    try:
        start()

    except Exception as err:
        print_pretty_exc(err)
        sys.exit(1)

def start():
    parser = argparse.ArgumentParser(
        prog="prokshy",
        description="Small and lightweight bhyve agent (client)",
        add_help=False
    )
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT)
    parser.add_argument("--command", required=True)
    from_group = parser.add_mutually_exclusive_group(required=True)
    from_group.add_argument("--from-string")
    from_group.add_argument("--from-file")
    parser.add_argument("--socket-path", required=True)

    args = parser.parse_args()

    timeout = args.timeout

    if timeout <= 0:
        log_err(f"{timeout}: timeout must be a positive integer constant")
        sys.exit(1)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(args.socket_path)
    sock.settimeout(timeout)

    data = args.from_string

    if args.from_file is not None:
        with open(args.from_file, "r") as fd:
            data = fd.readline()

    else:
        if len(data) > 0:
            data = data.splitlines()[0]

    command = args.command

    make_data = "%s\n%s\n" % (command, data)

    while True:
        try:
            buff = sock.recv(DEFAULT_BUFSIZE)

        except TimeoutError:
            break

    sock.sendall(make_data.encode())

    skip = True

    while True:
        try:
            buff = sock.recv(DEFAULT_BUFSIZE)

        except TimeoutError:
            break

        if skip:
            skipdata = "%s\r\n%s\r\n" % (command, data)
            skipdata = skipdata.encode()
            skiplen = len(skipdata)
            if skipdata == buff[:skiplen]:
                buff = buff[skiplen:]
            skip = False

            if len(buff) == 0:
                continue

        sys.stdout.buffer.write(buff)
        sys.stdout.buffer.flush()

    sys.exit(0)

def log_err(m):
    print("###> %s" % m, file=LOG_STDERR)

def print_pretty_exc(exc):
    print("Exception:", file=LOG_STDERR)
    print("", "type:", exc.__class__.__name__, file=LOG_STDERR)
    print("", "error:", exc, file=LOG_STDERR)

    with tempfile.NamedTemporaryFile(prefix="prokshy", mode="w", delete=False) as fd:
        print("", "file:", fd.name, file=LOG_STDERR)
        traceback.print_exc(file=fd)

if __name__ == "__main__":
    main()
