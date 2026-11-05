# 추가 연결 검증 (2026-11-05)

- 사용자 `일로와.zip`의 원본 소스 5개를 해제한 후 SHA-256 비교: **5/5 일치, 변경·삭제 0개**.
- HTTP로 원본 HTML·JS·CSS를 내려받아 ZIP 원본과 바이트 비교하는 테스트 포함. 서버에서도 원본 본문에 스크립트를 삽입하거나 내용을 바꿔 보내지 않는다.
- 실행 프레임이 원본 로딩 후 별도의 읽기 전용 브리지 파일을 추가한다. 원본 함수·이벤트·데이터를 교체하지 않고, 사용자가 보내기를 눌렀을 때만 추출 원문을 읽는다.
- 추가 서비스 모듈의 단위·HTTP·서버 프로세스 재시작 테스트 **21개 통과**.
- 확장판 루트의 원본 보존·HTTP 원본 바이트·추가 화면 제공 테스트 **2개 통과**.
- 실제 Chromium 151 / Playwright 1.62.1 / 430×950 / Asia/Seoul에서 추가 연결 브라우저 검사 **통과**.
- 원본 카메라 입력의 `accept=image/*`, `capture=environment` 속성이 유지됨을 확인. 실제 휴대폰 카메라 촬영·PC 웹캠은 검증하지 않음.
- 원본에서 한국어 폰트를 임베드한 가상 PDF를 PDF.js로 실제 추출 → 원문 보내기 → 추가 화면 원문 확인 → 규칙 분석 → SQLite 저장·개별 상세를 확인.
- 원본의 필드 교정 화면까지 실행한 뒤 추출 원문을 추가 화면으로 보낼 수 있는지 확인.
- 원본 일정 추가 후 원문 전달·추가 저장을 수행하고 새로고침: 원본 일정은 기존 localStorage에 유지, 추가 계약은 SQLite에 유지.
- 브라우저 JavaScript pageerror 없음. 원본·추가 화면 캡처를 직접 확인.
- 원본 OCR 코드는 보존하고 Tesseract.js 모듈을 불러오는 구조를 확인했지만 실제 한국어 인식 결과·정확도는 측정하지 않음.
- 원본의 법률 수치·판정·샘플·상담 내용은 검증하거나 수정하지 않음. ‘안전/위반’ 표현은 기존 코드의 표현이며 법률적 확정으로 해석하면 안 됨.

처음 테스트 PDF는 미임베드 CID 폰트 때문에 원본 PDF.js에서 텍스트가 비어 OCR 대상으로 처리되었다. 원본 코드를 수정하지 않고, 테스트를 위해 한국어 폰트가 임베드된 PDF로 재검사하여 통과했다. 실제 업로드에서도 PDF의 글꼴·인코딩에 따라 텍스트 추출이 실패하거나 OCR이 필요할 수 있다.

추가 연결 테스트 재현 (Windows, 가상 자료 전용):

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tests/make_fixture.py
npm install
npx playwright install chromium
# 다른 터미널에서 가상 테스트 DB로 서버를 실행
$env:APP_DB="$PWD/work/test.sqlite3"
python run.py
# 처음 터미널에서 실행
npm run test:browser
```

브라우저 테스트는 해당 브라우저 컨텍스트의 가상 일정·추가 계약을 생성한다. 사용자 실제 DB를 지정하지 않는다. Windows 맑은 고딕은 테스트 PDF 생성에만 필요하며 폰트 파일을 저장소나 ZIP에 배포하지 않는다. 추가 모듈의 합성 평가 결과와 범위는 `extensions/server-assistant/evaluation/results.json` 및 해당 모듈의 `docs/VALIDATION.md`를 따른다.
