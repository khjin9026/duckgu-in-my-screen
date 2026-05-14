# duckgu in my screen 🦆

내 데스크탑 위에 사는 작은 오리 친구, **덕구** (와 친구 **밤티**).

Desktop Goose 에서 영감을 받아 직접 만든 macOS 데스크탑 펫입니다.
PyQt5 의 QPainter 로 도형을 직접 그려서 만든 캐릭터예요 (이미지 파일 X).

## 캐릭터

| 덕구 (Ducku) | 밤티 (Bamti) |
| :-: | :-: |
| 노란 오리, 넓은 부리 | 동그란 머리 + 안테나 깃털, 항상 분홍 볼 |

메뉴에서 **캐릭터** 항목으로 언제든 바꿀 수 있어요.

## 기능

- 🚶 데스크탑 위를 걸어다니고, 가끔 잠도 잠
- 👀 마우스 따라오기 / 도망가기
- ❤️ 더블클릭하면 좋아함
- 🤚 드래그해서 옮기기
- 📝 스케줄 등록 → 시간 되면 포스트잇으로 메모 전달
- 🪟 모든 Mission Control 스페이스에 항상 떠 있음

## 설치 (사용자)

1. [Releases](../../releases) 에서 최신 `덕구.app.zip` 다운로드
2. 압축 풀고 `덕구.app` 더블클릭
3. 처음 실행 시 보안 경고가 뜨면:
   - `덕구.app` 우클릭 → **열기** → **허용**
   - (Apple 미서명 앱이라 한 번만 거치면 됨)

## 빌드 (개발자)

```bash
# 의존성 설치
pip install -r src/requirements.txt
pip install pyinstaller

# 빌드 (덕구.app 생성)
./rebuild.sh
```

`rebuild.sh` 가 PyInstaller 로 `.app` 을 빌드하고 최상위 폴더로 옮겨줍니다.

## 폴더 구조

```
duckgu-in-my-screen/
├── 덕구.app          ← 빌드 결과물 (Releases 에서 배포)
├── rebuild.sh        ← 빌드 스크립트
├── README.txt        ← 사용자용 안내 (zip 배포본에 포함)
└── src/
    ├── desktop_pet.py    ← 메인 코드
    ├── make_icon.py      ← 아이콘 PNG 생성
    ├── icon.png/icns     ← 앱 아이콘
    └── requirements.txt
```

## 기술 스택

- Python 3 + PyQt5 (그리기/UI)
- pyobjc (macOS Dock 아이콘 숨김, Spaces 전체 표시)
- PyInstaller (.app 패키징)

## 라이선스

MIT
