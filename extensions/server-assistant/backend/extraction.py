"""파일은 메모리에서 추출하고 OCR 임시 파일은 처리 후 삭제한다."""
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 100_000


def validate_text(text):
    if not isinstance(text, str) or not text.strip(): raise ValueError('문서가 비어 있습니다. 원문을 입력하세요.')
    if len(text) > MAX_TEXT: raise ValueError('원문은 100,000자 이하여야 합니다.')
    if '\x00' in text: raise ValueError('텍스트에 지원하지 않는 NUL 문자가 있습니다.')
    return text


def ocr_status():
    command = os.getenv('TESSERACT_CMD') or shutil.which('tesseract')
    languages = []
    if command:
        try:
            run = subprocess.run([command, '--list-langs'], capture_output=True, timeout=5)
            languages = run.stdout.decode('utf-8', errors='replace').splitlines()[1:]
        except (OSError, subprocess.TimeoutExpired): command = None
    try:
        import pypdfium2  # noqa: F401
        pdf_render = True
    except ImportError: pdf_render = False
    return {'available': bool(command and 'kor' in languages and 'eng' in languages),
            'pdf_render': pdf_render, 'languages': languages,
            'message': '한국어 OCR: Tesseract 실행 파일과 kor·eng 데이터가 필요합니다. 스캔 PDF에는 pypdfium2도 필요합니다.'}


def ocr_image(data):
    if not ocr_status()['available']: raise ValueError('OCR 미설치: Tesseract 및 kor·eng 언어 데이터를 설치한 뒤 서버를 다시 시작하세요. 직접 입력도 가능합니다.')
    from PIL import Image
    with Image.open(io.BytesIO(data)) as image:
        if image.width * image.height > 25_000_000: raise ValueError('이미지는 2,500만 화소 이하여야 합니다.')
        temp_root = Path(__file__).resolve().parents[1] / 'work'
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='contract-ocr-', dir=temp_root) as folder:
            source = Path(folder) / 'input.png'
            image.convert('RGB').save(source)
            result = subprocess.run([os.getenv('TESSERACT_CMD') or shutil.which('tesseract'), str(source), 'stdout', '-l', 'kor+eng'],
                                    capture_output=True, timeout=60)
            if result.returncode: raise ValueError('OCR 추출에 실패했습니다. 선명한 이미지로 다시 시도하세요.')
            return result.stdout.decode('utf-8', errors='replace')


def extract_file(name, data):
    if not data: raise ValueError('빈 파일입니다.')
    if len(data) > MAX_BYTES: raise ValueError('파일은 10MB 이하여야 합니다.')
    extension = Path(name).suffix.lower()
    method, warnings = 'TXT', []
    try:
        if extension == '.txt':
            text = None
            for encoding in ['utf-8-sig', 'cp949']:
                try: text = data.decode(encoding); break
                except UnicodeDecodeError: pass
            if text is None: raise ValueError('TXT 인코딩을 읽을 수 없습니다. UTF-8로 저장하세요.')
        elif extension == '.pdf':
            if not data.startswith(b'%PDF-'): raise ValueError('PDF 파일 내용이 올바르지 않습니다.')
            from pypdf import PdfReader
            pdf = PdfReader(io.BytesIO(data))
            if pdf.is_encrypted: raise ValueError('암호화 PDF는 지원하지 않습니다. 비밀번호를 해제한 파일을 사용하세요.')
            if len(pdf.pages) > 30: raise ValueError('PDF는 30쪽 이하여야 합니다.')
            pages, method = [], 'PDF 텍스트 추출'
            scanned = [i for i, p in enumerate(pdf.pages) if not (p.extract_text() or '').strip()]
            renderer = None
            if scanned:
                status = ocr_status()
                if not status['available'] or not status['pdf_render']:
                    raise ValueError('텍스트 없는 PDF 페이지가 있습니다. 한국어 Tesseract 및 pypdfium2 설치 후 OCR을 이용하거나 원문을 직접 입력하세요.')
                import pypdfium2
                renderer = pypdfium2.PdfDocument(data)
                method = 'PDF 텍스트 + OCR'
                warnings.append('OCR 결과에는 오자가 있을 수 있습니다. 원본과 대조하세요.')
            try:
                for i, page in enumerate(pdf.pages):
                    content = page.extract_text() or ''
                    if i in scanned:
                        handle = renderer[i]
                        bitmap = handle.render(scale=2)
                        image = bitmap.to_pil()
                        buf = io.BytesIO(); image.save(buf, format='PNG')
                        content = ocr_image(buf.getvalue())
                        image.close(); bitmap.close(); handle.close()
                    pages.append(f'[PDF {i+1}쪽]\n{content}')
            finally:
                if renderer: renderer.close()
            text = '\n'.join(pages)
            if not pdf.pages: raise ValueError('PDF에 페이지가 없습니다.')
        elif extension in ('.png', '.jpg', '.jpeg'):
            text, method = ocr_image(data), '이미지 OCR'
            warnings.append('OCR 결과에는 오자가 있을 수 있습니다. 원본과 대조하세요.')
        else: raise ValueError('지원 형식: TXT, PDF, PNG, JPG. DOCX는 지원하지 않습니다.')
        return {'text': validate_text(text), 'method': method, 'warnings': warnings,
                'location': '아래 편집 원문 기준 줄/문자 위치입니다. PDF는 쪽 머리말도 포함합니다.'}
    except (ValueError, ImportError) as exc:
        raise ValueError(str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError('OCR 처리 시간이 초과되었습니다 (페이지당 60초).') from exc
    except Exception as exc:
        raise ValueError('문서 추출에 실패했습니다. 손상 여부·형식을 확인하거나 직접 입력하세요.') from exc
