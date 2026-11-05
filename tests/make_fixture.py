"""브라우저 연결 검사용 가상 PDF. Windows 맑은 고딕을 임베드하며 실제 계약서가 아니다."""
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[1]/'work';root.mkdir(exist_ok=True)
font=Path('C:/Windows/Fonts/malgun.ttf')
if not font.exists():raise SystemExit('이 한국어 브라우저 PDF 테스트는 Windows 맑은 고딕이 필요합니다. 일반 앱 실행에는 필요 없습니다.')
pdfmetrics.registerFont(TTFont('DemoFont',str(font)))
c=Canvas(str(root/'fictional.pdf'));c.setFont('DemoFont',12)
for i,line in enumerate(['가상 표준근로계약서 (실제 계약 아님)','계약 기간: 2030년 3월 2일부터 2030년 5월 2일까지','임금은 100,000원이며 2030년 3월 10일 지급한다.','업무내용: 가상 시연 자료 디자인','근무장소: 가상 사무실','중도 해지 조건은 서면 협의한다.']):c.drawString(30,750-25*i,line)
c.save();print(root/'fictional.pdf')
