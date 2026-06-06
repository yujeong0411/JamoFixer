# 한글 파일명 자소 교정기 — 구현 명세 (Claude Code용)

## 1. 목적

맥(macOS)에서 만든 파일을 윈도우로 옮겼을 때, 한글 파일명이
`ㅍㅏㅇㅣㄹ.docx` 처럼 자음·모음이 분리되어 보이는 현상을 고치는 윈도우 데스크톱 앱.

원인은 유니코드 정규화 방식 차이다. macOS는 파일명을 **NFD(자모 분해형)**로
저장하고, Windows는 **NFC(완성형)**를 기대한다. 따라서 깨진 파일명을 NFC로
정규화하면 정상 표기로 복구된다.

핵심 변환 로직은 한 줄이다:

```python
import unicodedata
fixed = unicodedata.normalize("NFC", name)
```

## 2. 대상 사용자

- 개발자 본인(받은 파일 일괄 정리)
- 비개발자 동료(exe로 배포받아 클릭만으로 사용)

→ **비개발자도 설명 없이 쓸 수 있는 단순한 UI**가 최우선 요구사항.

## 3. 기술 스택

- Python 3.11+
- PyQt6 (GUI)
- PyInstaller (단일 exe 빌드)
- 표준 라이브러리 `os`, `unicodedata` 만으로 핵심 로직 처리 (외부 의존성 최소화)

## 4. 기능 요구사항

### 4.1 폴더 지정 (2가지 방법 모두 지원)
1. 창에 폴더(또는 파일)를 **드래그앤드롭** — 파일을 떨어뜨리면 그 부모 폴더를 대상으로.
2. **[폴더 선택…]** 버튼 → 표준 폴더 선택 다이얼로그.

### 4.2 미리보기 (변환 전 필수)
- 폴더를 지정하면 즉시 교정 대상을 스캔해 표로 보여준다.
- 표 컬럼: `종류(파일/폴더)`, `현재 이름`, `바뀔 이름`.
- 현재 이름은 빨간색, 바뀔 이름은 초록색으로 시각 구분.
- **이미 정상(NFC)인 항목은 목록에 넣지 않는다.** (`name != normalize("NFC", name)` 인 것만)
- 상단에 `교정 대상 N개` 카운트 표시.
- 대상이 0개면 "이미 모두 정상입니다" 안내 + 변환 버튼 비활성화.

### 4.3 옵션
- **[ ] 하위 폴더까지 포함** 체크박스 (기본 ON).
  - ON: `os.walk`로 전체 순회.
  - OFF: `os.listdir`로 최상위만.
- 체크 변경 시 미리보기 자동 갱신.

### 4.4 변환 실행
- **[변환하기]** 버튼 → "N개 항목의 이름을 바꿉니다. 계속할까요?" 확인 다이얼로그.
- 확인 시 실제 `os.rename` 수행.
- 완료 후 결과 다이얼로그: `완료: X개 변환됨` (+ 건너뛴 항목 있으면 사유 표시).
- 변환 후 미리보기 자동 갱신(남은 항목 0개가 정상).

## 5. 처리 순서 / 엣지 케이스 (중요)

### 5.1 파일 먼저, 폴더는 깊은 것부터
폴더 이름을 먼저 바꾸면 그 안 파일들의 경로가 깨진다. 따라서:
1. **파일을 먼저** 모두 처리.
2. **폴더는 경로가 긴 것(=더 깊은 것)부터** 처리.

스캔 결과를 `파일 목록 + 폴더목록(경로 길이 내림차순)` 순으로 반환할 것.

### 5.2 이름 충돌
NFC로 바꾼 이름이 같은 폴더에 이미 존재하면(자기 자신 제외) **덮어쓰지 말고 건너뛴다.**
경로 비교는 `os.path.normcase`로(윈도우는 대소문자 무시).

```python
if os.path.exists(target) and os.path.normcase(target) != os.path.normcase(full):
    skip(old, "같은 이름이 이미 있어 건너뜀")
```

### 5.3 rename 실패
권한 문제 등으로 `OSError` 발생 시 그 항목만 건너뛰고 사유를 결과에 기록.
전체 작업이 중단되지 않게 try/except로 항목별 보호.

### 5.4 건너뜀 목록 표시
건너뛴 항목은 결과 다이얼로그의 상세(detailed text)에 `· 이름 — 사유` 형태로,
최대 10개 + "외 N개"로 요약.

## 6. 핵심 함수 시그니처 (권장)

```python
def needs_fix(name: str) -> bool:
    """NFC 정규화 시 이름이 달라지면 True."""

def scan_folder(root: str, recursive: bool) -> list[tuple[str, str, str, str]]:
    """반환: [(전체경로, 현재이름, 바뀔이름, 종류), ...]  (파일→폴더 깊은순)"""

def apply_fix(items) -> tuple[int, list[tuple[str, str]]]:
    """반환: (성공수, [(이름, 사유), ...] 건너뛴 목록)"""
```

GUI는 `QMainWindow` 상속한 단일 클래스 `JamoFixer`로 구성.
`setAcceptDrops(True)` + `dragEnterEvent`/`dropEvent` 구현.

## 7. UI 레이아웃 (위→아래)

1. 제목 라벨: "한글 파일명 자소 교정기"
2. 설명 한 줄 (회색, 줄바꿈 허용)
3. [드롭존 라벨(점선 박스)] + [폴더 선택… 버튼] (가로 배치)
4. [☑ 하위 폴더까지 포함] ──── [교정 대상 N개]
5. 미리보기 테이블 (세로로 가장 큰 영역)
6. 구분선
7. 상태 라벨 ──── [변환하기 버튼(초록, 우측 하단)]

스타일: `app.setStyle("Fusion")`, 폰트 "맑은 고딕", 포인트 컬러 `#2E7D32`.
드롭존은 드래그 진입 시 초록 테두리로 강조, 폴더 지정되면 경로 표시 + 초록 배경.

## 8. 빌드 (배포용 exe)

```bash
pip install pyqt6 pyinstaller

# 단일 파일 exe, 콘솔창 숨김
pyinstaller --onefile --windowed --name "한글파일명교정기" jamo_fixer.py
```

- 결과물: `dist/한글파일명교정기.exe`
- 비개발자에게는 이 exe 하나만 전달하면 됨(파이썬 설치 불필요).
- 아이콘 추가 시: `--icon=app.ico` 옵션.
- 윈도우 SmartScreen 경고가 뜰 수 있음 → "추가 정보 → 실행"으로 안내.

## 9. 향후 확장 아이디어 (선택, 지금은 불필요)
- 우클릭 컨텍스트 메뉴 등록 (폴더 우클릭 → "자소 교정")
- 변환 로그를 텍스트 파일로 저장
- NFC↔NFD 양방향 전환 토글
- 다국어(파일명 안의 한글 외 문자)도 정규화 동일하게 적용되는지 테스트 케이스 추가

## 10. 참고: 동작 검증용 테스트

```python
import unicodedata
nfd = unicodedata.normalize("NFD", "한글파일.docx")   # 자모 분해 (맥 저장 형태 모사)
assert needs_fix(nfd) is True
assert unicodedata.normalize("NFC", nfd) == "한글파일.docx"
assert needs_fix("normal_english.txt") is False
assert needs_fix("한글파일.docx") is False  # 이미 NFC
```
