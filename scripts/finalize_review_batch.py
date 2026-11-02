# -*- coding: utf-8 -*-
"""Apply explicit prompt, explanation or tag repairs to an already reviewed batch."""
import argparse
import copy
import importlib
import json
import quiz
from review_batch_021 import ROOT, TODAY, save

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    parser.add_argument('--reason', required=True)
    args = parser.parse_args()
    module = importlib.import_module('review_batch_'+args.batch)
    questions = quiz.load(ROOT/'data/questions.jsonl')
    reviews = quiz.load(ROOT/'data/reviews.jsonl')
    qb = {q['ID']:q for q in questions}
    rb = {r['ID']:r for r in reviews}
    path = ROOT/('data/audits/batch-'+args.batch+'.json')
    audit = json.loads(path.read_text(encoding='utf-8'))
    cb = {c['ID']:c for c in audit['changes']}
    repaired = []
    for d in module.DECISIONS:
        n, genre, sub, level, tags, prompt, explanation, answers, reason, difficulty, key = d
        qid = 'Q%06d' % n
        q, r = qb[qid], rb[qid]
        if r.get('audit_batch') != args.batch:
            raise ValueError('Mismatched review batch: '+qid)
        after = dict(zip(quiz.FIELDS,[qid,genre,sub,level,prompt,explanation,answers,tags]))
        fields = [f for f in quiz.FIELDS if q[f] != after[f]]
        if not fields:
            continue
        if set(fields)-{'問','解説','タグ'}:
            raise ValueError('Needs a new evidence review, not a wording repair: '+qid)
        q.update(after)
        r['version'] += 1
        r['change_history'].append({'version':r['version'],'date':TODAY,'fields':fields,'reason':args.reason})
        r['tag_review']['tags'] = tags
        r['claims'][0]['claim'] = prompt.rstrip('？')+' 正解は「'+answers[0]+'」。 '+explanation
        cb[qid].update({'after':copy.deepcopy(q),'version':r['version']})
        repaired.append(qid)
    errors, warnings = quiz.validate(questions,reviews)
    if errors:
        raise ValueError('\n'.join(errors))
    audit['warnings'] = len(warnings)
    save(ROOT/'data/questions.jsonl',questions)
    save(ROOT/'data/reviews.jsonl',reviews)
    path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for status,suffix in [('all','all'),('candidate','candidates'),('verified','verified')]:
        quiz.export_csv(questions,reviews,status,ROOT/('data/quiz_'+suffix+'.csv'))
    print('repaired',repaired)

if __name__ == '__main__':
    main()
