#!/bin/bash
# 덕구.app 빌드 후 최상위 폴더로 끌어올리기
# 사용: ./rebuild.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/src"

echo "🦆 덕구 빌드 시작..."
# 안 쓰는 Qt/Python 모듈 제외해서 번들 크기 줄이기
EXCLUDES=(
  --exclude-module PyQt5.QtNetwork
  --exclude-module PyQt5.QtQml
  --exclude-module PyQt5.QtQmlModels
  --exclude-module PyQt5.QtQuick
  --exclude-module PyQt5.QtWebSockets
  --exclude-module PyQt5.QtPrintSupport
  --exclude-module PyQt5.QtSvg
  --exclude-module PyQt5.QtMultimedia
  --exclude-module PyQt5.QtMultimediaWidgets
  --exclude-module PyQt5.QtSql
  --exclude-module PyQt5.QtTest
  --exclude-module PyQt5.QtXml
  --exclude-module PyQt5.QtBluetooth
  --exclude-module PyQt5.QtDBus
  --exclude-module PyQt5.QtOpenGL
  --exclude-module PyQt5.QtWebChannel
  --exclude-module PyQt5.QtWebEngine
  --exclude-module PyQt5.QtWebEngineCore
  --exclude-module PyQt5.QtWebEngineWidgets
  --exclude-module tkinter
)
python3 -m PyInstaller --windowed --name 덕구 --icon icon.icns --noconfirm --clean "${EXCLUDES[@]}" desktop_pet.py

# Dock 아이콘 안 뜨게 LSUIElement 적용
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" dist/덕구.app/Contents/Info.plist

# 안 쓰는 Qt 프레임워크/플러그인 제거 (번들 크기 ~14MB 절감)
# cocoa 플랫폼 플러그인이 의존하는 QtDBus/QtPrintSupport 는 남겨야 함
QT_LIB=dist/덕구.app/Contents/Frameworks/PyQt5/Qt5/lib
QT_PLUGINS=dist/덕구.app/Contents/Frameworks/PyQt5/Qt5/plugins
rm -rf "$QT_LIB/QtQuick.framework" "$QT_LIB/QtQml.framework" \
       "$QT_LIB/QtQmlModels.framework" "$QT_LIB/QtWebSockets.framework" \
       "$QT_LIB/QtNetwork.framework" "$QT_LIB/QtSvg.framework"
rm -f "$QT_PLUGINS/platforms/libqminimal.dylib" \
      "$QT_PLUGINS/platforms/libqoffscreen.dylib" \
      "$QT_PLUGINS/platforms/libqwebgl.dylib"

# 빌드된 .app을 최상위 폴더로 이동 (기존 거 덮어쓰기)
cd "$SCRIPT_DIR"
rm -rf 덕구.app
mv src/dist/덕구.app ./덕구.app

echo "✅ 빌드 완료 — $(pwd)/덕구.app"
