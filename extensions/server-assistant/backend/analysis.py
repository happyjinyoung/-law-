"""규칙 기반 분석: 법률 판단 대신 원문에서 확인할 문장을 찾는다."""
import re
import time
from datetime import date

RULES = {
    'renewal': ('갱신', r'갱신|연장', '계약이 이어지는 조건과 의사 통보 방법을 확인하세요.'),
    'termination': ('해지', r'해지|해제|중도\s*종료', '계약을 끝낼 수 있는 조건과 통보 방법을 확인하세요.'),
    'penalty': ('위약금', r'위약금|위약벌|손해\s*배상', '계약을 지키지 못할 때 부담하는 금액과 적용 조건을 확인하세요.'),
    'unilateral': ('일방 변경', r'일방|임의로|사전\s*동의\s*없이', '한쪽이 조건을 바꿀 수 있는 범위와 절차를 확인하세요.'),
    'refund': ('반환·환불', r'환불|반환|공제', '돌려받는 금액과 시점, 공제 조건을 확인하세요.'),
}
TERMS = {
    '자동 갱신': '정해진 조건에서 별도 계약 없이 계약이 이어지는 것을 뜻합니다.',
    '위약금': '약속을 지키지 못했을 때 내기로 정한 돈입니다. 실제 부담 조건은 원문을 확인하세요.',
    '손해배상': '상대방에게 생긴 손해를 보상하는 것입니다.',
    '연대': '여러 사람이 함께 책임지는 내용일 수 있어 책임 범위를 확인해야 합니다.',
    '원상복구': '원래 상태로 되돌리는 것입니다. 복구 범위와 비용을 확인하세요.',
    '해지': '계약을 앞으로 끝내는 것을 뜻합니다. 통보 방식과 조건을 확인하세요.',
}
DATE_RE = re.compile(r'(?<!\d)(\d{4})\s*(?:년\s*|[-./]\s*)(\d{1,2})\s*(?:월\s*|[-./]\s*)(\d{1,2})\s*일?(?!\d)')


def evidence(text, start, end):
    """문자 위치는 Python 유니코드 코드포인트, 시작 포함/끝 제외 기준."""
    return {'quote': text[start:end], 'start': start, 'end': end,
            'line': text.count('\n', 0, start) + 1}


def clauses(text):
    return [evidence(text, m.start(), m.end()) for m in re.finditer(r'[^\n]+', text) if m.group().strip()]


def extract_dates(text):
    found = []
    for m in DATE_RE.finditer(text):
        try:
            value = date(*map(int, m.groups())).isoformat()
        except ValueError:
            continue
        left, right = text.rfind('\n', 0, m.start()) + 1, text.find('\n', m.end())
        right = len(text) if right < 0 else right
        # 날짜 주변의 명시적 문구만 용도로 제시하고 기한을 추정 계산하지 않는다.
        before, after = text[max(left, m.start()-20):m.start()], text[m.end():min(right, m.end()+20)]
        title = '원문 날짜 (용도 확인 필요)'
        if re.search(r'시작|개시', before + after): title = '시작 관련 날짜 (확인 필요)'
        if re.search(r'납부|지급|지불', before + after): title = '지급 관련 날짜 (확인 필요)'
        if re.search(r'종료|만료', before + after): title = '종료 관련 날짜 (확인 필요)'
        if re.search(r'통보|통지', before + after): title = '통보 관련 날짜 (확인 필요)'
        found.append({'date': value, 'title': title, 'evidence': evidence(text, left, right),
                      'date_evidence': evidence(text, m.start(), m.end())})
    return found


def analyze(text):
    started = time.perf_counter()
    lines = clauses(text)
    fields = {}
    patterns = {'기간': r'기간|시작|종료|만료|체결',
                '금액': r'(?:\d[\d,.]*\s*(?:억|만|천)?\s*원)|보증금|대금|급여|월세',
                '지급 조건': r'지급|납부|지불|입금|매월|분할'}
    for label, pattern in patterns.items():
        matches = [x for x in lines if re.search(pattern, x['quote'])]
        # '대금은 추후 협의' 같은 문장도 근거로 보여주되 금액 확정으로 오인시키지 않는다.
        known = [x for x in matches if not re.search(r'추후|미정|별도\s*협의|정하지\s*않|기재하지\s*않', x['quote'])]
        if label == '금액':
            known = [x for x in known if re.search(r'\d[\d,.]*\s*(?:억|만|천)?\s*원', x['quote'])]
        if label == '기간':
            known = [x for x in known if DATE_RE.search(x['quote']) or re.search(r'\d+\s*(?:년|개월|일간)|무기한', x['quote'])]
        fields[label] = {'value': '\n'.join(x['quote'] for x in known) or '확인 불가', 'evidence': matches}
    checks = []
    for key, (label, pattern, plain) in RULES.items():
        matches = [x for x in lines if re.search(pattern, x['quote'])]
        if matches:
            checks.append({'id': key, 'title': label, 'explanation': plain, 'evidence': matches})
    easy = [{'term': term, 'explanation': plain, 'evidence': [x for x in lines if term in x['quote']]}
            for term, plain in TERMS.items() if term in text]
    # 발췌 요약임을 명시한다. 빈 필드를 다른 계약의 샘플로 채우지 않는다.
    summary = []
    seen = set()
    for field in fields.values():
        for ev in field['evidence']:
            if ev['start'] not in seen:
                summary.append({'text': ev['quote'], 'evidence': ev})
                seen.add(ev['start'])
    if not summary and lines: summary = [{'text': lines[0]['quote'], 'evidence': lines[0]}]
    return {'mode': 'demo', 'mode_label': '로컬 규칙 분석', 'summary': summary[:5], 'fields': fields,
            'checks': checks, 'easy': easy, 'dates': extract_dates(text), 'ai_notes': [],
            'notice': '키워드 기반 확인 후보입니다. 탐지 결과가 없어도 문제가 없는 계약이라는 뜻은 아닙니다. 법률 판단을 대신하지 않습니다.',
            'elapsed_ms': round((time.perf_counter()-started)*1000, 3)}


def search_contract(text, question):
    tokens = set(re.findall(r'[가-힣A-Za-z0-9]{2,}', question))
    # 질문의 조사·어미 차이를 줄이기 위한 작은 사전. 의미 추론을 제공하지 않는다.
    for term in ['갱신','해지','위약금','반환','환불','보증금','지급','월세','기간','금액']:
        if term in question: tokens.add(term)
    scored = [(sum(t in x['quote'] for t in tokens), x) for x in clauses(text)]
    hits = [x for score, x in sorted(scored, key=lambda p: -p[0]) if score > 0][:4]
    return {'mode': 'search', 'label': '계약 문장 검색 (AI 상담 아님)', 'evidence': hits,
            'answer': '질문 단어와 일치하는 원문입니다. 문맥을 직접 확인하세요.' if hits else '선택한 계약 원문에서 확인할 수 없습니다.',
            'general': '일반 법률·제도 정보는 제공하지 않습니다.'}
