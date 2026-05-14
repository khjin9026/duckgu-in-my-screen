# -*- coding: utf-8 -*-
"""덕구 앱 아이콘 생성 스크립트.
메뉴바 트레이 아이콘과 동일한 디자인을 고해상도(1024x1024)로 그려서 PNG로 저장.
이후 sips 명령어로 .icns 변환해서 PyInstaller 빌드에 사용.
"""

import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor
from PyQt5.QtCore import Qt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

app = QApplication(sys.argv)

# 1024x1024 고해상도 아이콘 (macOS 표준)
SIZE = 1024
pix = QPixmap(SIZE, SIZE)
pix.fill(Qt.transparent)

p = QPainter(pix)
p.setRenderHint(QPainter.Antialiasing)
p.setRenderHint(QPainter.SmoothPixmapTransform)

# 트레이 아이콘이 22x22 좌표계로 그려졌으므로 그대로 스케일업
scale = SIZE / 22

def s(v):
    """22단위 좌표 → 1024단위로 변환."""
    return int(v * scale)

# ----- 머리 (큰 노란 원) -----
p.setBrush(QBrush(QColor(255, 216, 0)))
p.setPen(QPen(QColor(252, 190, 0), 1.2 * scale))
p.drawEllipse(s(1), s(2), s(20), s(19))

# ----- 머리 위 작은 깃털 -----
p.setBrush(QBrush(QColor(255, 216, 0)))
p.setPen(QPen(QColor(252, 190, 0), 1 * scale))
p.drawEllipse(s(8), s(0), s(5), s(4))

# ----- 눈 두 개 (검정 점) -----
p.setBrush(QBrush(QColor(20, 20, 20)))
p.setPen(Qt.NoPen)
p.drawEllipse(s(6), s(9), s(3), s(3))
p.drawEllipse(s(13), s(9), s(3), s(3))

# ----- 부리 (주황) -----
p.setBrush(QBrush(QColor(255, 123, 0)))
p.setPen(QPen(QColor(246, 92, 0), 1 * scale))
p.drawEllipse(s(7), s(13), s(8), s(5))

p.end()

output_path = os.path.join(SCRIPT_DIR, "icon.png")
pix.save(output_path, "PNG")
print(f"✅ icon.png 생성됨 ({SIZE}x{SIZE}) — {output_path}")
