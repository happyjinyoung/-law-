# 내손을 java · 계약 도우미

계약 경험이 적은 사회초년생을 위한 대학 창의작품경진대회 출품용 로컬 웹 프로그램입니다. 사용자가 원문을 확인한 뒤 분석하고, 근거를 읽고, 계약별로 보관하고, 명시된 날짜를 일정으로 등록합니다. `java`는 프로젝트 이름이며 Java 언어를 뜻하지 않습니다.

팀명·학교·팀원·지도교수·최종 작품명은 [제출 정보](docs/TEAM.md)에서 작성하세요. GitHub 업로드 전 미확인 항목을 수정하세요. 이 소스는 로컬 단일 사용자 시연용이며 법률 판단을 제공하지 않습니다.

## 실행

Python 3.12 권장 (검증: 3.12.14). 앱 실행에 Node.js는 필요 없습니다.

```powershell
cd "프로젝트를 푼 경로\naesoneul-java"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

macOS/Linux는 `.venv/bin/python`을 사용하세요. 브라우저에서 [로컬 앱](http://127.0.0.1:8765)을 엽니다. HTML 파일을 더블클릭하는 방식이 아닙니다. 기본 8765 포트는 `.env`의 `PORT`로 바꿀 수 있습니다. 서버를 종료하려면 실행한 터미널에서 Ctrl+C를 누릅니다.

별도 프런트엔드 빌드, CDN, 외부 계정 없이 규칙 분석·SQLite 보관·일정 기능을 사용할 수 있습니다. TXT는 UTF-8/CP949, 파일은 최대 10MB, PDF는 최대 30쪽, 원문은 100,000자까지 지원합니다. 일반 텍스트 PDF를 실제 추출하며, 표와 열 순서가 원본과 다를 수 있으므로 추출 결과를 확인해야 합니다.

## 핵심 기능

- 홈: 저장된 프로필·오늘 날짜·다가오는 일정
- 등록: 직접 원문, TXT/PDF 업로드, 설치 상태에 따른 PNG/JPG·스캔 PDF OCR; 추출 후 수정 및 확인
- 분석: 발췌 요약, 기간·금액·지급 조건 문장, 갱신·해지·위약금·일방 변경·환불 확인 후보, 쉬운 표현 사전
- 근거: 정확한 인용·줄·문자 범위, 확인할 수 없는 필드는 `확인 불가`
- 보관: 사용자 확인 후 저장, 이름·유형 수정, 이름/원문 검색, 유형·가상 자료 필터, 계약 ID별 상세
- 일정: 명시된 연월일 후보, 원문 근거 확인 및 날짜·이름 수정 후 등록; 월간 달력, D-day, 추가·수정·삭제
- 알림: 전체/개별 토글, 7/3/1/0일 전·시간 설정, DB 고유키 중복 방지, 앱 재접속·자정 갱신
- 상담: 선택한 계약 문장 검색 또는 서버 AI 설명, 근거 없는 답변 방지, 모드 명시
- 설정: 로컬 표시 이름과 알림 설정 저장

원본 v2 UI의 430px 모바일 프레임, 네이비·골드·아이보리, 히어로 원형 선, 둥근 카드, 떠 있는 메뉴를 유지했습니다. 화면별 원본 점검은 [UI_AUDIT.md](docs/UI_AUDIT.md)에 있습니다. 원본 첨부 파일은 수정하지 않았습니다. PPT와 보조 HTML은 참고 자료로만 사용했으며, 잘못 첨부된 HWP는 사용하지 않았습니다.

## 실제 AI 연결 (선택 사항)

`.env.example`을 `.env`로 복사하고 서버에서만 설정합니다.

```dotenv
AI_API_KEY=본인의_API_키
AI_MODEL=본인_계정에서_사용가능한_모델_ID
AI_BASE_URL=https://api.openai.com/v1
AI_TIMEOUT_SECONDS=40
```

서버 재시작 후 분석 화면에서 실제 AI 모드를 선택하세요. 기본값은 로컬 모드입니다. 모델명은 임의로 고정하지 않았습니다. 다른 공급자는 OpenAI Responses의 `/responses` 요청과 `output[].content[].type=output_text` 형식에 호환되어야 합니다. API 키는 브라우저·저장 DB·응답에 포함하지 않습니다. AI 모드는 계약 원문을 외부 API로 전송하며 별도 비용이 발생할 수 있습니다.

문서는 신뢰하지 않는 JSON 데이터로 전달하고, 서버 지시와 분리합니다. 도구 호출은 부여하지 않습니다. JSON 응답 구조·인용문의 원문 포함 여부를 검사합니다. 실패·시간 초과·근거 없는 응답은 오류로 표시하며 로컬 성공 결과로 위장하지 않습니다. 인용이 존재해도 AI 설명 자체가 틀릴 수 있습니다. 사용자의 검토가 필요합니다. 실제 유료 API 호출은 키가 없어 검증하지 않았고, 성공·잘못된 근거·시간 초과를 모의 응답으로 검증했습니다.

## OCR 설치 (선택 사항)

Tesseract 5 계열 실행 파일과 `kor.traineddata`, `eng.traineddata`가 필요합니다. 스캔 PDF의 페이지 렌더링에는 `pypdfium2`를 사용합니다.

```powershell
# Tesseract 설치 후 실행 파일 경로를 .env에 지정할 수 있습니다.
# TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
tesseract --list-langs
# kor와 eng가 모두 나오는지 확인하세요.
```

설치 문서: [Tesseract 공식 안내](https://tesseract-ocr.github.io/tessdoc/Installation.html), [공식 한국어 언어 데이터](https://github.com/tesseract-ocr/tessdata_fast). 자동 다운로드나 설치를 수행하지 않습니다. 서버 재시작 후 설정 화면의 한국어 OCR 설치 상태를 확인하세요. 해당 엔진이 없는 환경에서는 명확한 오류와 직접 입력 방법을 안내합니다. 현재 환경에서는 OCR 엔진이 없어 실제 한국어 인식 품질을 측정하지 못했습니다. 연결 코드와 미설치 오류 경로만 검증했습니다. 카메라 실시간 촬영·DOCX는 지원하지 않습니다. 휴대폰 사진은 PNG/JPG 업로드로 받습니다.

## 구조

```text
frontend/          기존 모바일 분위기의 HTML·CSS·브라우저 동작
server.py          로컬 HTTP API·검증·정적 파일 제공
backend/analysis.py 규칙 추출·날짜·근거·문장 검색
backend/ai.py      서버 측 Responses 호환 AI 어댑터
backend/extraction.py TXT·PDF·조건부 OCR
backend/storage.py SQLite 스키마·연결·영속 상태
samples/           규칙 개발·시연에 사용한 가상 문서
tests/             단위·HTTP·브라우저 테스트
evaluation/        별도 합성 정답·평가 코드·실측 JSON·사람 평가 양식
docs/              명세·설계·시연·분담·출처·체크리스트·검증 기록
submission/        결과보고서 초안·인쇄용 포스터
data/              실행 후 생성, Git 및 제출 ZIP 제외
```

Python 표준 라이브러리 서버와 SQLite를 선택해 서버 흐름과 저장 구조를 학생들이 쉽게 설명할 수 있게 했습니다. PDF/OCR에만 외부 라이브러리를 사용합니다. [시스템/API 설명](docs/SYSTEM.md), [기능 체크리스트](docs/CHECKLIST.md)를 참고하세요.

## 테스트·평가 재현

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m evaluation.run
```

실측값은 [evaluation/results.json](evaluation/results.json), 검증 범위는 [docs/VALIDATION.md](docs/VALIDATION.md)에 기록했습니다. 12개 합성 문서에서 고유 날짜 집합의 정밀도·재현율·F1, 항목별/전체 주의 탐지, 인용 존재 여부, 규칙 처리 시간을 평가합니다. 개발 예시는 `samples/`, 평가 정답은 `evaluation/data.json`에 별도로 관리합니다. 작성자가 규칙을 알고 만든 작은 평가이므로 블라인드 검증이 아니며 실제 계약 전체로 일반화할 수 없습니다. 평가 결과를 보고 규칙을 변경한다면 기존 평가 데이터를 개발 세트로 재분류하고 새 평가 세트를 만드세요. 요약·쉬운 설명의 사람 평가 양식은 [human-review.csv](evaluation/human-review.csv)입니다. 만족도·사람 평가 결과는 아직 없습니다.

선택적 실제 브라우저 테스트 (Node.js 22+):

```powershell
npm install
npx playwright install chromium
# 다른 터미널에서 별도 시연 DB로 서버 실행
$env:APP_DB="$PWD/work/browser-test.sqlite3"
python server.py
# 원래 터미널에서 실행
npm run test:browser
```

설치된 Edge로 검사하려면 `$env:BROWSER_CHANNEL="msedge"`로 지정하세요. 브라우저 테스트는 가상 계약 생성·삭제 및 프로필 변경을 수행하므로 실제 사용자 DB에 실행하지 마세요. 테스트 화면은 `work/browser/`에 생성됩니다.

## 3~5분 시연 및 GitHub 제출

[시연 시나리오](docs/DEMO.md)에 따라 가상 샘플 → 분석 → 인용 확인 → 저장 → 상세 → 날짜 후보 수정·등록 → 상담 검색 → 재접속 보관 확인 순서로 진행하세요. [팀 역할](docs/TEAM.md), [AI·외부 라이브러리 활용 및 출처](docs/SOURCES.md), [결과보고서 초안](submission/REPORT.md), [인쇄용 포스터](submission/poster.html)를 함께 제공합니다. 포스터·보고서는 학교 양식과 팀 정보 확인 후 최종 편집하세요.

이 폴더 자체가 GitHub 저장소의 루트가 됩니다. 개인 GitHub 계정에 자동 업로드하지 않았습니다.

```powershell
git init
git add .
git status --short
# .env, data/, uploads/, work/, 실제 계약서가 목록에 없는지 확인
git commit -m "Implement contract assistant demo with evidence and schedules"
git branch -M main
git remote add origin https://github.com/본인계정/저장소이름.git
git push -u origin main
```

API 키·실제 계약서·개인정보는 저장소에 넣지 마세요. `.gitignore`는 파일 내용 검사를 대체하지 않습니다. 실수로 커밋한 키는 즉시 폐기하고 기록에서도 제거해야 합니다. 팀 작성 코드의 공개 라이선스는 학교·팀이 정하세요. 첨부 UI 원본의 권리 관계를 확인하지 않아 임의의 오픈소스 라이선스를 부여하지 않았습니다.

## 한계

로컬 단일 사용자, DB 평문 저장, 계정 인증·암호화 보관·운영 배포·브라우저 종료 중 푸시 미구현. 알림은 앱이 열린 때에만 동작하며 운영체제/브라우저 권한에 따라 표시되지 않을 수 있습니다. 중복 기록은 DB에서 방지하지만 표시와 DB 기록 사이 앱이 종료되면 해당 알림이 누락될 수 있습니다. 날짜는 완전한 연월일만 추출하고 상대 기한·연도 없는 날짜·정기 납부일은 자동 계산하지 않습니다. 키워드 규칙은 부정문에도 반응하고 동의어를 놓칠 수 있습니다. 법률·제도 안내 및 출처가 검증되지 않은 뉴스는 제공하지 않습니다.
