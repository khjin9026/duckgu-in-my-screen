# -*- coding: utf-8 -*-
"""
도형 기반 데스크탑 펫 (오리 — 캐릭터명 "아리")
- 이미지 파일 없이 QPainter로만 그림
- 항상 다른 창 위에 떠 있고 배경은 투명
- 화면 하단을 좌우로 아장아장 걸어다님
"""

import sys
import math
import random
import json
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMenu, QAction, QSystemTrayIcon,
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTimeEdit, QPushButton, QCheckBox,
    QAbstractSpinBox,
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QRectF, QTime
from PyQt5.QtGui import (
    QPainter, QColor, QBrush, QPen, QCursor,
    QPainterPath, QRadialGradient, QPixmap, QIcon,
)


class MemoNote(QWidget):
    """포스트잇 스타일 메모 — 스케줄 알림 시 화면 가운데에 톡 등장.
    클릭해야 사라짐 — 사용자 주목 강제."""

    WIDTH = 240
    HEIGHT = 160

    def __init__(self, message, screen_x, screen_y):
        super().__init__()
        self.message = message
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(self.WIDTH, self.HEIGHT)
        # (screen_x, screen_y) 를 중심으로 배치
        self.move(screen_x - self.WIDTH // 2, screen_y - self.HEIGHT // 2)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 그림자 (살짝 아래쪽으로 오프셋)
        painter.setBrush(QBrush(QColor(0, 0, 0, 55)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(10, 14, self.WIDTH - 16, self.HEIGHT - 22), 4, 4)

        # 포스트잇 본체 (노란색)
        painter.setBrush(QBrush(QColor(255, 230, 110)))
        painter.setPen(QPen(QColor(225, 190, 70), 1))
        painter.drawRoundedRect(QRectF(6, 10, self.WIDTH - 16, self.HEIGHT - 22), 3, 3)

        # 위에 테이프 모양 (반투명 흰색)
        tape_x = self.WIDTH // 2 - 35
        painter.setBrush(QBrush(QColor(255, 250, 220, 190)))
        painter.setPen(QPen(QColor(220, 210, 170, 120), 0.8))
        painter.drawRect(QRectF(tape_x, 2, 70, 14))

        # 메시지 텍스트 (가운데 정렬, 굵은 글씨)
        painter.setPen(QColor(60, 50, 20))
        font = painter.font()
        font.setPointSize(15)
        font.setBold(True)
        painter.setFont(font)
        text_rect = QRectF(20, 32, self.WIDTH - 40, self.HEIGHT - 70)
        painter.drawText(
            text_rect,
            int(Qt.AlignCenter | Qt.TextWordWrap),
            self.message,
        )

        # 하단 힌트 (작게)
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(140, 110, 50, 200))
        hint_rect = QRectF(0, self.HEIGHT - 30, self.WIDTH - 10, 16)
        painter.drawText(hint_rect, int(Qt.AlignCenter), "클릭해서 닫기")

    def mousePressEvent(self, event):
        """클릭하면 닫힘."""
        self.close()


class SettingsDialog(QDialog):
    """덕구 설정 다이얼로그 — 시간별 알림 메시지를 최대 5개까지 편집.

    각 행: 시간(HH:mm) + 메시지(빈칸이면 비활성).
    저장/취소 버튼으로 결과 반영.
    """

    MAX_SCHEDULES = 5

    def __init__(self, parent, schedules):
        super().__init__(parent)
        self.setWindowTitle("덕구 설정")
        self.setMinimumWidth(460)

        # 원본 변경 방지를 위해 복사
        existing = [dict(s) for s in schedules]
        # 5개로 패딩 (빈 슬롯은 메모 체크 OFF 기본값)
        while len(existing) < self.MAX_SCHEDULES:
            existing.append({"time": "12:00", "message": "", "use_memo": False, "last_fired": ""})
        self.schedules = existing[: self.MAX_SCHEDULES]

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("덕구 말풍선 설정")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel("메모 체크를 활성화하면 덕구가 포스트잇을 물어와요")
        hint.setStyleSheet("color: gray; font-size: 11px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 입력 그리드
        grid = QGridLayout()
        grid.setColumnStretch(2, 1)
        self.time_inputs = []
        self.message_inputs = []
        self.memo_checks = []
        for i, entry in enumerate(self.schedules):
            num_label = QLabel(f"{i + 1}.")
            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
            time_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)  # 화살표 제거
            t = QTime.fromString(entry.get("time", "12:00"), "HH:mm")
            if t.isValid():
                time_edit.setTime(t)
            msg_edit = QLineEdit(entry.get("message", ""))
            msg_edit.setPlaceholderText("메시지 (비어있으면 비활성)")
            msg_edit.setMaxLength(30)
            memo_check = QCheckBox("메모")
            memo_check.setChecked(entry.get("use_memo", True))
            memo_check.setToolTip(
                "체크 : 펫이 포스트잇 들고 화면 가운데로 배달\n"
                "해제 : 펫 위치 그대로 말풍선만 표시"
            )

            grid.addWidget(num_label, i, 0)
            grid.addWidget(time_edit, i, 1)
            grid.addWidget(msg_edit, i, 2)
            grid.addWidget(memo_check, i, 3)
            self.time_inputs.append(time_edit)
            self.message_inputs.append(msg_edit)
            self.memo_checks.append(memo_check)
        layout.addLayout(grid)

        # 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("저장")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_schedules(self):
        """다이얼로그 현재 상태를 schedule 리스트로 반환."""
        result = []
        for time_edit, msg_edit, memo_check in zip(
            self.time_inputs, self.message_inputs, self.memo_checks
        ):
            time_str = time_edit.time().toString("HH:mm")
            msg = msg_edit.text().strip()
            use_memo = memo_check.isChecked()
            result.append({
                "time": time_str,
                "message": msg,
                "use_memo": use_memo,
                "last_fired": "",
            })
        return result


class FoodItem(QWidget):
    """데스크탑에 떨어뜨려놓는 작은 먹이(빵) 위젯.
    펫이 발견하면 그쪽으로 걸어가서 먹고 사라짐."""

    SIZE = 24   # 위젯 전체 크기 (px)

    def __init__(self, screen_x, screen_y):
        super().__init__()
        # 클릭 통과 + 항상 위 + 테두리 없음 (펫과 동일한 류의 윈도우)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.resize(self.SIZE, self.SIZE)
        # 입력으로 받은 (screen_x, screen_y) 는 먹이 "중심" 화면 좌표
        self.move(screen_x - self.SIZE // 2, screen_y - self.SIZE // 2)
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 빵 — 둥근 갈색 원
        painter.setPen(QPen(QColor(140, 90, 35), 1.2))
        painter.setBrush(QBrush(QColor(210, 155, 85)))
        painter.drawEllipse(3, 3, 18, 18)
        # 작은 디테일 — 빵 표면 점 2개로 질감
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(140, 90, 35, 120)))
        painter.drawEllipse(8, 7, 2, 2)
        painter.drawEllipse(13, 12, 2, 2)


class DesktopPet(QWidget):
    """도형으로 그린 데스크탑 펫(오리, 캐릭터명 "아리") 클래스."""

    def __init__(self):
        super().__init__()

        # ===========================================================
        # 1) 윈도우 기본 설정 (투명 / 항상 위 / 테두리 없음)
        # ===========================================================
        # FramelessWindowHint: 창 테두리/타이틀바 제거
        # WindowStaysOnTopHint: 다른 모든 창 위에 항상 표시
        # ※ Qt.Tool 은 macOS에서 다른 앱 클릭 시 자동 숨김 부작용 있어서 제외
        #   (대신 main에서 NSApp Accessory 모드로 Dock 아이콘 숨김 처리)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        # 배경을 완전히 투명하게 → 그린 도형만 화면에 보이게 됨
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 캐릭터를 그릴 캔버스(=윈도우) 크기
        # height를 캐릭터 키보다 넉넉히 잡아서 점프 시 머리가 잘리지 않게 함.
        # (윈도우 배경이 투명이라 빈 공간은 화면에 보이지 않음)
        self.pet_width = 100
        self.pet_height = 180
        self.resize(self.pet_width, self.pet_height)

        # 멀티 디스플레이 지원: 모든 모니터를 합친 "가상 데스크탑" 영역
        # 좌표는 가상 좌표 — 주 모니터 왼쪽에 있는 보조 모니터면 음수 x도 가능
        self.virtual_rect = self._compute_virtual_rect()
        # 호환용 (구 코드가 쓰던 width/height — 이제 가상 데스크탑 크기)
        self.screen_width = self.virtual_rect.width()
        self.screen_height = self.virtual_rect.height()

        # 시작 위치 + 집(go home) 기준: 주 디스플레이 가운데 하단
        primary = QApplication.primaryScreen().geometry()
        self.ground_y = primary.y() + primary.height() - self.pet_height - 60
        start_x = primary.x() + primary.width() // 2
        self.move(start_x, self.ground_y)

        # ===========================================================
        # 2) 동작/애니메이션 상태 변수
        # ===========================================================
        self.direction = 1            # 1: 오른쪽, -1: 왼쪽
        self.walk_speed = 2           # 한 프레임당 이동 픽셀
        self.bounce_phase = 0.0       # 바운스 sin 위상
        self.bounce_offset = 0        # 현재 바운스 y 오프셋(픽셀)

        # 눈 깜빡 상태
        self.is_blinking = False
        self.blink_timer = 0          # 남은 깜빡 프레임

        # 점프 상태 (간단한 중력 시뮬레이션)
        self.is_jumping = False
        self.jump_velocity = 0        # 음수 = 위로
        self.jump_offset = 0          # 현재 점프 y 오프셋

        # 멈춤 상태 (랜덤 이벤트 동안 잠시 정지)
        self.is_idle = False
        self.idle_timer = 0

        # 두리번 (멈춰있을 때 머리만 좌우로 까딱)
        self.is_looking_around = False
        self.look_timer = 0
        self.head_tilt = 0            # 머리/눈/부리에 적용할 좌우 픽셀 오프셋

        # 쪼기 (peck): 화면 끝에 닿으면 잠깐 옆모습으로 벽을 쪼다가 돌아섬
        self.is_at_wall = False
        self.wall_timer = 0
        self.wall_facing = 0          # -1=왼쪽 벽, +1=오른쪽 벽 보고 있음

        # 갸우뚱 (head tilt): 멈춰서 머리 각도를 좌우로 회전 (QPainter rotate)
        self.is_tilting = False
        self.tilt_timer = 0
        self.tilt_angle = 0.0         # 도(degree) 단위, 양수=시계방향

        # 말풍선 (다른 동작 위에 오버레이로 잠깐 떴다 사라짐)
        self.is_speaking = False
        self.speech_text = ""
        self.speech_timer = 0         # 남은 표시 프레임

        # 우다다 (랜덤하게 잠깐 빠르게 뛰어다님)
        self.is_running = False
        self.run_timer = 0            # 남은 우다다 프레임

        # 그림자 y 오프셋: 걸을/뛸 때 발이 그림자 윗쪽에 머무르도록 살짝 아래로 내림
        # 0(가만)~3(걷기)~5(우다다) 사이에서 부드럽게 보간됨
        self.shadow_y_offset = 0.0

        # 마우스 커서 따라가기/도망가기
        self.last_cursor_pos = None       # 이전 프레임 커서 위치 (속도 계산용)
        self.cursor_mode = "normal"       # "normal" / "follow" / "escape" / "stare"
        self.cursor_ignore_timer = 0      # 벽 부딪힌 직후 잠시 커서 무시 (피드백 루프 방지)
        self.follow_mode_enabled = False  # 메뉴 토글로 ON/OFF. 기본은 OFF

        # 자유 산책 (2D 랜덤 목적지)
        # wander_target_x, _y 는 펫 "중심"의 목표 화면 좌표 (가상 데스크탑 좌표)
        self.wander_target_x = primary.x() + primary.width() // 2
        self.wander_target_y = self.ground_y + self.pet_height // 2
        self.wander_target_timer = 0      # 0이면 다음 프레임에 새 목적지 픽

        # 집 위치 ("집으로 보내기" 했을 때 가는 좌표) — 주 디스플레이 왼쪽 구석
        # 펫 "중심"이 좌측 80px 지점에 가게 → 펫 좌상단은 30px 안쪽 (살짝 끝에 붙음)
        self.home_x = primary.x() + 80
        self.home_y = self.ground_y + self.pet_height // 2
        self.is_going_home = False
        self.is_napping_at_home = False   # 집 도착 후 영구 잠 상태 (클릭으로만 깨움)

        # 더블클릭 → 좋아함 반응 (작은 점프 + 머리 위 ♥ 파티클)
        self.is_happy = False
        self.happy_timer = 0
        self.heart_phase = 0.0

        # 먹이 주기 — 데스크탑에 떨어뜨려놓은 FoodItem 위젯들
        self.food_items = []

        # 커서 잡기 — 2단계: stalking(슬금슬금) → snatch(잡아채기 + ride)
        self.is_stalking_cursor = False
        self.stalking_timer = 0
        self.is_riding_cursor = False
        self.riding_timer = 0

        # 캐릭터 선택 — "ducku" (오리, 기본) 또는 "chick" (병아리)
        # _load_settings 에서 덮어쓸 수 있음
        self.current_character = "ducku"

        # 사용자 설정 스케줄 (시간별 알림 메시지, 최대 5개)
        self.schedules = []
        self._load_settings()
        # 현재 표시 중인 포스트잇 메모 (하나씩만 — 새로 뜨면 이전 거 닫음)
        self.active_memo = None

        # 메모 배달 상태 — 펫이 메모를 입에 물고 목적지로 비행
        self.delivering_memo = False
        self.delivery_target_x = 0
        self.delivery_target_y = 0
        self.pending_memo_message = ""
        # ride 시작될 때 picking — 펫이 커서 끌고 갈 목표 좌표
        self._riding_target_x = 0.0
        self._riding_target_y = 0.0

        # 낮잠 (긴 시간 정지 + 눈 감기 + ZZZ + 호흡 애니메이션)
        self.is_sleeping = False
        self.sleep_timer = 0
        self.zzz_phase = 0.0          # 머리 위 ZZZ 떠오름 위상 (0~1 순환)
        self.breathing_phase = 0.0    # 호흡 sin 위상

        # 호버(볼 발그레)와 드래그 상태
        self.is_hovered = False
        self.is_dragging = False
        self.drag_position = QPoint()

        # 들어올리기 효과: 드래그 중일 때 캐릭터만 위로 떠오르는 오프셋
        # 0 → 20 까지 부드럽게 lerp(보간) → 슉 떠올랐다가 놓으면 슉 내려옴
        self.lift_offset = 0.0

        # ===========================================================
        # 3) 타이머: 메인 애니메이션 루프 (걷기/바운스/그리기)
        # ===========================================================
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(30)  # 30ms 간격 ≈ 33 FPS

        # ===========================================================
        # 4) 타이머: 5~10초마다 랜덤 이벤트(깜빡 or 점프)
        # ===========================================================
        self.event_timer = QTimer(self)
        self.event_timer.timeout.connect(self.trigger_random_event)
        self.schedule_next_event()

        self.show()

        # 윈도우가 실제로 생성된 다음에 macOS 전용 동작 설정
        # → 모든 Space(데스크탑/풀스크린 앱 위)에서 펫이 보이게 함
        if sys.platform == "darwin":
            self._make_visible_on_all_spaces()

        # 첫 자유 산책 목적지 픽 + 메뉴바 트레이 아이콘 셋업
        self._pick_new_wander_target()
        self._setup_tray_icon()

        # 설정 스케줄 체크 타이머 (30초마다 시간 일치 확인)
        self.schedule_check_timer = QTimer(self)
        self.schedule_check_timer.timeout.connect(self._check_schedules)
        self.schedule_check_timer.start(30_000)

    def _make_visible_on_all_spaces(self):
        """
        macOS 전용: 펫 윈도우가 모든 Mission Control Space에 표시되도록 설정.
        - CanJoinAllSpaces: Space를 전환해도 모든 화면에 같이 나타남
        - Stationary: Space 전환 애니메이션 때 같이 슬라이드하지 않고 그 자리에 고정
        - FullScreenAuxiliary: 다른 앱이 풀스크린일 때도 펫이 위에 떠 있음
        pyobjc 가 설치되어 있어야 동작. 미설치 시 조용히 무시.
        """
        try:
            from AppKit import (
                NSApp,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorStationary,
                NSWindowCollectionBehaviorFullScreenAuxiliary,
            )
            behavior = (
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorStationary
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            # Accessory 모드라 윈도우는 펫 하나뿐 → 전부 같은 동작 적용
            for window in NSApp.windows():
                window.setCollectionBehavior_(behavior)
        except ImportError:
            # pyobjc 미설치 — Space 이동 시 펫이 따라오지 않을 수 있음
            pass

    # ===============================================================
    # 랜덤 이벤트 로직
    # ===============================================================
    def schedule_next_event(self):
        """다음 랜덤 이벤트까지의 대기 시간을 5~10초 사이로 다시 설정."""
        interval = random.randint(5000, 10000)  # 단위: ms
        self.event_timer.start(interval)

    def trigger_random_event(self):
        """5~10초마다 호출 → 가중치 기반으로 동작 중 하나 무작위 선택."""
        # 이미 진행 중인 긴 동작 또는 집으로 가는 중이면 새 이벤트는 건너뜀
        # (자던/쪼던/갸우뚱하던 도중 깜빡 같은 새 이벤트가 끼어드는 걸 방지)
        if (
            self.is_sleeping
            or self.is_looking_around
            or self.is_jumping
            or self.is_at_wall
            or self.is_tilting
            or self.is_going_home
            or self.delivering_memo
        ):
            self.schedule_next_event()
            return

        # follow 모드일 땐 펫이 커서에 도착한 상태(stare) 일 때만 이벤트 발생
        # (커서 쫓아가는 중엔 따라가기에만 집중)
        if self.follow_mode_enabled and self.cursor_mode != "stare":
            self.schedule_next_event()
            return

        # 말풍선: 20% 확률로 한 마디 (두 모드 다 작동)
        # "심심해" → stalking 은 follow_mode OFF 일 때만
        if not self.is_speaking and random.random() < 0.2:
            self.is_speaking = True
            self.speech_text = random.choice(["배고파", "심심해"])
            self.speech_timer = 90
            if self.speech_text == "심심해" and not self.follow_mode_enabled:
                self._maybe_start_stalking()

        # 랜덤 이벤트 선택 — follow_mode 면 자리 안 옮기는 idle 만 허용
        # (jump/run 은 자리 이동하므로 제외. sleep 은 OK — 커서 움직이면 자동 기상)
        if self.follow_mode_enabled:
            event = random.choices(
                ["blink", "look_around", "tilt", "sleep"],
                weights=[3, 3, 2, 2],
            )[0]
        else:
            event = random.choices(
                ["blink", "jump", "look_around", "sleep", "run", "tilt"],
                weights=[3, 2, 3, 1, 2, 2],
            )[0]

        if event == "blink":
            self.is_idle = True
            self.idle_timer = 25
            self.is_blinking = True
            self.blink_timer = 8

        elif event == "jump":
            self.is_idle = True
            self.idle_timer = 25
            self.is_jumping = True
            self.jump_velocity = -9

        elif event == "look_around":
            # 90프레임(약 2.7초) 동안 멈춰서 머리만 좌우로 까딱 (3번)
            self.is_looking_around = True
            self.look_timer = 90

        elif event == "sleep":
            # 4.5~9초간 잠. 시작 시 ZZZ/호흡 위상 초기화
            self.is_sleeping = True
            self.sleep_timer = random.randint(150, 300)
            self.zzz_phase = 0.0
            self.breathing_phase = 0.0
            # 잠 들기 직전에 말풍선 뜨고 있던 거 있으면 즉시 제거
            self.is_speaking = False
            self.speech_text = ""
            self.speech_timer = 0

        elif event == "run":
            # 우다다 — 2~4초 동안 빠르게 뛰어다님 (속도/바운스 증가)
            self.is_running = True
            self.run_timer = random.randint(60, 120)

        elif event == "tilt":
            # 갸우뚱 — 2.3초 동안 멈춰서 머리만 좌→우→좌 회전 (Figma Section 3)
            self.is_tilting = True
            self.tilt_timer = 75

        # 다음 이벤트 다시 예약
        self.schedule_next_event()

    # ===============================================================
    # 매 프레임 호출되는 메인 업데이트
    # ===============================================================
    def update_animation(self):
        """걷기/바운스/점프/깜빡 상태를 1프레임만큼 진행하고 다시 그린다."""
        # 들어올리기(lift_offset)는 드래그 여부와 무관하게 항상 부드럽게 보간
        # 드래그 중이면 20을 향해 ↑, 떼면 0을 향해 ↓ → "슉" 떴다 내려앉는 느낌
        target_lift = 20.0 if self.is_dragging else 0.0
        self.lift_offset += (target_lift - self.lift_offset) * 0.35

        # 드래그 중이면 위치는 마우스가 결정 → 자동 이동 스킵 (단, 그림 다시 그리기 위해 update)
        if self.is_dragging:
            self.update()
            return

        # 멈춤 타이머 감소
        if self.is_idle:
            self.idle_timer -= 1
            if self.idle_timer <= 0:
                self.is_idle = False

        # 눈 깜빡 타이머 감소
        if self.is_blinking:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = False

        # 점프(중력) 처리: 매 프레임 속도에 +1 → 포물선 운동
        if self.is_jumping:
            self.jump_offset += self.jump_velocity
            self.jump_velocity += 1   # 중력 가속도
            if self.jump_offset >= 0: # 바닥에 다시 닿으면 종료
                self.jump_offset = 0
                self.is_jumping = False
                self.jump_velocity = 0

        # head_tilt(머리 좌우 픽셀 오프셋)는 여러 동작이 공유.
        # 우선순위: 쪼기(벽) > 두리번 > 그 외(0)
        if self.is_at_wall:
            # 쪼기: 머리가 벽 쪽으로 살짝 기운 채 1.5주기 동안 좌우로 흔들
            self.wall_timer -= 1
            progress = 1.0 - (self.wall_timer / 60.0)
            self.head_tilt = int(
                2 * self.wall_facing
                + math.sin(progress * 3 * math.pi) * 2
            )
            if self.wall_timer <= 0:
                self.is_at_wall = False
                self.direction = -self.wall_facing  # 반대 방향으로 돌아섬
                self.head_tilt = 0
        elif self.is_looking_around:
            # 두리번: sin(3π·진행도) → 우→좌→우 3번 까딱 (1.5주기)
            self.look_timer -= 1
            progress = 1.0 - (self.look_timer / 90.0)
            self.head_tilt = int(math.sin(progress * 3 * math.pi) * 4)
            if self.look_timer <= 0:
                self.is_looking_around = False
                self.head_tilt = 0
        else:
            # 그 외엔 머리 정중앙
            self.head_tilt = 0

        # 낮잠 처리: 타이머 카운트다운 + ZZZ 떠오름 위상 + 호흡 위상
        if self.is_sleeping:
            self.sleep_timer -= 1
            self.zzz_phase = (self.zzz_phase + 0.012) % 1.0   # 천천히 순환
            self.breathing_phase += 0.05                      # 호흡 sin 위상
            if self.sleep_timer <= 0:
                self.is_sleeping = False

            # follow 모드에선 잠자는 중 커서가 50px 이상 움직이면 자동 기상
            # (커서 따라가야 하므로 — 집잠 napping_at_home 은 예외)
            if (self.is_sleeping
                    and self.follow_mode_enabled
                    and not self.is_napping_at_home
                    and self.last_cursor_pos is not None):
                cursor_now = QCursor.pos()
                moved = math.sqrt(
                    (cursor_now.x() - self.last_cursor_pos.x()) ** 2
                    + (cursor_now.y() - self.last_cursor_pos.y()) ** 2
                )
                if moved > 50:
                    self._wake_up_if_sleeping(force=False)

        # 말풍선 표시 타이머
        if self.is_speaking:
            self.speech_timer -= 1
            if self.speech_timer <= 0:
                self.is_speaking = False
                self.speech_text = ""

        # 우다다 타이머
        if self.is_running:
            self.run_timer -= 1
            if self.run_timer <= 0:
                self.is_running = False

        # 좋아함(더블클릭) 타이머 + ♥ 위상
        if self.is_happy:
            self.happy_timer -= 1
            self.heart_phase = (self.heart_phase + 0.015) % 1.0
            if self.happy_timer <= 0:
                self.is_happy = False
                self.heart_phase = 0.0

        # 갸우뚱 타이머 + 각도 애니메이션 (sin 곡선: 0 → +12 → 0 → -12 → 0)
        if self.is_tilting:
            self.tilt_timer -= 1
            progress = 1.0 - (self.tilt_timer / 75.0)
            self.tilt_angle = math.sin(progress * 2 * math.pi) * 12.0
            if self.tilt_timer <= 0:
                self.is_tilting = False
                self.tilt_angle = 0.0

        # 커서 무시 타이머 (벽 끝난 직후 잠깐 커서 무시 → 같은 벽으로 끌려가는 거 방지)
        if self.cursor_ignore_timer > 0:
            self.cursor_ignore_timer -= 1

        # === Stalking: 슬금슬금 커서 다가가기 ===
        if self.is_stalking_cursor:
            self.stalking_timer -= 1
            cursor = QCursor.pos()
            pet_cx = self.x() + self.pet_width // 2
            pet_cy = self.y() + self.pet_height // 2
            dx = cursor.x() - pet_cx
            dy = cursor.y() - pet_cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist < 35:
                # 가까이 왔다 — 잡아채기! (snatch + ride 시작)
                self._snatch_cursor()
                # 아래 riding 핸들러로 이번 프레임 그대로 흘러감
            elif self.stalking_timer <= 0 or dist > 600:
                # 못 잡았다 — 포기
                self.is_stalking_cursor = False
            else:
                # 슬금슬금 다가가기 — 느린 속도
                speed = 1.5
                dx_step = dx / max(dist, 0.1) * speed
                dy_step = dy / max(dist, 0.1) * speed
                if abs(dx_step) > 0.3:
                    self.direction = 1 if dx_step > 0 else -1
                vl = self.virtual_rect.x()
                vt = self.virtual_rect.y()
                vr = vl + self.virtual_rect.width()
                vb = vt + self.virtual_rect.height()
                new_x = max(vl, min(self.x() + dx_step, vr - self.pet_width))
                new_y = max(vt, min(self.y() + dy_step, vb - self.pet_height))
                self.move(int(new_x), int(new_y))
                # 천천히 바운스
                total = math.sqrt(dx_step * dx_step + dy_step * dy_step)
                if total > 0.3:
                    self.bounce_phase += 0.25
                    self.bounce_offset = int(abs(math.sin(self.bounce_phase)) * 4)
                self.update()
                return

        # === Riding: 잡아챈 커서를 끌고 도망가기 ===
        if self.is_riding_cursor:
            self.riding_timer -= 1
            if self.riding_timer <= 0:
                # 시간 끝 — 작은 점프로 커서 놓고 떨어짐 + "헤헤 재밌당" 멘트
                self.is_riding_cursor = False
                self.is_jumping = True
                self.jump_velocity = -7
                self.jump_offset = 0
                self.is_speaking = True
                self.speech_text = "헤헤 재밌당"
                self.speech_timer = 90
            else:
                # 목표 지점으로 빠르게 이동
                pet_cx = self.x() + self.pet_width // 2
                pet_cy = self.y() + self.pet_height // 2
                dx = self._riding_target_x - pet_cx
                dy = self._riding_target_y - pet_cy
                dist = math.sqrt(dx * dx + dy * dy)
                # 도착했으면 새 목적지 픽 → 계속 zigzag (떨림 방지)
                if dist < 30:
                    self._pick_riding_target(pet_cx, pet_cy)
                    dx = self._riding_target_x - pet_cx
                    dy = self._riding_target_y - pet_cy
                    dist = math.sqrt(dx * dx + dy * dy)
                dist = max(dist, 0.1)
                speed = 7
                dx_step = dx / dist * speed
                dy_step = dy / dist * speed
                # 오버슈트 방지 — 남은 거리보다 더 멀리 안 가게
                if abs(dx_step) > abs(dx):
                    dx_step = dx
                if abs(dy_step) > abs(dy):
                    dy_step = dy
                if abs(dx_step) > 0.3:
                    self.direction = 1 if dx_step > 0 else -1
                vl = self.virtual_rect.x()
                vt = self.virtual_rect.y()
                vr = vl + self.virtual_rect.width()
                vb = vt + self.virtual_rect.height()
                new_x = max(vl, min(self.x() + dx_step, vr - self.pet_width))
                new_y = max(vt, min(self.y() + dy_step, vb - self.pet_height))
                self.move(int(new_x), int(new_y))
                # 시스템 커서를 펫 부리 위치로 끌고 옴
                beak_window_y = self.pet_height - 71
                beak_screen_x = int(new_x) + self.pet_width // 2
                beak_screen_y = int(new_y) + beak_window_y
                self._move_system_cursor(beak_screen_x, beak_screen_y)
                # 빠르게 바운스
                total = math.sqrt(dx_step * dx_step + dy_step * dy_step)
                if total > 0.5:
                    self.bounce_phase += 0.55
                    self.bounce_offset = int(abs(math.sin(self.bounce_phase)) * 8)
                self.update()
                return

        # 걷기 멈춤 조건: 짧은 idle / 두리번 / 낮잠 / 쪼기 / 갸우뚱 중 하나라도 활성이면 정지
        is_paused = (
            self.is_idle
            or self.is_looking_around
            or self.is_sleeping
            or self.is_at_wall
            or self.is_tilting
        )

        if not is_paused:
            # 마우스 커서 반응 체크 → cursor_mode 결정
            self._update_cursor_reaction()

            # 이동 벡터(dx_step, dy_step) 결정
            # 우선순위: 메모 배달 > 집으로 보내기 > 커서 반응 > 자유 산책
            dx_step = 0.0
            dy_step = 0.0
            pet_cx = self.x() + self.pet_width // 2
            pet_cy = self.y() + self.pet_height // 2

            if self.delivering_memo:
                # 메모를 부리에 물고 목적지로 비행
                tdx = self.delivery_target_x - pet_cx
                tdy = self.delivery_target_y - pet_cy
                dist = math.sqrt(tdx * tdx + tdy * tdy)
                if dist < 30:
                    # 도착 — 메모 떨궈놓기
                    self._drop_memo()
                    dx_step = 0
                    dy_step = 0
                else:
                    speed = 5.0
                    dx_step = tdx / dist * speed
                    dy_step = tdy / dist * speed
            elif self.is_going_home:
                # 집으로 비행 — 어떤 상태든 override
                tdx = self.home_x - pet_cx
                tdy = self.home_y - pet_cy
                dist = math.sqrt(tdx * tdx + tdy * tdy)
                if dist < 8:
                    # 집 도착 → 영구 잠 모드 진입 (클릭으로만 깸)
                    self.is_going_home = False
                    self.is_sleeping = True
                    self.is_napping_at_home = True
                    self.sleep_timer = 10_000_000   # 매우 큰 수 (사실상 무한)
                    self.zzz_phase = 0.0
                    self.breathing_phase = 0.0
                    dx_step = 0
                    dy_step = 0
                else:
                    speed = 4.5
                    dx_step = tdx / dist * speed
                    dy_step = tdy / dist * speed
            elif self.cursor_mode == "follow" or self.cursor_mode == "stare":
                # follow/stare 중에도 먹이가 있으면 먹이를 우선 (먹고 나서 커서로 복귀)
                if self.food_items:
                    nearest = min(
                        self.food_items,
                        key=lambda f: (f.x() + f.width() // 2 - pet_cx) ** 2
                        + (f.y() + f.height() // 2 - pet_cy) ** 2,
                    )
                    target_x = nearest.x() + nearest.width() // 2
                    target_y = nearest.y() + nearest.height() // 2
                    tdx = target_x - pet_cx
                    tdy = target_y - pet_cy
                    tdist = math.sqrt(tdx * tdx + tdy * tdy)
                    if tdist < 20:
                        self._eat_food(nearest)
                        dx_step = 0
                        dy_step = 0
                    else:
                        speed = 2.5
                        dx_step = tdx / max(tdist, 0.1) * speed
                        dy_step = tdy / max(tdist, 0.1) * speed
                elif self.cursor_mode == "follow":
                    cursor = QCursor.pos()
                    dxc = cursor.x() - pet_cx
                    dyc = cursor.y() - pet_cy
                    dist = max(math.sqrt(dxc * dxc + dyc * dyc), 0.1)
                    speed = 2.5
                    dx_step = dxc / dist * speed
                    dy_step = dyc / dist * speed
                else:  # stare — 커서 옆에 가만히 떠 있음 (먼지 없을 때)
                    dx_step = 0.0
                    dy_step = 0.0
            elif self.cursor_mode == "escape":
                cursor = QCursor.pos()
                dxc = cursor.x() - pet_cx
                dyc = cursor.y() - pet_cy
                dist = max(math.sqrt(dxc * dxc + dyc * dyc), 0.1)
                speed = 5.0
                dx_step = -dxc / dist * speed
                dy_step = -dyc / dist * speed
            else:  # "normal" — 자유 2D 산책 (먹이 있으면 그쪽으로 우선)
                # 먹이가 있으면 가장 가까운 빵으로 향함
                if self.food_items:
                    nearest = min(
                        self.food_items,
                        key=lambda f: (f.x() + f.width() // 2 - pet_cx) ** 2
                        + (f.y() + f.height() // 2 - pet_cy) ** 2,
                    )
                    target_x = nearest.x() + nearest.width() // 2
                    target_y = nearest.y() + nearest.height() // 2
                    tdx = target_x - pet_cx
                    tdy = target_y - pet_cy
                    tdist = math.sqrt(tdx * tdx + tdy * tdy)
                    if tdist < 20:
                        # 빵에 도착 → 먹기
                        self._eat_food(nearest)
                        dx_step = 0
                        dy_step = 0
                    else:
                        speed = 4 if self.is_running else self.walk_speed
                        dx_step = tdx / max(tdist, 0.1) * speed
                        dy_step = tdy / max(tdist, 0.1) * speed
                else:
                    # 평소 산책 — 랜덤 목적지로
                    self.wander_target_timer -= 1
                    tdx = self.wander_target_x - pet_cx
                    tdy = self.wander_target_y - pet_cy
                    tdist = math.sqrt(tdx * tdx + tdy * tdy)
                    if self.wander_target_timer <= 0 or tdist < 25:
                        self._pick_new_wander_target()
                        tdx = self.wander_target_x - pet_cx
                        tdy = self.wander_target_y - pet_cy
                        tdist = max(math.sqrt(tdx * tdx + tdy * tdy), 0.1)
                    else:
                        tdist = max(tdist, 0.1)
                    speed = 4 if self.is_running else self.walk_speed
                    dx_step = tdx / tdist * speed
                    dy_step = tdy / tdist * speed

            # 진행 방향(facing) 갱신: 의미 있게 좌우 이동할 때만
            if abs(dx_step) > 0.3:
                self.direction = 1 if dx_step > 0 else -1

            # 새 위치 계산
            new_x = self.x() + dx_step
            new_y = self.y() + dy_step

            # 가상 데스크탑 경계 (모든 모니터 합친 영역) 기준 클램프
            vleft = self.virtual_rect.x()
            vtop = self.virtual_rect.y()
            vright = vleft + self.virtual_rect.width()
            vbottom = vtop + self.virtual_rect.height()

            # 좌우 벽 충돌 (쪼기 트리거는 평소 모드일 때만 — 도망/따라갈 땐 그냥 클램프)
            hit_h_wall = False
            if new_x <= vleft:
                new_x = vleft
                hit_h_wall = True
                wall_dir = -1
            elif new_x + self.pet_width >= vright:
                new_x = vright - self.pet_width
                hit_h_wall = True
                wall_dir = 1

            if hit_h_wall and self.cursor_mode == "normal" and not self.is_at_wall:
                self.is_at_wall = True
                self.wall_facing = wall_dir
                self.wall_timer = 60
                self.cursor_ignore_timer = 90

            # 상하 경계 클램프 (가상 데스크탑 위/아래로 나가지 않게)
            new_y = max(vtop, min(new_y, vbottom - self.pet_height))

            self.move(int(new_x), int(new_y))

            # 바운스: 좌우든 위아래든 의미 있게 움직일 때 발걸음 애니메이션
            # (수직으로만 이동할 때 바운스가 멈춰서 둥둥 떠 보이던 버그 수정)
            total_movement = math.sqrt(dx_step * dx_step + dy_step * dy_step)
            if total_movement > 0.5:
                bounce_step = 0.5 if self.is_running else 0.35
                bounce_amp = 8 if self.is_running else 5
                self.bounce_phase += bounce_step
                self.bounce_offset = int(abs(math.sin(self.bounce_phase)) * bounce_amp)
            else:
                self.bounce_offset = 0
        else:
            # 멈춰있을 땐 바운스 없음
            self.bounce_offset = 0

        # 그림자 y 오프셋: 움직임 상태에 따라 부드럽게 보간
        # → 가만히 있을 땐 발이 그림자 위쪽, 움직일 땐 그림자가 살짝 더 아래로 가서
        #   바운스해도 발이 그림자 바닥에 안 닿음
        if self.is_running:
            target_shadow_offset = 5.0
        elif not is_paused:
            target_shadow_offset = 3.0
        else:
            target_shadow_offset = 0.0
        self.shadow_y_offset += (target_shadow_offset - self.shadow_y_offset) * 0.15

        # 화면 다시 그리기 요청 → paintEvent 호출됨
        self.update()

    # ===============================================================
    # 자유 산책 / 집으로 보내기
    # ===============================================================
    def _compute_virtual_rect(self):
        """모든 디스플레이를 합친 가상 데스크탑 rect 계산."""
        rect = QRect()
        for s in QApplication.screens():
            rect = rect.united(s.geometry())
        return rect

    def _pick_new_wander_target(self):
        """랜덤 디스플레이를 하나 골라 그 안에서 목적지 픽 — 모니터 사이 빈 공간은 피함."""
        screens = QApplication.screens()
        target_screen = random.choice(screens).geometry()
        half_w = self.pet_width // 2
        half_h = self.pet_height // 2
        margin = 20
        self.wander_target_x = random.randint(
            target_screen.x() + half_w + margin,
            target_screen.x() + target_screen.width() - half_w - margin,
        )
        self.wander_target_y = random.randint(
            target_screen.y() + half_h + margin,
            target_screen.y() + target_screen.height() - half_h - margin,
        )
        # 5~15초 후 다음 목적지 또 픽 (그 전에 도착하면 더 빠르게 새 목적지)
        self.wander_target_timer = random.randint(150, 450)

    def toggle_follow_mode(self):
        """커서 따라다니기 모드 ON/OFF 토글. 메뉴 액션들의 체크 상태도 동기화."""
        self.follow_mode_enabled = not self.follow_mode_enabled
        # 트레이 메뉴 액션 체크 상태 갱신
        if hasattr(self, "tray_action_follow"):
            self.tray_action_follow.setChecked(self.follow_mode_enabled)
        # 끄는 경우 커서 무시 + cursor_mode 초기화
        if not self.follow_mode_enabled:
            self.cursor_mode = "normal"

    def go_home(self):
        """우클릭 메뉴/트레이에서 호출. 펫을 왼쪽 구석으로 슉 비행 → 도착 후 영구 잠.
        진행 중인 모든 동작(짧은 idle 포함) 완전 초기화해서 바로 집으로 가게 함."""
        self.is_going_home = True
        # 긴 동작들
        self.is_sleeping = False
        self.is_napping_at_home = False
        self.is_looking_around = False
        self.is_tilting = False
        self.is_at_wall = False
        self.is_speaking = False
        self.speech_text = ""
        # 짧은 동작들 (이거 안 지우면 끝날 때까지 기다리느라 "딴짓"하는 것처럼 보임)
        self.is_idle = False
        self.idle_timer = 0
        self.is_blinking = False
        self.blink_timer = 0
        self.is_jumping = False
        self.jump_offset = 0
        self.jump_velocity = 0
        self.is_running = False
        self.run_timer = 0
        # 각도/오프셋 리셋
        self.head_tilt = 0
        self.tilt_angle = 0.0

    # ===============================================================
    # 설정 (시간별 알림 스케줄)
    # ===============================================================
    def _settings_path(self):
        return os.path.expanduser("~/.desktop-pet-settings.json")

    def _load_settings(self):
        """JSON 파일에서 스케줄/캐릭터 설정 로드. 파일 없으면 기본값으로 시작."""
        path = self._settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.schedules = data.get("schedules", [])
                    self.current_character = data.get("character", "ducku")
                    # 이전 버전 호환 — "chick" 으로 저장돼 있던 경우 "bamti" 로 마이그
                    if self.current_character == "chick":
                        self.current_character = "bamti"
                    return
            except (json.JSONDecodeError, OSError):
                pass
        # 첫 실행 또는 에러 → 기본값
        self.current_character = "ducku"
        self.schedules = [
            {"time": "11:15", "message": "점심시간임! 가는 김에 나도 밥 좀 주고🍚", "use_memo": True, "last_fired": ""},
            {"time": "15:00", "message": "하 개졸려 집 가고싶다ㅜ", "use_memo": False, "last_fired": ""},
            {"time": "18:00", "message": "퇴근준비 ㄱㄱ", "use_memo": False, "last_fired": ""},
            {"time": "19:00", "message": "야근 하는거임?", "use_memo": False, "last_fired": ""},
        ]
        self._save_settings()

    def _save_settings(self):
        """현재 스케줄/캐릭터를 JSON 파일에 저장."""
        try:
            with open(self._settings_path(), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schedules": self.schedules,
                        "character": self.current_character,
                    },
                    f,
                    ensure_ascii=False, indent=2,
                )
        except OSError:
            pass

    def set_character(self, character):
        """캐릭터 변경 + 저장 + 트레이 메뉴 체크 동기화 + 즉시 다시 그리기."""
        self.current_character = character
        self._save_settings()
        # 트레이 메뉴 액션 체크 상태 동기화
        if hasattr(self, "tray_action_char_ducku"):
            self.tray_action_char_ducku.setChecked(character == "ducku")
        if hasattr(self, "tray_action_char_bamti"):
            self.tray_action_char_bamti.setChecked(character == "bamti")
        self.update()

    def _set_character_from_tray(self, character):
        """트레이에서 호출되는 wrapper — set_character 와 같음."""
        self.set_character(character)

    def _check_schedules(self):
        """30초마다 호출. 현재 시간이 스케줄과 일치하면 한 번 발동."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_hm = now.strftime("%H:%M")
        for entry in self.schedules:
            msg = entry.get("message", "").strip()
            if not msg:
                continue
            if entry.get("time") == current_hm and entry.get("last_fired") != today_str:
                use_memo = entry.get("use_memo", True)
                self._fire_scheduled_speech(msg, use_memo)
                entry["last_fired"] = today_str
                self._save_settings()
                break   # 같은 시각에 여러 개 겹치면 하나만 발동

    def _fire_scheduled_speech(self, message, use_memo=True):
        """스케줄 시간 도달 시 entry point — use_memo에 따라 포스트잇/말풍선 분기."""
        if use_memo:
            self._start_memo_delivery(message)
        else:
            self._fire_simple_speech(message)

    def _fire_simple_speech(self, message):
        """말풍선만 표시 (펫 위치 그대로). 자고 있으면 깨움, 숨김 해제."""
        if self.is_sleeping:
            self.is_sleeping = False
            self.is_napping_at_home = False
            self.sleep_timer = 0
        if not self.isVisible():
            self.show_pet()
        self.is_speaking = True
        self.speech_text = message
        self.speech_timer = 180   # 약 6초

    def _start_memo_delivery(self, message):
        """펫이 메모를 입에 물고 화면 가운데로 배달 시작."""
        # 진행 중이던 상태 모두 정리 (배달이 최우선)
        self.is_sleeping = False
        self.is_napping_at_home = False
        self.is_idle = False
        self.idle_timer = 0
        self.is_blinking = False
        self.blink_timer = 0
        self.is_looking_around = False
        self.is_tilting = False
        self.is_jumping = False
        self.jump_offset = 0
        self.jump_velocity = 0
        self.is_at_wall = False
        self.is_running = False
        self.is_stalking_cursor = False
        self.is_riding_cursor = False
        self.is_going_home = False
        self.head_tilt = 0
        self.tilt_angle = 0.0
        # 숨겨져 있으면 다시 보이게
        if not self.isVisible():
            self.show_pet()

        # 배달 목적지: 펫 현재 모니터의 가운데
        pet_cx = self.x() + self.pet_width // 2
        pet_cy = self.y() + self.pet_height // 2
        current_screen = None
        for screen in QApplication.screens():
            if screen.geometry().contains(pet_cx, pet_cy):
                current_screen = screen
                break
        if current_screen is None:
            current_screen = QApplication.primaryScreen()
        rect = current_screen.geometry()
        self.delivery_target_x = rect.x() + rect.width() // 2
        self.delivery_target_y = rect.y() + rect.height() // 2
        self.pending_memo_message = message
        self.delivering_memo = True

    def _drop_memo(self):
        """배달지 도착 — 메모 떨궈놓고 말풍선 표시."""
        msg = self.pending_memo_message or ""
        # 이전 메모 있으면 닫고 새로 띄움
        if self.active_memo is not None:
            try:
                self.active_memo.close()
            except Exception:
                pass
        self.active_memo = MemoNote(msg, self.delivery_target_x, self.delivery_target_y)
        if sys.platform == "darwin":
            self._make_visible_on_all_spaces()
        # 말풍선도 함께
        self.is_speaking = True
        self.speech_text = msg
        self.speech_timer = 180
        # 배달 상태 해제
        self.delivering_memo = False
        self.pending_memo_message = ""

    def show_settings(self):
        """메뉴에서 호출. 다이얼로그를 클릭 위치(커서) 근처에서 열고 결과 반영."""
        dlg = SettingsDialog(self, self.schedules)

        # 다이얼로그를 메뉴 클릭 위치 근처로 이동
        cursor_pos = QCursor.pos()
        size_hint = dlg.sizeHint()
        dlg_w = max(size_hint.width(), 460)
        dlg_h = max(size_hint.height(), 320)
        # 커서 우측 하단으로 살짝 오프셋
        target_x = cursor_pos.x() + 5
        target_y = cursor_pos.y() + 5
        # 화면 밖으로 나가지 않게 클램프 (커서가 속한 모니터 기준)
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                rect = screen.geometry()
                target_x = max(rect.x() + 10,
                               min(target_x, rect.x() + rect.width() - dlg_w - 10))
                target_y = max(rect.y() + 30,
                               min(target_y, rect.y() + rect.height() - dlg_h - 10))
                break
        dlg.move(target_x, target_y)

        if dlg.exec_() == QDialog.Accepted:
            new_schedules = dlg.get_schedules()
            # 같은 시간+메시지 항목은 last_fired 보존 (오늘 이미 떴으면 다시 안 뜨게)
            for new_entry in new_schedules:
                for old_entry in self.schedules:
                    if (old_entry.get("time") == new_entry["time"]
                            and old_entry.get("message") == new_entry["message"]):
                        new_entry["last_fired"] = old_entry.get("last_fired", "")
                        break
            self.schedules = new_schedules
            self._save_settings()

    # ===============================================================
    # 먹이 주기
    # ===============================================================
    def feed_pet(self):
        """메뉴에서 호출. 펫이 있는 같은 모니터 안, 적당한 거리에 빵을 떨어뜨림."""
        # 자고 있으면 먹기 위해 깨움
        self.is_sleeping = False
        self.is_napping_at_home = False

        pet_cx = self.x() + self.pet_width // 2
        pet_cy = self.y() + self.pet_height // 2

        # 펫이 현재 어느 모니터에 있는지 찾기 (못 찾으면 주 모니터로 폴백)
        current_screen = None
        for screen in QApplication.screens():
            if screen.geometry().contains(pet_cx, pet_cy):
                current_screen = screen
                break
        if current_screen is None:
            current_screen = QApplication.primaryScreen()
        rect = current_screen.geometry()

        # 펫 주변 100~400px 범위에서 화면 안에 들어가는 위치 찾기
        MIN_DIST = 100
        MAX_DIST = 400
        food_x = food_y = 0
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(MIN_DIST, MAX_DIST)
            food_x = int(pet_cx + math.cos(angle) * distance)
            food_y = int(pet_cy + math.sin(angle) * distance)
            # 화면 안에 들어가고 가장자리에서 적당히 떨어진 위치인지 확인
            if (rect.x() + 40 <= food_x <= rect.x() + rect.width() - 40
                    and rect.y() + 40 <= food_y <= rect.y() + rect.height() - 40):
                break
        else:
            # 20번 시도해도 못 찾으면 화면 가운데 근처로 폴백
            food_x = rect.x() + rect.width() // 2
            food_y = rect.y() + rect.height() // 2

        food = FoodItem(food_x, food_y)
        self.food_items.append(food)
        # 새 위젯도 모든 Space에서 보이게 + 위 레이어로
        if sys.platform == "darwin":
            self._make_visible_on_all_spaces()

    def _eat_food(self, food):
        """펫이 빵에 도착했을 때 — 빵 사라지고 행복한 반응."""
        food.close()
        if food in self.food_items:
            self.food_items.remove(food)
        # 멘트 (이미 말하고 있으면 덮어쓰지 않음)
        if not self.is_speaking:
            self.is_speaking = True
            self.speech_text = random.choice(["냠냠~", "맛있다!", "잘먹었어!", "꿀맛!"])
            self.speech_timer = 75
        # 행복한 작은 점프
        self.is_jumping = True
        self.jump_velocity = -6
        self.jump_offset = 0

    # ===============================================================
    # 커서 잡기 (riding cursor)
    # ===============================================================
    def _maybe_start_stalking(self):
        """심심해 말풍선 뜰 때 호출. 커서가 500px 이내면 stalking 시작."""
        if self.is_stalking_cursor or self.is_riding_cursor:
            return
        cursor = QCursor.pos()
        pet_cx = self.x() + self.pet_width // 2
        pet_cy = self.y() + self.pet_height // 2
        dist = math.sqrt((cursor.x() - pet_cx) ** 2 + (cursor.y() - pet_cy) ** 2)
        if dist > 500:
            return  # 커서 너무 멀면 그냥 심심해만 뜨고 끝
        self._begin_stalking(cursor, pet_cx)

    def force_cursor_catch(self):
        """메뉴에서 "장난치기" 누르면 거리 무관하게 stalking 시작 (수동 발동).
        '심심해' 말풍선도 같이 뜸. 따라다니기 모드 ON 일 땐 비활성."""
        if self.follow_mode_enabled:
            return
        if self.is_stalking_cursor or self.is_riding_cursor:
            return
        cursor = QCursor.pos()
        pet_cx = self.x() + self.pet_width // 2
        # 말풍선
        self.is_speaking = True
        self.speech_text = "심심해"
        self.speech_timer = 90
        self._begin_stalking(cursor, pet_cx)

    def _begin_stalking(self, cursor, pet_cx):
        """실제 stalking 상태로 진입. _maybe_start_stalking 와 force_cursor_catch 공통."""
        self.is_stalking_cursor = True
        self.stalking_timer = 240   # 약 8초 안에 잡아야 함
        # 진행 중인 짧은 동작 정리
        self.is_idle = False
        self.idle_timer = 0
        self.is_blinking = False
        self.blink_timer = 0
        # 커서 방향으로 facing
        self.direction = 1 if cursor.x() > pet_cx else -1

    def _snatch_cursor(self):
        """Stalking 끝, 커서 잡아채기. 펫이 랜덤 방향으로 도망가며 커서를 끌고 감."""
        self.is_stalking_cursor = False
        self.is_riding_cursor = True
        self.riding_timer = 90  # 약 2.7초 도망
        # 잡아채는 lunge 점프
        self.is_jumping = True
        self.jump_velocity = -8
        self.jump_offset = 0
        # 첫 목적지 픽
        pet_cx = self.x() + self.pet_width // 2
        pet_cy = self.y() + self.pet_height // 2
        self._pick_riding_target(pet_cx, pet_cy)

    def _pick_riding_target(self, from_x, from_y):
        """현재 위치에서 랜덤 방향으로 250~450px 떨어진 지점을 새 목적지로 설정.
        가상 데스크탑 경계 안에 들어가도록 클램프."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(250, 450)
        tx = from_x + math.cos(angle) * distance
        ty = from_y + math.sin(angle) * distance
        vl = self.virtual_rect.x()
        vt = self.virtual_rect.y()
        vr = vl + self.virtual_rect.width()
        vb = vt + self.virtual_rect.height()
        self._riding_target_x = max(vl + 100, min(tx, vr - 100))
        self._riding_target_y = max(vt + 100, min(ty, vb - 100))

    def _move_system_cursor(self, x, y):
        """시스템 커서를 (x, y) 로 이동. Quartz framework 필요."""
        if sys.platform != "darwin":
            return False
        try:
            from Quartz import CGWarpMouseCursorPosition
            CGWarpMouseCursorPosition((float(x), float(y)))
            return True
        except Exception:
            return False

    # ===============================================================
    # 숨기기 / 보이기 (트레이 아이콘 연동)
    # ===============================================================
    def hide_pet(self):
        """펫 윈도우 숨김. 메뉴바 아이콘으로 다시 보이게 할 수 있음.
        안전망: 60초 후 자동으로 다시 등장 (트레이 아이콘 못 찾을 경우 대비)."""
        self.hide()
        # 자동 복귀 타이머 (트레이 아이콘이 안 보이는 환경 대비 안전망)
        QTimer.singleShot(60_000, self._auto_unhide)

    def _auto_unhide(self):
        """숨기기 후 자동 복귀 — 이미 보이는 상태면 아무 효과 없음."""
        if not self.isVisible():
            self.show_pet()

    def show_pet(self):
        """펫 윈도우 다시 표시."""
        self.show()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide_pet()
        else:
            self.show_pet()

    def _setup_tray_icon(self):
        """메뉴바에 작은 펫 아이콘 추가 — 보이기·숨기기·집으로·종료 메뉴."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # 메뉴바 아이콘 — Retina 대응 (실제 44x44 pixel, 논리적 22x22 단위)
        # devicePixelRatio=2 로 설정해야 macOS Retina에서도 선명하고 다른 아이콘과 같은 크기
        pix = QPixmap(44, 44)
        pix.fill(Qt.transparent)
        pix.setDevicePixelRatio(2.0)
        ip = QPainter(pix)
        ip.setRenderHint(QPainter.Antialiasing)

        # 작은 크기에서 디테일을 살리려고 머리(얼굴)만 크게 그림 — 22x22 거의 꽉 채움
        ip.setBrush(QColor(255, 216, 0))
        ip.setPen(QPen(QColor(252, 190, 0), 1.2))
        ip.drawEllipse(1, 2, 20, 19)            # 머리 (큰 원)

        # 머리 위 작은 깃털 (귀여움 포인트)
        ip.setBrush(QColor(255, 216, 0))
        ip.setPen(QPen(QColor(252, 190, 0), 1))
        ip.drawEllipse(8, 0, 5, 4)

        # 눈
        ip.setBrush(QColor(20, 20, 20))
        ip.setPen(Qt.NoPen)
        ip.drawEllipse(6, 9, 3, 3)              # 왼쪽 눈
        ip.drawEllipse(13, 9, 3, 3)             # 오른쪽 눈

        # 부리
        ip.setBrush(QColor(255, 123, 0))
        ip.setPen(QPen(QColor(246, 92, 0), 1))
        ip.drawEllipse(7, 13, 8, 5)
        ip.end()

        self.tray = QSystemTrayIcon(QIcon(pix), self)
        self.tray.setToolTip("덕구")

        # 메뉴/액션을 self에 저장해서 GC로 사라지지 않게 함 (트레이 아이콘 사라짐 방지)
        self.tray_menu = QMenu()
        self.tray_action_toggle = QAction("보이기 / 숨기기", self)
        self.tray_action_toggle.triggered.connect(self.toggle_visibility)
        self.tray_menu.addAction(self.tray_action_toggle)
        self.tray_action_feed = QAction("먹이 주기", self)
        self.tray_action_feed.triggered.connect(self.feed_pet)
        self.tray_menu.addAction(self.tray_action_feed)
        self.tray_action_play = QAction("장난치기", self)
        self.tray_action_play.triggered.connect(self.force_cursor_catch)
        self.tray_menu.addAction(self.tray_action_play)
        self.tray_action_follow = QAction("커서 따라다니기", self)
        self.tray_action_follow.setCheckable(True)
        self.tray_action_follow.setChecked(self.follow_mode_enabled)
        self.tray_action_follow.triggered.connect(self.toggle_follow_mode)
        self.tray_menu.addAction(self.tray_action_follow)
        self.tray_action_home = QAction("집으로 보내기", self)
        self.tray_action_home.triggered.connect(self.go_home)
        self.tray_menu.addAction(self.tray_action_home)
        self.tray_menu.addSeparator()
        # 캐릭터 선택 서브메뉴
        self.tray_char_menu = self.tray_menu.addMenu("캐릭터")
        self.tray_action_char_ducku = QAction("덕구", self)
        self.tray_action_char_ducku.setCheckable(True)
        self.tray_action_char_ducku.setChecked(self.current_character == "ducku")
        self.tray_action_char_ducku.triggered.connect(lambda: self._set_character_from_tray("ducku"))
        self.tray_char_menu.addAction(self.tray_action_char_ducku)
        self.tray_action_char_bamti = QAction("밤티", self)
        self.tray_action_char_bamti.setCheckable(True)
        self.tray_action_char_bamti.setChecked(self.current_character == "bamti")
        self.tray_action_char_bamti.triggered.connect(lambda: self._set_character_from_tray("bamti"))
        self.tray_char_menu.addAction(self.tray_action_char_bamti)
        self.tray_action_settings = QAction("설정", self)
        self.tray_action_settings.triggered.connect(self.show_settings)
        self.tray_menu.addAction(self.tray_action_settings)
        self.tray_action_exit = QAction("Exit", self)
        self.tray_action_exit.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.tray_action_exit)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()

    # ===============================================================
    # 마우스 커서 반응 (따라가기 / 도망가기)
    # ===============================================================
    def _update_cursor_reaction(self):
        """매 프레임 호출. 마우스 커서 위치/속도로 cursor_mode 결정.

        - follow_mode ON → 거리 무관 follow/stare, 도망 X
        - follow_mode OFF + 빠른 커서 가까이 → escape (도망)
        - 그 외 → normal (평소 산책)
        """
        cursor = QCursor.pos()

        # 펫 화면 좌표상 중심
        pet_center_x = self.x() + self.pet_width // 2
        pet_center_y = self.y() + self.pet_height // 2

        dx = cursor.x() - pet_center_x
        dy = cursor.y() - pet_center_y
        distance = math.sqrt(dx * dx + dy * dy)

        # 커서 속도 (이전 프레임 대비 이동 거리)
        if self.last_cursor_pos is None:
            cursor_speed = 0.0
        else:
            cursor_speed = math.sqrt(
                (cursor.x() - self.last_cursor_pos.x()) ** 2
                + (cursor.y() - self.last_cursor_pos.y()) ** 2
            )
        self.last_cursor_pos = cursor

        # follow_mode ON → 거리 무관 항상 follow/stare (도망 안 함)
        if self.follow_mode_enabled and self.cursor_ignore_timer == 0:
            if distance > 50:
                self.cursor_mode = "follow"
            else:
                self.cursor_mode = "stare"
            return

        # follow_mode OFF: 빠른 커서 + 가까이 → 도망
        if (distance <= 250 and cursor_speed > 12
                and self.cursor_ignore_timer == 0):
            self.cursor_mode = "escape"
            self.is_running = True
            if self.run_timer < 15:
                self.run_timer = 15
            return

        # 그 외엔 평소 모드 (자유 산책 + 랜덤 이벤트 등)
        self.cursor_mode = "normal"

    # ===============================================================
    # 그리기: paintEvent
    # ===============================================================
    def paintEvent(self, event):
        """
        QPainter로 캐릭터를 직접 그린다.
        self.update() 가 호출될 때마다 Qt가 이 함수를 실행함.
        좌표는 윈도우(=캔버스) 기준 (0,0) ~ (pet_width, pet_height).
        """
        painter = QPainter(self)
        # 안티앨리어싱 → 둥근 모서리가 부드럽게 보임
        painter.setRenderHint(QPainter.Antialiasing)

        # 캐릭터의 중심 좌표 계산
        # 캐릭터를 윈도우 "아래쪽"에 정렬 → 위쪽에 점프 헤드룸 확보.
        # (pet_height - 60) 으로 기준점을 잡으면 평소엔 발이 윈도우 바닥 근처,
        # 점프해도 머리가 잘리지 않음.
        # bounce_offset(걷기 들썩임)과 jump_offset(점프) 모두 y에 반영
        cx = self.pet_width // 2
        # cy는 캐릭터 중심. lift_offset 만큼 위로 올라감(=드래그 시 떠오름)
        cy = (
            self.pet_height - 60
            + self.bounce_offset
            + self.jump_offset
            - int(self.lift_offset)
        )

        # 그림자 (공통, 캐릭터별 차이 X)
        self._draw_shadow(painter, cx, cy)

        # 잠자는 동안 호흡으로 캐릭터 전체가 살짝 위아래 (그림자는 고정)
        if self.is_sleeping:
            cy += int(math.sin(self.breathing_phase) * 1.5)

        # 캐릭터별 본체 그리기 분기
        if self.current_character == "bamti":
            self._draw_bamti(painter, cx, cy)
        else:
            self._draw_ducku(painter, cx, cy)

        # ----- 이하 ZZZ/하트/말풍선/메모는 캐릭터 공통 오버레이 -----
        # ----- ZZZ (잠잘 때만, 머리 위로 떠오름) -----
        if self.is_sleeping:
            self._draw_zzz(painter, cx, cy)

        # ----- ♥ 파티클 (더블클릭 좋아함 반응) -----
        if self.is_happy:
            self._draw_hearts(painter, cx, cy)

        # ----- 말풍선 (잠자는 동안엔 안 보이게) -----
        if self.is_speaking and not self.is_sleeping:
            self._draw_speech_bubble(painter, cx, cy)

        # ----- 부리에 물고 있는 작은 메모 (배달 중일 때만) -----
        if self.delivering_memo:
            self._draw_carried_memo(painter, cx, cy)

    def _draw_speech_bubble(self, painter, cx, cy):
        """펫 머리 위에 말풍선(둥근 사각형 + 회색 테두리 + 굵은 글씨)을 그림."""
        text = self.speech_text

        # 폰트: 굵게 + 가독성 좋은 크기
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)

        # 텍스트 폭/높이 측정 → 박스 크기 자동 계산
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(text)
        text_h = metrics.height()

        padding_x = 10
        padding_y = 5
        bubble_w = text_w + padding_x * 2
        bubble_h = text_h + padding_y * 2

        # 위치: 머리(cy - 38) 위로 8px 띄움. 화면 밖 잘림 방지를 위해 max(2, ...)
        bubble_x = cx - bubble_w / 2
        bubble_y = max(2.0, cy - 38 - bubble_h - 8)
        bubble_rect = QRectF(bubble_x, bubble_y, bubble_w, bubble_h)
        radius = 6

        # 배경: 흰색(살짝 반투명)
        painter.setBrush(QColor(255, 255, 255, 240))
        # 테두리: 진한 회색
        painter.setPen(QPen(QColor(110, 110, 110), 1.5))
        painter.drawRoundedRect(bubble_rect, radius, radius)

        # 텍스트: 어두운 회색, 박스 정중앙
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(bubble_rect, Qt.AlignCenter, text)

    def _draw_shadow(self, painter, cx, cy):
        """발 아래 그림자 — 캐릭터 공통."""
        air_distance = abs(self.jump_offset) + self.lift_offset
        shadow_scale = max(0.35, 1.0 - air_distance / 50)
        shadow_alpha = int(40 * shadow_scale)
        shadow_w = 42 * shadow_scale
        shadow_h = 7 * shadow_scale
        shadow_y = self.pet_height - 22 + int(self.shadow_y_offset)
        painter.setBrush(QColor(0, 0, 0, shadow_alpha))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            QRectF(cx - shadow_w / 2, shadow_y - shadow_h / 2, shadow_w, shadow_h)
        )

    def _draw_ducku(self, painter, cx, cy):
        """덕구 (오리) 캐릭터 — Figma 디자인 기반. 넓은 부리 + 깃털 union."""
        # ===== 색상 팔레트 =====
        body_yellow = QColor(255, 216, 0)
        body_outline = QColor(252, 190, 0)
        beak_orange = QColor(255, 123, 0)
        beak_outline = QColor(246, 92, 0)
        eye_dark = QColor(6, 5, 1)
        cheek_hover = QColor(255, 145, 165, 200)

        # ----- 발 (몸통 뒤에) -----
        if self.is_sleeping or self.is_looking_around or self.is_at_wall:
            foot_l_offset = 0
            foot_r_offset = 0
        else:
            lift = math.sin(self.bounce_phase) * 3
            foot_l_offset = int(lift)
            foot_r_offset = -int(lift)
        foot_half_spread = 7 if self.is_at_wall else 12
        painter.setBrush(QBrush(beak_orange))
        painter.setPen(QPen(beak_outline, 1))
        painter.drawEllipse(
            QRectF(cx - foot_half_spread - 7, cy + 20 - foot_l_offset, 14, 13)
        )
        painter.drawEllipse(
            QRectF(cx + foot_half_spread - 7, cy + 20 - foot_r_offset, 14, 13)
        )

        # ----- 몸통 -----
        painter.setBrush(QBrush(body_yellow))
        painter.setPen(QPen(body_outline, 1))
        painter.drawEllipse(QRectF(cx - 23, cy - 11, 46, 42))

        # ----- 비대칭 mirror 계산 -----
        if self.is_at_wall:
            facing = self.wall_facing
        else:
            facing = 1 if self.direction > 0 else -1
        mx = -facing

        def hf(orig_left, w):
            return (-orig_left - w) if mx == -1 else orig_left

        # ----- 갸우뚱 회전 (머리/깃털/눈/부리에만 적용) -----
        rotated = self.is_tilting and self.tilt_angle != 0
        if rotated:
            painter.save()
            painter.translate(cx, cy - 2)
            painter.rotate(self.tilt_angle)
            painter.translate(-cx, -(cy - 2))

        # ----- 머리 + 깃털 union -----
        head_path = QPainterPath()
        head_path.addEllipse(QRectF(cx - 20 + self.head_tilt, cy - 32, 40, 40))
        tuft1_left = hf(-10, 12)
        tuft2_left = hf(-5, 8)
        tuft1 = QPainterPath()
        tuft1.addRoundedRect(cx + self.head_tilt + tuft1_left, cy - 36, 12, 9, 4.5, 4.5)
        tuft2 = QPainterPath()
        tuft2.addRoundedRect(cx + self.head_tilt + tuft2_left, cy - 38, 8, 12, 4.0, 4.0)
        united_head = head_path.united(tuft1).united(tuft2)
        painter.setBrush(QBrush(body_yellow))
        painter.setPen(QPen(body_outline, 1))
        painter.drawPath(united_head)

        # ----- 볼 (드래그 시만) -----
        if self.is_dragging:
            painter.setBrush(QBrush(cheek_hover))
            painter.setPen(Qt.NoPen)
            if self.is_at_wall:
                cheek_x = cx + (5 * self.wall_facing) - 3.5 + self.head_tilt
                painter.drawEllipse(QRectF(cheek_x, cy - 13, 7, 5))
            else:
                painter.drawEllipse(QRectF(cx - 16 + self.head_tilt, cy - 13, 7, 5))
                painter.drawEllipse(QRectF(cx + 9 + self.head_tilt, cy - 13, 7, 5))

        # ----- 눈 -----
        eyes_closed = self.is_blinking or self.is_sleeping
        painter.setBrush(QBrush(eye_dark))
        painter.setPen(Qt.NoPen)
        if self.is_at_wall and not eyes_closed:
            eye_x = cx + (12 * self.wall_facing) - 2.5 + self.head_tilt
            painter.drawEllipse(QRectF(eye_x, cy - 20, 5, 5))
        elif eyes_closed:
            painter.setPen(QPen(eye_dark, 2))
            painter.drawLine(cx - 10 + self.head_tilt, cy - 17,
                             cx - 5 + self.head_tilt, cy - 17)
            painter.drawLine(cx + 5 + self.head_tilt, cy - 17,
                             cx + 10 + self.head_tilt, cy - 17)
        else:
            eye1_left = hf(-13, 5)
            eye2_left = hf(1, 5)
            painter.drawEllipse(QRectF(cx + self.head_tilt + eye1_left, cy - 20, 5, 5))
            painter.drawEllipse(QRectF(cx + self.head_tilt + eye2_left, cy - 20, 5, 5))

        # ----- 부리 (3도형 union, mirror) -----
        if self.is_at_wall:
            beak_shift = 12 * self.wall_facing + self.head_tilt
        elif self.is_looking_around or self.is_sleeping:
            beak_shift = self.head_tilt
        else:
            beak_shift = 2 * facing
        rect1_left = hf(-11, 11)
        rect2_left = hf(-9, 9)
        ell_left = hf(-7, 9)
        p_rect1 = QPainterPath()
        p_rect1.addRoundedRect(cx + beak_shift + rect1_left, cy - 16, 11, 6, 3, 3)
        p_rect2 = QPainterPath()
        p_rect2.addRoundedRect(cx + beak_shift + rect2_left, cy - 12, 9, 5, 2.5, 2.5)
        p_ell = QPainterPath()
        p_ell.addEllipse(QRectF(cx + beak_shift + ell_left, cy - 16, 9, 9))
        united_beak = p_rect1.united(p_rect2).united(p_ell)
        painter.setBrush(QBrush(beak_orange))
        painter.setPen(QPen(beak_outline, 1))
        painter.drawPath(united_beak)

        if rotated:
            painter.restore()

    def _draw_bamti(self, painter, cx, cy):
        """밤티 캐릭터 — 큰 원형 눈 + 항상 분홍 볼 + 안쪽으로 살짝 기운 안테나 + 가로 타원 부리."""
        # ===== 색상 팔레트 =====
        body_light = QColor(255, 240, 110)       # 밝은 노랑 (그라데이션 중앙)
        body_dark = QColor(235, 185, 25)         # 더 진한 노랑 (그라데이션 가장자리)
        body_outline = QColor(215, 160, 25)
        beak_orange = QColor(255, 145, 35)
        beak_outline = QColor(215, 105, 20)
        eye_dark = QColor(25, 20, 15)
        eye_highlight = QColor(255, 255, 255)
        cheek_pink = QColor(255, 160, 170, 220)  # 항상 보이는 분홍 볼

        # facing 계산 (벽 모드에서만 의미 있음)
        if self.is_at_wall:
            facing = self.wall_facing
        else:
            facing = 1 if self.direction > 0 else -1

        # ----- 발 -----
        if self.is_sleeping or self.is_looking_around or self.is_at_wall:
            foot_l_offset = 0
            foot_r_offset = 0
        else:
            lift = math.sin(self.bounce_phase) * 3
            foot_l_offset = int(lift)
            foot_r_offset = -int(lift)
        foot_half_spread = 7 if self.is_at_wall else 11
        painter.setBrush(QBrush(beak_orange))
        painter.setPen(QPen(beak_outline, 1))
        painter.drawEllipse(
            QRectF(cx - foot_half_spread - 6, cy + 31 - foot_l_offset, 12, 8)
        )
        painter.drawEllipse(
            QRectF(cx + foot_half_spread - 6, cy + 31 - foot_r_offset, 12, 8)
        )

        # ----- 몸통 — 살짝 납작한 타원 + 그라데이션 -----
        body_grad = QRadialGradient(cx - 10, cy + 12, 45)
        body_grad.setColorAt(0, body_light)
        body_grad.setColorAt(1, body_dark)
        painter.setBrush(QBrush(body_grad))
        painter.setPen(QPen(body_outline, 1.3))
        painter.drawEllipse(QRectF(cx - 27, cy + 1, 54, 36))

        # ----- 갸우뚱 회전 적용 (머리만 회전) -----
        rotated = self.is_tilting and self.tilt_angle != 0
        if rotated:
            painter.save()
            painter.translate(cx, cy + 4)
            painter.rotate(self.tilt_angle)
            painter.translate(-cx, -(cy + 4))

        # ----- 머리 — 둥근 원 + 그라데이션 -----
        head_grad = QRadialGradient(cx - 6, cy - 18, 30)
        head_grad.setColorAt(0, body_light)
        head_grad.setColorAt(1, body_dark)
        painter.setBrush(QBrush(head_grad))
        painter.setPen(QPen(body_outline, 1.3))
        painter.drawEllipse(QRectF(cx - 19, cy - 30, 38, 36))

        # ----- 안테나 깃털 (2개 작은 삼각형, 안쪽으로 살짝 기움) -----
        painter.setBrush(QBrush(body_dark))
        painter.setPen(QPen(body_outline, 1))
        tuft_path = QPainterPath()
        # 왼쪽 안테나: 끝이 살짝 오른쪽(안쪽)으로 기움
        lx_base = cx - 4 + self.head_tilt
        tuft_path.moveTo(lx_base - 2, cy - 28)
        tuft_path.lineTo(lx_base + 1.5, cy - 36)
        tuft_path.lineTo(lx_base + 2, cy - 28)
        tuft_path.closeSubpath()
        # 오른쪽 안테나: 끝이 살짝 왼쪽(안쪽)으로 기움
        rx_base = cx + 4 + self.head_tilt
        tuft_path.moveTo(rx_base - 2, cy - 28)
        tuft_path.lineTo(rx_base - 1.5, cy - 36)
        tuft_path.lineTo(rx_base + 2, cy - 28)
        tuft_path.closeSubpath()
        painter.drawPath(tuft_path)

        # ----- 볼 — 항상 보이는 분홍 (밤티의 특징!) -----
        painter.setBrush(QBrush(cheek_pink))
        painter.setPen(Qt.NoPen)
        if self.is_at_wall:
            cheek_x = cx + (5 * self.wall_facing) - 4 + self.head_tilt
            painter.drawEllipse(QRectF(cheek_x, cy - 7, 8, 6))
        else:
            painter.drawEllipse(QRectF(cx - 16 + self.head_tilt, cy - 7, 8, 6))
            painter.drawEllipse(QRectF(cx + 8 + self.head_tilt, cy - 7, 8, 6))

        # ----- 눈 — 크고 동그란 검은 눈 + 흰 하이라이트 -----
        eyes_closed = self.is_blinking or self.is_sleeping
        if self.is_at_wall and not eyes_closed:
            # 벽에 붙어 있을 때는 한쪽 눈만
            painter.setBrush(QBrush(eye_dark))
            painter.setPen(Qt.NoPen)
            eye_x = cx + (8 * self.wall_facing) - 4 + self.head_tilt
            painter.drawEllipse(QRectF(eye_x, cy - 20, 8, 8))
            # 흰 하이라이트
            painter.setBrush(QBrush(eye_highlight))
            painter.drawEllipse(QRectF(eye_x + 4.5, cy - 18.5, 2.5, 2.5))
        elif eyes_closed:
            # 자거나 깜빡일 때 — 굵은 가로선
            painter.setPen(QPen(eye_dark, 2.5))
            painter.drawLine(int(cx - 12 + self.head_tilt), int(cy - 16),
                             int(cx - 5 + self.head_tilt), int(cy - 16))
            painter.drawLine(int(cx + 5 + self.head_tilt), int(cy - 16),
                             int(cx + 12 + self.head_tilt), int(cy - 16))
        else:
            # 큰 동그란 검은 눈
            painter.setBrush(QBrush(eye_dark))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(cx - 12 + self.head_tilt, cy - 20, 8, 8))
            painter.drawEllipse(QRectF(cx + 4 + self.head_tilt, cy - 20, 8, 8))
            # 흰 하이라이트 (오른쪽 위)
            painter.setBrush(QBrush(eye_highlight))
            painter.drawEllipse(QRectF(cx - 7.5 + self.head_tilt, cy - 18.5, 2.5, 2.5))
            painter.drawEllipse(QRectF(cx + 8.5 + self.head_tilt, cy - 18.5, 2.5, 2.5))

        # ----- 부리 — 가로 타원 + 가운데 입선 (오리 부리 같은 모양) -----
        if self.is_at_wall:
            beak_shift = 6 * self.wall_facing + self.head_tilt
        elif self.is_looking_around or self.is_sleeping:
            beak_shift = self.head_tilt
        else:
            beak_shift = 2 * facing
        bx = cx + beak_shift
        painter.setBrush(QBrush(beak_orange))
        painter.setPen(QPen(beak_outline, 1))
        painter.drawEllipse(QRectF(bx - 6, cy - 8, 12, 8))
        # 가운데 입선
        painter.setPen(QPen(beak_outline, 0.8))
        painter.drawLine(int(bx - 5), int(cy - 4), int(bx + 5), int(cy - 4))

        if rotated:
            painter.restore()

    def _draw_carried_memo(self, painter, cx, cy):
        """배달 중 펫 부리 위에 작은 포스트잇을 그림."""
        facing_offset = 4 if self.direction > 0 else -4
        memo_x = cx - 12 + facing_offset
        memo_y = cy - 30
        # 살짝 그림자
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(memo_x + 1, memo_y + 2, 24, 18), 2, 2)
        # 노란 포스트잇
        painter.setBrush(QBrush(QColor(255, 230, 110)))
        painter.setPen(QPen(QColor(225, 190, 70), 0.8))
        painter.drawRoundedRect(QRectF(memo_x, memo_y, 24, 18), 2, 2)
        # 글씨 표현 (작은 가로선 3개)
        painter.setPen(QPen(QColor(160, 130, 50, 200), 1))
        painter.drawLine(int(memo_x + 4), int(memo_y + 6),
                         int(memo_x + 20), int(memo_y + 6))
        painter.drawLine(int(memo_x + 4), int(memo_y + 10),
                         int(memo_x + 20), int(memo_y + 10))
        painter.drawLine(int(memo_x + 4), int(memo_y + 14),
                         int(memo_x + 16), int(memo_y + 14))

    def _draw_hearts(self, painter, cx, cy):
        """더블클릭 좋아함 반응 — 머리 위로 ♥ 3개가 떠오름."""
        font = painter.font()
        original_size = font.pointSize() if font.pointSize() > 0 else 10
        # 3개의 ♥를 0.33 위상 차이로 그려서 연속 떠오르는 효과
        for i in range(3):
            phase = (self.heart_phase + i * 0.33) % 1.0
            # 위로 떠오르며 좌우로 살랑살랑
            sway = math.sin(phase * math.pi * 3) * 6
            heart_x = cx - 5 + sway
            heart_y = cy - 40 - phase * 35
            # 페이드 인 → 아웃 (sin)
            fade = math.sin(phase * math.pi)
            alpha = int(230 * fade)
            if alpha <= 0:
                continue
            font.setPointSize(int(original_size + phase * 5))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 100, 130, alpha))
            painter.drawText(int(heart_x), int(heart_y), "♥")

    def _draw_zzz(self, painter, cx, cy):
        """잠자는 펫 머리 위에 ZZZ 가 떠다니는 듯한 효과를 그림."""
        font = painter.font()
        original_size = font.pointSize() if font.pointSize() > 0 else 10
        # 두 개의 Z를 0.5 위상 차이로 그려 연속해서 떠오르는 듯한 느낌
        for i in range(2):
            phase = (self.zzz_phase + i * 0.5) % 1.0
            # 위로 + 오른쪽으로 점점 멀어짐
            z_x = cx + 14 + phase * 18
            z_y = cy - 38 - phase * 28
            # 페이드 인 → 페이드 아웃 (sin 곡선)
            fade = math.sin(phase * math.pi)  # 0 → 1 → 0
            alpha = int(220 * fade)
            if alpha <= 0:
                continue
            font.setPointSize(int(original_size + phase * 6))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(80, 110, 200, alpha))
            painter.drawText(int(z_x), int(z_y), "Z")

    # ===============================================================
    # 마우스 상호작용
    # ===============================================================
    def mousePressEvent(self, event):
        """왼쪽 버튼: 드래그 시작 / 오른쪽 버튼: 종료 메뉴 표시."""
        # 어떤 버튼이든 클릭하면 자고 있던 펫을 강제로 깨움 (집잠 포함)
        self._wake_up_if_sleeping(force=True)
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            # 드래그 시작하면 진행 중인 stalking/riding 은 즉시 종료
            self.is_stalking_cursor = False
            self.is_riding_cursor = False
            # 클릭 지점과 창 좌상단 사이의 오프셋을 저장 →
            # 드래그 도중 이 오프셋을 유지해야 자연스럽게 따라옴
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            # 들어올림 멘트는 더블클릭 가능성 때문에 즉시 X — doubleClickInterval 만큼 지연
            # 그 사이 더블클릭이 발동되면 happy 멘트가 먼저 뜨고, 이 콜백은 스킵
            QTimer.singleShot(
                QApplication.doubleClickInterval(),
                self._show_lift_speech_if_dragging,
            )
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def _show_lift_speech_if_dragging(self):
        """Press 후 doubleClickInterval 지난 뒤 호출.
        더블클릭으로 happy 상태가 됐으면 스킵, 아니면 들어올림 멘트 표시."""
        if self.is_dragging and not self.is_happy:
            self.is_speaking = True
            self.speech_text = "대박, 날고있음"
            self.speech_timer = 90

    def mouseDoubleClickEvent(self, event):
        """더블클릭 → 좋아함 반응 (점프 + 머리 위 ♥ + 멘트)."""
        if event.button() != Qt.LeftButton:
            return
        # 자고 있어도 강제로 깨움
        self._wake_up_if_sleeping(force=True)
        # 좋아함 모드 ON
        self.is_happy = True
        self.happy_timer = 75   # 약 2.3초 ♥ 파티클
        self.heart_phase = 0.0
        # 작은 점프
        self.is_jumping = True
        self.jump_velocity = -7
        self.jump_offset = 0
        # 좋아함 멘트 — 더블클릭은 명확한 액션이므로 다른 멘트 덮어쓰고 항상 표시
        # (이렇게 안 하면 press 시 예약된 "대박" 등에 가려져서 안 보임)
        self.is_speaking = True
        self.speech_text = random.choice(["꽥!", "좋아!", "헤헤", "꽥꽥"])
        self.speech_timer = 75

    def mouseMoveEvent(self, event):
        """드래그 중일 때만 창 위치를 마우스에 맞춰 이동."""
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """왼쪽 버튼 떼면 드래그 종료."""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(QCursor(Qt.ArrowCursor))

    def enterEvent(self, event):
        """마우스가 캐릭터 영역에 들어옴 → 볼 발그레 ON + 자고 있으면 깨움."""
        self.is_hovered = True
        self._wake_up_if_sleeping()
        self.update()

    def _wake_up_if_sleeping(self, force=False):
        """잠자는 상태면 깨움.
        force=False (호버 등): 집잠(is_napping_at_home)은 안 깨움
        force=True (클릭 등): 집잠도 깨움 + '개꿀잠 ㅋㅋ' 말풍선 표시
        """
        if not self.is_sleeping:
            return
        if self.is_napping_at_home and not force:
            return  # 호버로는 집잠 안 깨움
        was_napping_at_home = self.is_napping_at_home
        self.is_sleeping = False
        self.sleep_timer = 0
        self.is_napping_at_home = False
        if was_napping_at_home:
            # 집에서 자다 깬 거면 멘트 띄움
            self.is_speaking = True
            self.speech_text = "개꿀잠 ㅋㅋ"
            self.speech_timer = 150  # 약 4.5초

    def leaveEvent(self, event):
        """마우스가 캐릭터 영역에서 벗어남 → 볼 발그레 OFF."""
        self.is_hovered = False
        self.update()

    def show_context_menu(self, global_pos):
        """오른쪽 클릭 시 메뉴 표시."""
        menu = QMenu(self)
        feed_action = QAction("먹이 주기", self)
        feed_action.triggered.connect(self.feed_pet)
        menu.addAction(feed_action)
        play_action = QAction("장난치기", self)
        play_action.triggered.connect(self.force_cursor_catch)
        menu.addAction(play_action)
        follow_action = QAction("커서 따라다니기", self)
        follow_action.setCheckable(True)
        follow_action.setChecked(self.follow_mode_enabled)
        follow_action.triggered.connect(self.toggle_follow_mode)
        menu.addAction(follow_action)
        home_action = QAction("집으로 보내기", self)
        home_action.triggered.connect(self.go_home)
        menu.addAction(home_action)
        hide_action = QAction("숨기기", self)
        hide_action.triggered.connect(self.hide_pet)
        menu.addAction(hide_action)
        menu.addSeparator()
        # 캐릭터 선택 서브메뉴
        char_menu = menu.addMenu("캐릭터")
        ducku_action = QAction("덕구", self)
        ducku_action.setCheckable(True)
        ducku_action.setChecked(self.current_character == "ducku")
        ducku_action.triggered.connect(lambda: self.set_character("ducku"))
        char_menu.addAction(ducku_action)
        bamti_action = QAction("밤티", self)
        bamti_action.setCheckable(True)
        bamti_action.setChecked(self.current_character == "bamti")
        bamti_action.triggered.connect(lambda: self.set_character("bamti"))
        char_menu.addAction(bamti_action)
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)
        menu.exec_(global_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # macOS 전용: Accessory 모드로 전환
    # → Dock 아이콘이 안 뜨고, 다른 앱 클릭해도 펫이 사라지지 않음
    if sys.platform == "darwin":
        try:
            from AppKit import (
                NSApplication,
                NSApplicationActivationPolicyAccessory,
            )
            NSApplication.sharedApplication().setActivationPolicy_(
                NSApplicationActivationPolicyAccessory
            )
        except ImportError:
            print(
                "⚠️  pyobjc 미설치 → Dock 아이콘 숨김이 비활성화됩니다.\n"
                "   터미널에서 다음 명령으로 설치 후 다시 실행하세요:\n"
                "   pip3 install -r requirements.txt"
            )

    pet = DesktopPet()
    sys.exit(app.exec_())
