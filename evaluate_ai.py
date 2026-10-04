"""Reproduce the frozen synthetic retrieval evaluation, without sponsor inputs."""
import argparse
import hashlib
import json
from pathlib import Path
from corroborai.suggest import LabelIndex, MODEL_INFO


def evaluate(output):
    path=Path(__file__).parent/'tests/fixtures/retrieval_cases.json'
    case=json.loads(path.read_text(encoding='utf-8'));index=LabelIndex(case['candidates']);reports={}
    for subset in ('development','evaluation'):
        comparisons=[]
        for item in case[subset]:
            record={**item}
            for method,baseline in [('tfidf',False),('difflib',True)]:
                result=index.query(item['query'],baseline=baseline);ranked=[r['label'] for r in result['candidates']]
                accepted=result['status']=='suggestion';expected=item['expected'];record[method]={'status':result['status'],'candidates':result['candidates'],'top1_correct':expected is not None and accepted and bool(ranked) and ranked[0]==expected,'top3_contains_expected':expected is not None and expected in ranked,'correct_abstention':expected is None and not accepted,'wrong_suggestion':accepted and (expected is None or ranked[0]!=expected)}
            comparisons.append(record)
        summaries={}
        positive=sum(r['expected'] is not None for r in comparisons);negative=len(comparisons)-positive
        for method in ('tfidf','difflib'):
            summaries[method]={'positive_queries':positive,'no_unique_match_queries':negative,'correct_top1_suggestions':sum(r[method]['top1_correct'] for r in comparisons),'expected_in_top3':sum(r[method]['top3_contains_expected'] for r in comparisons),'correct_abstentions':sum(r[method]['correct_abstention'] for r in comparisons),'wrong_suggestions':sum(r[method]['wrong_suggestion'] for r in comparisons),'total_abstentions':sum(r[method]['status']=='abstain' for r in comparisons)}
        reports[subset]={'summary':summaries,'cases':comparisons,'rules_only_candidate_suggestions':0}
    result={'case_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'provenance':case['provenance'],'model':MODEL_INFO,'results':reports,'interpretation':'Synthetic reference retrieval, not independently annotated HR accuracy. Candidate suggestions supplement exact-rule review; baseline comparison does not imply superiority.'}
    Path(output).parent.mkdir(parents=True,exist_ok=True);Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({s:reports[s]['summary'] for s in reports}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);evaluate(p.parse_args().output)
