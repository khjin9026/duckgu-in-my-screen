# duckgu in my screen 🦆

내 데스크탑 위에 사는 작은 오리 친구, **덕구** (와 비밀친구 **밤티**).

## 캐릭터

| 덕구 | 밤티 |
| :-: | :-: |
| 귀여워요 | 귀?여워요 |

메뉴에서 **캐릭터** 항목으로 언제든 바꿀 수 있어요.

## 기능

- 🚶 데스크탑 위를 걸어다니고, 가끔 잠도 잠
- 👀 마우스 따라오기 / 도망가기
- ❤️ 더블클릭하면 좋아함
- 🤚 드래그해서 옮기기
- 📝 스케줄 등록 → 시간 되면 포스트잇으로 메모 전달
- 🪟 Mission Control 에서도 설정 가능

## 실행방법
* 실행 전 유의사항
  1. 덕구는 개발 인증서 없이 취미로 제작한 서비스로, 첫 실행시 보안 경고가 뜰 수 있습니다.
  2. Mac OS만 지원됩니다.

1. [Releases](../../releases) 에서 최신 `duckgu in my screen.zip` 다운로드해주세요.
2. 압축 풀고 `덕구` 앱 아이콘 더블 클릭해주세요.
3. 처음 실행 시 보안 경고가 뜰 경우 아래 방법 중 하나로 진행해주세요.
   > 방법 1. `덕구.app` 우클릭 → **열기** → **허용**   
   > 방법 2. `덕구.app` 클릭 → 설정 - 개인정보 보호 및 보안 - (스크롤) 보안의 덕구 **그래도 열기** 버튼 클릭 → **그래도 열기** → **암호 입력**
   
   한 번만 열기 성공하면 이후엔 그냥 클릭만으로 열려요!



### 실행방법 이미지 첨부

<img width="198" height="217" alt="image" src="https://github.com/user-attachments/assets/48773fe8-f080-4b55-b722-c976ed4f6702" />

<img width="698" height="185" alt="image" src="https://github.com/user-attachments/assets/b3db9ab3-5b99-4a0c-9cd0-affa12bb5a0c" />

<img width="198" height="266" alt="image" src="https://github.com/user-attachments/assets/bb8c2597-d01f-465a-a20d-842402d6ad5d" />




그럼 덕구와 밤티와 재밌는 맥생활하세요
https://github.com/user-attachments/assets/bd174c83-22de-45cc-b817-c8366b5dcd74

<img width="484" height="276" alt="image" src="https://github.com/user-attachments/assets/f0d534b2-b911-4eac-a400-506891a6975d" />





---


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
