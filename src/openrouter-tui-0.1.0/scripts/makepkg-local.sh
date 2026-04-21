#!/usr/bin/env bash
# Helper to create a source tarball from the current git HEAD and run makepkg locally.
set -euo pipefail
pkgname="openrouter-tui"
pkgver="0.1.0"

# Create tarball in parent directory that makepkg will use as source
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

git archive --format=tar.gz --prefix="${pkgname}-${pkgver}/" -o "$tmpdir/${pkgname}-${pkgver}.tar.gz" HEAD

# Move tarball into current dir so makepkg can find it
mv "$tmpdir/${pkgname}-${pkgver}.tar.gz" .

echo "Created source tarball: ${pkgname}-${pkgver}.tar.gz"

echo "Now running: makepkg -f"
makepkg -f
