#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
echo "[\$(date --iso-8601=seconds)] Stopping DigiFlot from \$DIR" >> /tmp/digiflot-desktop-run.log
pkill -f "python.*digiflot" && echo "DigiFlot stopped." || echo "No DigiFlot process found."
