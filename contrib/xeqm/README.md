# XEQM Session Router operator kit

Everything a XEQM service-node operator needs to run the Session Router relay
sidecar alongside their node. The relay is non-enforcing today; it runs now so a
node is already proven on Session Router before enforcement turns on at HF23.

## Contents

- `INSTALL.md` — step-by-step install guide (read this first).
- `session-router.ini.example` — relay config template (`netid=xeqm`, oxend socket,
  bootstrap, logging).
- `xeqm-session-router@.service` — systemd template unit (one instance per node).
- `make-package.sh` — assemble a distributable tarball from built binaries plus the
  files here and `../bootstrap/xeqm.signed`.
- `tools/select-bootstrap-rcs.py` — pick bootstrap anchor RCs (see below).

The signed bootstrap itself lives with the other networks' bootstraps at
`../bootstrap/xeqm.signed`, built in the canonical format by
`../bootstrap/make-bootstrap-list.sh` (a bencoded list of signed RelayContacts).

## Building a package

    ./make-package.sh amd64 /path/to/built/bin
    ./make-package.sh arm64 /path/to/built/bin

Each run writes `dist/session-router-xeqm-linux-<arch>-<version>.tar.xz` with an
in-package `SHA256SUMS`. The binaries come from a static build of this repo
(`cmake -G Ninja .. -DBUILD_STATIC_DEPS=ON -DSROUTER_NATIVE_BUILD=OFF -DWITH_SYSTEMD=OFF
-DCMAKE_BUILD_TYPE=Release && ninja`).

## Refreshing the bootstrap anchors

`../bootstrap/xeqm.signed` is a list of signed RelayContacts for stable, reachable
XEQM relays. Upstream built-in seeds do not serve the `xeqm` netid, so this file is
required to join. Expired RCs in it are fine (the loader accepts them and fetches
fresh ones on connect); what matters is that each listed IP:port still hosts a relay.

To regenerate from a live hub's node database, pick the freshest relay per distinct
host IP and wrap them in the list format:

    # on a well-connected relay host, with its nodedb copied locally:
    tools/select-bootstrap-rcs.py <nodedb-dir> ../bootstrap/xeqm.signed

The selector prints the chosen anchors (IP, port, host). Prefer stable, controlled,
provider-diverse hosts so a single operator or outage can't take bootstrap down.
