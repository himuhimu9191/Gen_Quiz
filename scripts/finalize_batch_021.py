"""Correct answer leaks found during review and record the final batch snapshot."""
import copy
import json
from pathlib import Path
import quiz
from review_batch_021 import DECISIONS, ROOT, TODAY, save

questions = quiz.load(ROOT/'data/questions.jsonl')
reviews = quiz.load(ROOT/'data/reviews.jsonl')
rb = {r['ID']:r for r in reviews}
audit_path = ROOT/'data/audits/batch-021.json'
audit = json.loads(audit_path.read_text(encoding='utf-8'))
cb = {c['ID']:c for c in audit['changes']}
for decision in DECISIONS:
    number, genre, subgenre, level, tags, prompt, explanation, answers, reason, difficulty, key = decision
    q = questions[number-1]
    if q['問'] == prompt and q['解説'] == explanation and q['答えjson'] == answers:
        continue
    before = copy.deepcopy(q)
    r = rb[q['ID']]
    q.update({'問':prompt, '解説':explanation, '答えjson':answers})
    fields = [f for f in q if q[f] != before[f]]
    r['version'] += 1
    r['change_history'].append({'version':r['version'], 'date':TODAY, 'fields':fields, 'reason':'許容別名が問題文に含まれる箇所を修正。和菓子と暦で読みを共有できるかを再審査。'})
    r['alias_review']['accepted'] = answers[2:]
    r['alias_review']['reason'] = reason
    r['claims'][0]['claim'] = prompt.rstrip('？') + ' 正解は「' + answers[0] + '」。 ' + explanation
    r['uniqueness_review'] = '設問の条件から「' + answers[0] + '」を特定。正式な別名・異読は答え配列に記録。' + reason
    cb[q['ID']].update({'after':copy.deepcopy(q), 'version':r['version'], 'reason':reason})
save(ROOT/'data/questions.jsonl',questions)
save(ROOT/'data/reviews.jsonl',reviews)
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for status,suffix in [('all','all'),('candidate','candidates'),('verified','verified')]:
    quiz.export_csv(questions,reviews,status,ROOT/f'data/quiz_{suffix}.csv')
