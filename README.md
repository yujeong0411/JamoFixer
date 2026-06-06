<div align="center">
  <img src="Icon.png" alt="Jamo Fixer" width="128" />
  <h1>Jamo Fixer</h1>
  <p>맥에서 받은 한글 파일명이 <code>ㅍㅏㅇㅣㄹ.docx</code>처럼 자모 분리되어 보일 때, 폴더·파일을 끌어다 놓으면 정상 이름으로 일괄 교정하는 Windows 데스크톱 앱.</p>
</div>

---

## 왜 필요한가요?

macOS는 한글 파일명을 **NFD(자모 분해형)**, Windows는 **NFC(완성형)**로 다룹니다. 같은 "한글" 글자가 OS마다 다르게 저장되어, 맥에서 만든 파일을 윈도우로 옮기면 자음·모음이 풀려 보입니다.

핵심 변환은 한 줄입니다:

```python
import unicodedata
fixed = unicodedata.normalize("NFC", name)
```

Jamo Fixer는 이걸 클릭 한 번에, 폴더 단위로 안전하게 수행합니다.

## 주요 기능

- **NFC 자동 정규화** — NFD로 깨진 이름을 완성형으로 일괄 복구
- **드래그앤드롭** — 폴더·파일 여러 개를 던지면 누적해서 한 번에 처리
- **변환 전 미리보기** — `현재 이름 → 바뀔 이름`을 표로 확인 후 실행
- **하위 폴더 포함** — 체크박스 한 번으로 전체 트리 재귀 스캔
- **안전한 처리 순서** — 파일 먼저, 폴더는 깊은 것부터 → 경로 깨짐 방지
- **충돌 회피** — 같은 이름이 이미 있으면 덮어쓰지 않고 건너뜀
- **오프라인 동작** — 네트워크·외부 의존성 없이 내 컴퓨터에서만 실행

## 설치 & 실행

1. [Releases](https://github.com/yujeong0411/JamoFixer/releases/latest)에서 `JamoFixer.exe`를 받습니다. (파이썬 설치 불필요)
2. 더블클릭으로 실행. Windows SmartScreen 경고가 뜨면 **추가 정보 → 실행**.
3. 교정할 폴더나 파일을 창에 끌어다 놓거나, **[폴더 선택…]** / **[파일 선택…]** 버튼으로 추가.
4. 미리보기를 확인하고 **[변환하기]**.

## 사용 팁

- 여러 폴더의 파일을 한꺼번에 정리하려면 그냥 드롭을 반복하세요. **누적**됩니다. (필요 시 **[초기화]**)
- 한 폴더에서 특정 파일만 고치고 싶으면 그 파일들만 골라 드롭하거나 "파일 선택…"으로 다중 선택.
- 변환 후 결과 다이얼로그의 "자세히"에서 건너뛴 항목과 사유를 확인할 수 있습니다.

## 개발자용

### 소스에서 실행

```bash
pip install pyqt6
python jamo_fixer.py
```

### 단일 실행 파일 빌드 (Windows)

```bash
pip install pyqt6 pyinstaller

pyinstaller --onefile --windowed --name "JamoFixer" ^
            --icon Icon.ico --add-data "Icon.png;." ^
            jamo_fixer.py
```

결과물: `dist/JamoFixer.exe`

### 릴리즈 자동 배포

태그를 푸시하면 GitHub Actions가 `windows-latest`에서 exe를 빌드해 GitHub Release에 자동 첨부합니다.

```bash
# 1) jamo_fixer.py 상단의 __version__ 을 새 버전으로 수정
#    예: __version__ = "1.0.1"
# 2) 커밋
git add jamo_fixer.py
git commit -m "Bump version to 1.0.1"

# 3) 태그 + 푸시
git tag v1.0.1
git push origin master --tags
```

워크플로(`.github/workflows/release.yml`)는 태그 이름(`v*`에서 `v` 제거)과 코드의 `__version__`이 **일치하는지 검증**한 뒤 빌드하므로, 둘이 어긋나면 빌드가 실패합니다.

### 인앱 업데이트 알림

앱 시작 시 백그라운드 스레드에서 GitHub Releases API로 최신 버전을 조회합니다. 더 높은 버전이 있으면 상단에 노란 배너가 떠서 다운로드 페이지로 이동하는 링크를 보여줍니다. 네트워크가 없거나 API 호출이 실패하면 조용히 무시되어 일반 사용에는 영향 없습니다.

## 기술 스택

- Python 3.11+
- PyQt6 — GUI
- 표준 라이브러리 `os`, `unicodedata` — 핵심 변환 로직
- PyInstaller — 단일 exe 패키징

## 라이선스

개인 사용 용도. 자세한 라이선스 정책은 별도 명시 전까지 보류.
