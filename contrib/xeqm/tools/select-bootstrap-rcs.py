#!/usr/bin/env python3
# Select bootstrap anchor RelayContacts for the XEQM Session Router network and
# write them as a signed bootstrap list (bencoded: l<dict><dict>...e, the same
# format produced by ../bootstrap/make-bootstrap-list.sh).
#
# Picks the freshest RC per distinct host IP from a relay's node database, limited
# to the stable, controlled, provider-diverse ANCHORS below. Edit ANCHORS when the
# anchor set changes. RCs are copied verbatim (already signed); no re-signing.
#
# Usage: select-bootstrap-rcs.py <nodedb-dir> <out.signed>
import sys, os, glob, struct

# ip -> human label. Keep these on stable hosts across diverse providers/regions.
ANCHORS = {
    "144.217.7.129":  "seed-1 (OVH CA)",
    "135.148.44.243": "surf (OVH)",
    "5.78.221.246":   "seed-3 (Hetzner US-OR)",
    "158.220.116.207":"seed-4 (Contabo FR)",
    "217.216.108.148":"seed-5 (Contabo)",
    "217.77.5.231":   "pn-2 (Contabo US-MO)",
    "46.250.241.236": "pn-5 (Contabo AU)",
}

def bdecode(data, i=0):
    c = data[i:i+1]
    if c == b'i':
        j = data.index(b'e', i); return int(data[i+1:j]), j+1
    if c == b'l':
        i += 1; out = []
        while data[i:i+1] != b'e':
            v, i = bdecode(data, i); out.append(v)
        return out, i+1
    if c == b'd':
        i += 1; out = {}
        while data[i:i+1] != b'e':
            k, i = bdecode(data, i); v, i = bdecode(data, i); out[k] = v
        return out, i+1
    j = data.index(b':', i); n = int(data[i:j]); return data[j+1:j+1+n], j+1+n

def main():
    if len(sys.argv) != 3:
        sys.exit("usage: select-bootstrap-rcs.py <nodedb-dir> <out.signed>")
    nodedb, out = sys.argv[1], sys.argv[2]
    best = {}
    for f in glob.glob(os.path.join(nodedb, "*.signed")):
        raw = open(f, "rb").read()
        try:
            d, end = bdecode(raw, 0)
        except Exception:
            continue
        if end != len(raw) or raw[:1] != b'd' or raw[-1:] != b'e':
            continue
        b = d.get(b'4', b'')
        if len(b) != 6:
            continue
        ip = "%d.%d.%d.%d" % (b[0], b[1], b[2], b[3])
        if ip not in ANCHORS:
            continue
        port = struct.unpack(">H", b[4:6])[0]
        ts = d.get(b't') or 0
        if ip not in best or ts > best[ip][1]:
            best[ip] = (raw, ts, port)

    missing = [ip for ip in ANCHORS if ip not in best]
    if missing:
        print("WARNING: no current RC found for:", ", ".join(missing))

    payload = b'l' + b''.join(best[ip][0] for ip in best) + b'e'
    lst, end = bdecode(payload, 0)
    assert end == len(payload) and len(lst) == len(best)
    open(out, "wb").write(payload)

    print("wrote %s : %d anchors, %d bytes" % (out, len(best), len(payload)))
    for ip in sorted(best):
        print("  %-16s :%-5d  %s" % (ip, best[ip][2], ANCHORS[ip]))

if __name__ == "__main__":
    main()
