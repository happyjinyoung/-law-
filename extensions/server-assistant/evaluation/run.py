"""실행: python -m evaluation.run. 모델 API를 호출하지 않는 결정적 평가."""
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from backend.analysis import analyze, RULES

ROOT = Path(__file__).resolve().parent


def score(tp, fp, fn):
    p = tp/(tp+fp) if tp+fp else 0
    r = tp/(tp+fn) if tp+fn else 0
    return {'tp':tp,'fp':fp,'fn':fn,'precision':round(p,4),'recall':round(r,4),'f1':round(2*p*r/(p+r),4) if p+r else 0}


def all_evidence(result):
    for x in result['summary']: yield x['evidence']
    for field in result['fields'].values(): yield from field['evidence']
    for x in result['checks']+result['easy']: yield from x['evidence']
    for x in result['dates']: yield x['evidence']; yield x['date_evidence']


def run():
    dataset=json.loads((ROOT/'data.json').read_text(encoding='utf-8'))
    counts={k:[0,0,0] for k in ['dates',*RULES]}; evidence_ok=0; evidence_total=0; times=[]; details=[]
    for doc in dataset['documents']:
        start=time.perf_counter(); result=analyze(doc['text']); times.append((time.perf_counter()-start)*1000)
        predicted={x['date'] for x in result['dates']}; gold=set(doc['dates'])
        counts['dates'][0]+=len(predicted&gold);counts['dates'][1]+=len(predicted-gold);counts['dates'][2]+=len(gold-predicted)
        actual={x['id'] for x in result['checks']}
        for key in RULES:
            counts[key][0]+=int(key in actual and key in doc['checks'])
            counts[key][1]+=int(key in actual and key not in doc['checks'])
            counts[key][2]+=int(key not in actual and key in doc['checks'])
        for ev in all_evidence(result):
            evidence_total+=1;evidence_ok+=int(doc['text'][ev['start']:ev['end']]==ev['quote'] and ev['quote'] in doc['text'])
        details.append({'id':doc['id'],'predicted_dates':sorted(predicted),'gold_dates':sorted(gold),'predicted_checks':sorted(actual),'gold_checks':doc['checks']})
    totals=[sum(counts[k][i] for k in RULES) for i in range(3)]
    output={'measured_at_utc':datetime.now(timezone.utc).isoformat(), 'mode':'demo / local rules',
            'environment':{'os':platform.platform(),'python':platform.python_version(),'processor':platform.processor()},
            'documents':len(times),'data_disclosure':dataset['metadata'],
            'date_metric_unit':'문서별 고유 ISO 날짜 집합. 같은 날짜의 반복 언급은 1개로 계산.',
            'dates':score(*counts['dates']), 'checks':{k:score(*counts[k]) for k in RULES},'checks_micro':score(*totals),
            'evidence':{'exact_match':evidence_ok,'total':evidence_total,'ratio':round(evidence_ok/evidence_total,4)},
            'time_ms':{'mean':round(statistics.mean(times),4),'median':round(statistics.median(times),4),'max':round(max(times),4),'total':round(sum(times),4)},
            'time_scope':'1회 실행, 규칙 분석만 측정. PDF·OCR·HTTP·AI·저장 시간은 포함하지 않음.',
            'limitations':'소규모 합성 세트이며 실제 계약 성능으로 일반화할 수 없음. 인용 존재 검사는 설명의 의미적 정확성을 증명하지 않음.', 'details':details}
    (ROOT/'results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:output[k] for k in ['documents','dates','checks_micro','evidence','time_ms']},ensure_ascii=False,indent=2))
    return output


if __name__=='__main__':run()
