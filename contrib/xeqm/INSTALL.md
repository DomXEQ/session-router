# XEQM Session Router relay — install guide

This package installs the Session Router relay sidecar alongside your XEQM service
node. It runs non-enforcing today: the core network does not yet require it. Install
it now so your node is already proven on Session Router when enforcement turns on at
HF23, instead of scrambling on the day.

The relay fetches its identity from your running `xeqm-d` service node and joins the
XEQM Session Router network. It does not touch your node's keys on disk and does not
change how your node validates or earns.

## Requirements

- Linux, amd64 or arm64 (the two tarballs in this release).
- A running XEQM service node (`xeqm-d --service-node`) on the same host.
- Root (sudo) to install the binary, unit, and firewall rule.
- One inbound UDP port open (1190 in this guide).
- `/dev/net/tun` available (standard on all mainstream kernels/VPS).

## Step 1 — let your core daemon expose the key socket

Session Router reads your service-node keys over a local control socket. Your
`xeqm-d` must be started with (adjust the path to your own data dir):

    --lmq-local-control=ipc:///var/lib/xeqm/oxend.sock

If your `xeqm-d` command or config does not already have `--lmq-local-control`, add
it and restart the daemon. Confirm the socket exists afterward:

    ls -l /var/lib/xeqm/oxend.sock

The socket stays local to the machine; nothing is exposed to the network by this.

## Step 2 — install the binaries

Pick the tarball for your architecture, verify it, unpack it, and place the binaries:

    sha256sum -c SHA256SUMS
    tar xf session-router-xeqm-linux-amd64-<ver>.tar.xz
    cd session-router-xeqm-linux-amd64-<ver>
    sudo install -o root -g root -m 0755 bin/session-router        /opt/xeqm/bin/
    sudo install -o root -g root -m 0755 bin/session-router-config  /opt/xeqm/bin/

## Step 3 — install the bootstrap file

    sudo mkdir -p /var/lib/xeqm-session-router
    sudo install -o xeqm -g xeqm -m 0644 bootstrap.signed /var/lib/xeqm-session-router/

(Use whatever unprivileged user owns your node's data dir if it is not `xeqm`.)

## Step 4 — write your config

Copy the example and edit the three things that are specific to your host:

    sudo cp session-router.ini.example /etc/xeqm-session-router/sn.ini

Edit `/etc/xeqm-session-router/sn.ini` and set:

- `data-dir` — a per-instance dir, e.g. `/var/lib/xeqm-session-router/sn`
- `public-ip` — your server's public IPv4
- `[oxend] rpc` — the exact `ipc://...oxend.sock` path from Step 1

Leave `netid=xeqm` and the `bootstrap` line as they are.

## Step 5 — install and start the service

    sudo cp xeqm-session-router@.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now xeqm-session-router@sn

The instance name after `@` must match your `.ini` filename (`sn.ini` -> `@sn`).

## Step 6 — open the firewall

Open the inbound UDP port you set in the config (1190 here). For example:

    sudo ufw allow 1190/udp

## Step 7 — verify

    systemctl status xeqm-session-router@sn
    journalctl -u xeqm-session-router@sn -n 50 --no-pager

A healthy relay fetches its keys, loads the bootstrap, and settles at `warn` with no
repeating errors. If you see it retrying the oxend socket, re-check Step 1 (the
`--lmq-local-control` path must match `[oxend] rpc` exactly) and that `xeqm-d` is
running.

## Running more than one node on a host

Repeat Steps 4–5 per instance with a distinct name, a distinct `data-dir`, a distinct
`ifname` (`sr-0`, `sr-1`, ...), a distinct `public-port`/`listen` port, and the
matching per-node `oxend.sock`. The `@`-template unit handles each instance.

## Notes

- Non-enforcing: nothing about your node's rewards or uptime depends on this relay
  yet. It is safe to run now and it gives us a real soak before HF23.
- Updating: replace the two binaries in `/opt/xeqm/bin` and
  `sudo systemctl restart xeqm-session-router@sn`.
- Support / security: report issues to security@xeqmlabs.com.
