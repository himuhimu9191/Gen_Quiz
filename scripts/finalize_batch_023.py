# -*- coding: utf-8 -*-
"""Repair the checked batch's controlled tags and short prompts before committing."""
import copy
import json
import quiz
from review_batch_021 import ROOT, TODAY, save
from review_batch_023 import DECISIONS

questions = quiz.load(ROOT/'data/questions.jsonl')
reviews = quiz.load(ROOT/'data/reviews.jsonl')
rb = {r['ID']:r for r in reviews}
audit_path = ROOT/'data/audits/batch-023.json'
audit = json.loads(audit_path.read_text(encoding='utf-8'))
cb = {c['ID']:c for c in audit['changes']}
for d in DECISIONS:
    number, genre, subgenre, level, tags, prompt, explanation, answers, reason, difficulty, key = d
    q = questions[number-1]
    after = dict(zip(quiz.FIELDS,[q['ID'],genre,subgenre,level,prompt,explanation,answers,tags]))
    fields = [f for f in quiz.FIELDS if q[f] != after[f]]
    if not fields:
        continue
    q.update(after)
    r = rb[q['ID']]
    r['version'] += 1
    r['change_history'].append({'version':r['version'],'date':TODAY,'fields':fields,
        'reason':'タグの対象種別を既存の管理語彙に統一し、短い設問を確認済みの根拠の範囲で調整。'})
    r['tag_review']['tags'] = tags
    r['claims'][0]['claim'] = prompt.rstrip('？')+' 正解は「'+answers[0]+'」。 '+explanation
    cb[q['ID']].update({'after':copy.deepcopy(q),'version':r['version']})
errors, warnings = quiz.validate(questions,reviews)
if errors:
    raise ValueError('\n'.join(errors))
audit['warnings'] = len(warnings)
save(ROOT/'data/questions.jsonl',questions)
save(ROOT/'data/reviews.jsonl',reviews)
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for status,suffix in [('all','all'),('candidate','candidates'),('verified','verified')]:
    quiz.export_csv(questions,reviews,status,ROOT/f'data/quiz_{suffix}.csv')
print('warnings',len(warnings))
