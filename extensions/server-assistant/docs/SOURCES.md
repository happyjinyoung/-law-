# AI·외부 라이브러리·자료 활용 기록

기준일: 2026-11-05. 일반 법률·제도에 관한 정보를 제공하지 않으므로 법률 출처를 만들어 넣지 않았다.

|대상|사용 위치·용도|출처·조건|
|---|---|---|
|사용자 제공 AI 계약 도우미 v2.html|모바일 구조·색·히어로·달력·일정 CRUD·알림 설정 설계|사용자 첨부, 권리 관계는 팀이 확인|
|사용자 제공 ai (2).html|별도 일정 화면·기존 화면 흐름 참고|사용자 첨부|
|사용자 제공 내손을_java_화이트_11.5일용.pptx|프로젝트 배경·대상·기능 흐름·법률 판단 경계 참고|사용자 첨부|
|생성형 AI 코딩 지원|서버·브라우저 코드·규칙·합성 데이터·테스트·문서 초안 작성|Codex를 통한 코드 생성 및 실행 보조. 실제 모델 ID는 이 세션에서 확인하지 않아 확정하지 않음. 팀은 설명·수정·검증 책임을 갖고 사용 내역을 보완|
|실행 시 선택형 AI|서버 설명 생성 / 계약 질의|[OpenAI 공식 Text generation 문서](https://developers.openai.com/api/docs/guides/text), Responses 방식 확인. 키·모델은 환경변수. 이번 실제 호출 없음|
|Python 3.12.14|http.server·sqlite3·정규식·unittest·urllib|[Python 문서](https://docs.python.org/3.12/), PSF 라이선스|
|pypdf 6.10.0|PDF 텍스트 추출|[공식 추출 안내](https://pypdf.readthedocs.io/en/stable/user/extract-text.html), BSD-3-Clause. OCR은 제공하지 않음|
|Pillow 13.0.0|OCR 입력 이미지 변환|[Pillow](https://python-pillow.github.io/), HPND 계열 라이선스|
|pypdfium2 5.14.0|선택형 스캔 PDF 렌더링|[pypdfium2](https://github.com/pypdfium2-team/pypdfium2), Apache-2.0/BSD-3-Clause; PDFium 및 번들 고지 확인|
|Tesseract (미설치)|선택형 한국어/영어 OCR 실행|[설치](https://tesseract-ocr.github.io/tessdoc/Installation.html), [명령](https://github.com/tesseract-ocr/tessdoc/blob/main/Command-Line-Usage.md), [언어 데이터](https://github.com/tesseract-ocr/tessdata_fast), Apache-2.0|
|ReportLab 4.4.9|테스트에서 가상 PDF 생성|[ReportLab](https://www.reportlab.com/opensource/), BSD 계열|
|Playwright 1.62.1|실제 브라우저 자동 검증|[Playwright](https://playwright.dev/), Apache-2.0|

버전은 실제 검증 환경 기준으로 고정했다. 외부 패키지 소스·설치 파일·브라우저는 이 저장소에 포함하지 않으며 라이선스의 정확한 전문은 설치 버전 패키지에 동봉된 LICENSE/NOTICE를 따른다. UI는 시스템 글꼴과 로컬 CSS를 사용해 외부 CDN 요청을 제거했다.
