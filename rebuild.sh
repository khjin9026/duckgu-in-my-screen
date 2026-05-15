#!/bin/bash
# 덕구.app 빌드 + ad-hoc 서명 후 최상위 폴더로 끌어올리기
# 사용: ./rebuild.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/src"

# 빌드 전용 venv — 시스템 Python 에 깔린 다른 패키지들이 번들에 안 딸려오게
# 첫 실행 시에만 생성 (약 1~2분 소요), 이후엔 재사용
VENV_DIR=".venv-build"
if [ ! -d "$VENV_DIR" ]; then
  echo "🐣 빌드용 가상환경 생성 중 (최초 1회, 1~2분 소요)..."
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet \
    pyqt5 \
    pyobjc-framework-Cocoa \
    pyobjc-framework-Quartz \
    pyinstaller
fi
PYTHON="$VENV_DIR/bin/python"

echo "🦆 덕구 빌드 시작..."
# 안 쓰는 Python 모듈 제외 (번들 빌드 시간 단축)
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
# --name 을 ASCII (duckgu) 로 빌드 — 한글 파일명일 때 macOS codesign 이
# "code object is not signed at all" 로 거절하는 버그가 있어서 영문으로 빌드 후
# 사용자에게 보이는 표시 이름만 한글로 덮어씀
"$PYTHON" -m PyInstaller --windowed --name duckgu --icon icon.icns --noconfirm --clean "${EXCLUDES[@]}" desktop_pet.py

# ASCII 경로로 옮겨서 작업 (경로/이름에 한글 있으면 codesign 이 가끔 막힘)
SIGN_DIR="/tmp/duckgu-build-$$"
mkdir -p "$SIGN_DIR"
mv dist/duckgu.app "$SIGN_DIR/duckgu.app"

# Info.plist 손질
# - LSUIElement: Dock 아이콘 안 뜨게
# - CFBundleName/DisplayName: 사용자에게 보이는 이름은 "덕구"
# - CFBundleIdentifier: ASCII (서명에 들어가므로 한글이면 깨질 수 있음)
INFO="$SIGN_DIR/duckgu.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$INFO"
/usr/libexec/PlistBuddy -c "Set :CFBundleName 덕구" "$INFO"
/usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string 덕구" "$INFO" 2>/dev/null || \
  /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName 덕구" "$INFO"
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.hyejin.duckgu" "$INFO"

# 모든 서명 재귀적으로 벗기기 — PyInstaller 가 빌드 도중 자동 서명을 시도하다
# 실패하면 어정쩡한 상태(일부만 서명됨) 로 남는데, 그 위에서 재서명하면
# 검증이 "sealed resource missing/invalid" 로 거절함. 처음부터 깨끗하게.
echo "🧹 기존 서명 제거 중..."
find "$SIGN_DIR/duckgu.app" \( -name "*.dylib" -o -name "*.so" \) -type f \
  -exec codesign --remove-signature {} \; 2>/dev/null || true
find "$SIGN_DIR/duckgu.app" -name "*.framework" -type d \
  -exec codesign --remove-signature {} \; 2>/dev/null || true
codesign --remove-signature "$SIGN_DIR/duckgu.app/Contents/MacOS/duckgu" 2>/dev/null || true
codesign --remove-signature "$SIGN_DIR/duckgu.app" 2>/dev/null || true

# ad-hoc 서명 — 안에서부터 바깥으로 (--deep 은 macOS 버그로 bus error 나서 수동 처리)
echo "🔏 ad-hoc 서명 중..."
find "$SIGN_DIR/duckgu.app" \( -name "*.dylib" -o -name "*.so" \) -type f \
  -exec codesign --force --sign - {} \; 2>&1 | grep -v "replacing existing" || true
find "$SIGN_DIR/duckgu.app" -name "*.framework" -type d \
  -exec codesign --force --sign - {} \; 2>&1 | grep -v "replacing existing" || true
codesign --force --sign - "$SIGN_DIR/duckgu.app/Contents/MacOS/duckgu"
codesign --force --sign - "$SIGN_DIR/duckgu.app"

# 검증 (실패하면 빌드 중단)
echo "🔎 서명 검증 중..."
codesign --verify --strict "$SIGN_DIR/duckgu.app"
echo "✅ 서명 통과"

# 최종 위치로 한글 이름 .app 으로 이동 (폴더 이름은 서명에 영향 없음)
cd "$SCRIPT_DIR"
rm -rf 덕구.app
mv "$SIGN_DIR/duckgu.app" ./덕구.app
rmdir "$SIGN_DIR" 2>/dev/null || true

echo "✅ 빌드 완료 — $(pwd)/덕구.app"
