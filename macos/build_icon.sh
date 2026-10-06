#!/usr/bin/env sh
# Regenerates macos/omawrite-icon.svg and macos/omawrite.icns.
set -eu
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
QMAKE="${QMAKE:-$(brew --prefix qt)/bin/qmake}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

python3 "$HERE/make_icon.py" > "$HERE/omawrite-icon.svg"
(cd "$WORK" && "$QMAKE" "$HERE/iconrender/iconrender.pro" >/dev/null && make -s)
mkdir "$WORK/omawrite.iconset"
QT_QPA_PLATFORM=offscreen "$WORK/iconrender" "$HERE/omawrite-icon.svg" "$WORK/omawrite.iconset" \
  16 icon_16x16.png 32 icon_16x16@2x.png 32 icon_32x32.png 64 icon_32x32@2x.png \
  128 icon_128x128.png 256 icon_128x128@2x.png 256 icon_256x256.png 512 icon_256x256@2x.png \
  512 icon_512x512.png 1024 icon_512x512@2x.png
iconutil -c icns "$WORK/omawrite.iconset" -o "$HERE/omawrite.icns"
echo "Wrote $HERE/omawrite.icns"
