#!/usr/bin/env bash
# Assemble a community XEQM Session Router relay package from compiled binaries
# plus the operator kit in this directory. Repo-relative; usable by hand or CI.
#
# Usage:
#   make-package.sh <arch> <bindir> [version] [outdir]
#     arch     e.g. amd64 | arm64 (label only)
#     bindir   directory containing the built `session-router` + `session-router-config`
#     version  tag/sha label for the filename (default: `git describe` or "dev")
#     outdir   where to write the tarball (default: ./dist)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"

arch="${1:?arch required (e.g. amd64)}"
bindir="${2:?bindir required (dir with session-router binaries)}"
version="${3:-$(git -C "$repo" describe --tags --always 2>/dev/null || echo dev)}"
outdir="${4:-$PWD/dist}"

for b in session-router session-router-config; do
  [ -x "$bindir/$b" ] || { echo "missing executable: $bindir/$b" >&2; exit 1; }
done

pkg="session-router-xeqm-linux-${arch}-${version}"
stage="$(mktemp -d)"
dst="$stage/$pkg"
mkdir -p "$dst/bin" "$outdir"

install -m 0755 "$bindir/session-router"        "$dst/bin/"
install -m 0755 "$bindir/session-router-config" "$dst/bin/"
install -m 0644 "$repo/contrib/bootstrap/xeqm.signed" "$dst/bootstrap.signed"
install -m 0644 "$here/session-router.ini.example"    "$dst/"
install -m 0644 "$here/xeqm-session-router@.service"  "$dst/"
install -m 0644 "$here/INSTALL.md"                    "$dst/"

( cd "$dst" && find bin bootstrap.signed -type f | sort | xargs sha256sum > SHA256SUMS )
( cd "$stage" && tar cJf "$outdir/$pkg.tar.xz" "$pkg" )
( cd "$outdir" && sha256sum "$pkg.tar.xz" > "$pkg.tar.xz.sha256" )
rm -rf "$stage"
echo "wrote $outdir/$pkg.tar.xz"
