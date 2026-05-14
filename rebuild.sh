#!/bin/bash
# 덕구.app 빌드 후 최상위 폴더로 끌어올리기
# 사용: ./rebuild.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/src"

echo "🦆 덕구 빌드 시작..."
python3 -m PyInstaller --windowed --name 덕구 --icon icon.icns --noconfirm --clean desktop_pet.py

# Dock 아이콘 안 뜨게 LSUIElement 적용
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/덕구.app/Contents/Info.plist

# 빌드된 .app을 최상위 폴더로 이동 (기존 거 덮어쓰기)
cd "$SCRIPT_DIR"
rm -rf 덕구.app
mv src/dist/덕구.app ./덕구.app

echo "✅ 빌드 완료 — $(pwd)/덕구.app"
