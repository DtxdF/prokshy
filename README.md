# prokshy

**prokshy** is a small and lightweight script that uses [unixexec](https://github.com/DtxdF/unixexec) to exchange data through the special character file (`/dev/vtcon/prokshy`) created by `virtio_console(4)`. This script is designed to "standardize" the way a command is executed from the host into the virtual machine. The host connects to the `unix(4)` socket created by `bhyve(8)` and then sends a command, a space, and then the data (or the command’s argument). prokshy doesn’t care about the argument format: you can use netstring, JSON, base64, or any other format that can be sent for the command you’ve created. That’s the other advantage of prokshy: it allows you to implement a "command," making it truly flexible.

## Getting Started

Inside the VM, enable and start prokshy.

```sh
sysrc prokshy_enable=YES
service prokshy start
```

This will wait to receive data from `/dev/vtcon/prokshy`, but since no command has been implemented, prokshy will simply ignore any data sent by the host.

**/usr/local/etc/prokshy/command.d/statgrab**:

```sh
#!/bin/sh

PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin; export PATH

if ! pkg info -e statgrab; then
    pkg install -y statgrab || exit $?
fi

exec statgrab
```

This command implements the “statgrab” command to run the executable file provided by [devel/libstatgrab](https://freshports.org/devel/libstatgrab), which displays useful information about the system. Note that the argument is completely ignored, and you must set the execute bit on this file for prokshy to run it.

```console
# chmod +x /usr/local/etc/prokshy/command.d/statgrab
```

Next, from the host, you can use `nc(1)` to connect to the `unix(4)` socket created by `bhyve(8)` and run the command we've implemented.

```sh
# echo "statgrab" | nc -U vtcon.prokshy
statgrab
const.0 = 0
cpu.ctxsw = 0
cpu.idle = 7212359
cpu.intrs = 0
cpu.iowait = 0
cpu.kernel = 14792
cpu.nice = 0
cpu.nvctxsw = 0
cpu.softintrs = 0
cpu.swap = 0
cpu.syscalls = 0
cpu.systime = 1777959159
cpu.total = 7241438
cpu.user = 7018
cpu.vctxsw = 0
disk.nda0.disk_name = nda0
disk.nda0.read_bytes = 677440000
disk.nda0.systime = 1777959159
disk.nda0.write_bytes = 29893522944
disk.pass0.disk_name = pass0
disk.pass0.read_bytes = 0
disk.pass0.systime = 1777959159
disk.pass0.write_bytes = 0
fs.devfs.avail = 1024
fs.devfs.avail_blocks = 2
fs.devfs.avail_inodes = 0
fs.devfs.block_size = 512
fs.devfs.device_canonical = devfs
fs.devfs.device_name = devfs
fs.devfs.free_blocks = 2
fs.devfs.free_inodes = 0
fs.devfs.fs_type = devfs
fs.devfs.io_size = 512
fs.devfs.mnt_point = /dev
fs.devfs.size = 1024
fs.devfs.total_blocks = 2
fs.devfs.total_inodes = 0
fs.devfs.used = 0
fs.devfs.used_blocks = 0
fs.devfs.used_inodes = 0
fs.nda0p3.avail = 1780576256
fs.nda0p3.avail_blocks = 434711
fs.nda0p3.avail_inodes = 1071470
fs.nda0p3.block_size = 4096
fs.nda0p3.device_canonical = /dev/nda0p3
fs.nda0p3.device_name = /dev/nda0p3
fs.nda0p3.free_blocks = 617382
fs.nda0p3.free_inodes = 1071470
fs.nda0p3.fs_type = ufs
fs.nda0p3.io_size = 32768
fs.nda0p3.mnt_point = /
fs.nda0p3.size = 9352802304
fs.nda0p3.total_blocks = 2283399
fs.nda0p3.total_inodes = 1201918
fs.nda0p3.used = 6824005632
fs.nda0p3.used_blocks = 1666017
fs.nda0p3.used_inodes = 130448
general.bitwidth = 64
general.hostname = test-vm
general.hoststate = unknown
general.ncpus = 2
general.ncpus_cfg = 2
general.os_name = FreeBSD
general.os_release = 15.1-STABLE
general.os_version = FreeBSD 15.1-STABLE stable/15-n283454-4702f6ab1514 GENERIC
general.platform = amd64
general.uptime = 28510
load.min1 = 0.104004
load.min15 = 0.222168
load.min5 = 0.184570
mem.cache = 0
mem.free = 1606631424
mem.total = 2054467584
mem.used = 447836160
net.lo0.collisions = 0
net.lo0.duplex = unknown
net.lo0.ierrors = 0
net.lo0.interface_name = lo0
net.lo0.ipackets = 389
net.lo0.oerrors = 0
net.lo0.opackets = 389
net.lo0.rx = 23360
net.lo0.speed = 0
net.lo0.systime = 1777959159
net.lo0.tx = 23360
net.lo0.up = true
net.vtnet0.collisions = 0
net.vtnet0.duplex = full
net.vtnet0.ierrors = 0
net.vtnet0.interface_name = vtnet0
net.vtnet0.ipackets = 621114
net.vtnet0.oerrors = 0
net.vtnet0.opackets = 442069
net.vtnet0.rx = 735707386
net.vtnet0.speed = 10000
net.vtnet0.systime = 1777959159
net.vtnet0.tx = 36502321
net.vtnet0.up = true
page.in = 2
page.out = 718
page.systime = 1777959159
proc.running = 2
proc.sleeping = 31
proc.stopped = 0
proc.total = 33
proc.zombie = 0
swap.free = 1073676288
swap.total = 1073741824
swap.used = 65536
user.names = root
user.num = 1
user.pts/1.from = ajnet.appjail
user.pts/1.login_name = root
user.pts/1.login_time = 1777931158
user.pts/1.tty = pts/1
^C
```

A slightly more complex command may require a more robust programming language, such as Python, and, as mentioned earlier, it’s up to you how you parse the argument passed via stdin.

**/usr/local/etc/prokshy/command.d/OpenFile**:

```python
#!/usr/local/bin/python

import shlex
import sys

lex = shlex.shlex(posix=True)
lex.whitespace = ","
lex.whitespace_split = True

params = {}

for arg in lex:
    arg = arg.split("=", 1)

    if len(arg) == 1:
        (key, value) = (arg, None)

    else:
        (key, value) = arg

    params[key] = value

filename = params.get("filename")
assert filename is not None

mode = params.get("mode", "read")
assert not (mode != "read" and mode != "write")

if mode == "read":
    from base64 import b64encode

    with open(filename, "rb") as fd:
        data = b64encode(fd.read())
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()

else:
    from base64 import b64decode

    content = params.get("content", "")
    content = b64decode(content)

    with open(filename, "wb") as fd:
        fd.write(content)
```

**Console**:

In the following example, let's use the CLI client, which is more powerful.

```console
# prokshy --command OpenFile --from-string "filename=/tmp/hello.txt,mode=write,content=SGVsbG8hCg==" --socket-path vtcon.prokshy
# prokshy --command OpenFile --from-string "filename=/tmp/hello.txt" --socket-path vtcon.prokshy | base64 -d
Hello!
```

## Caveats

As you have probably noticed, in the case of `virtio_console(4)`, there is always a connected peer; therefore, if you send data through the `unix(4)` socket (host) or the special character file (VM), the data is always sent, but this does not mean that the other side will perform something useful (if no one sees the data, there's nothing to do).

## Notes

1. Command names are limited to: `^[a-zA-Z0-9_.-]+$`. If the host attempts to execute a command that contains a character not allowed, the data is simply ignored.
