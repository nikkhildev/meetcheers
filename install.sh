#!/usr/bin/env bash
# Install MeetCheers as a clickable app icon (Activities/app menu).
# Run once:  ./install.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="${HOME}/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "${DESKTOP_DIR}/meetcheers.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=MeetCheers
Comment=Soundboard that plays into your meeting mic
Exec=${DIR}/run.sh
Icon=audio-x-generic
Terminal=false
Categories=AudioVideo;Audio;
EOF

chmod +x "${DIR}/run.sh" "${DIR}/setup.sh"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo "Installed. Search 'MeetCheers' in your apps menu and click it."
echo "First launch auto-creates the virtual mic — no terminal needed ever again."
