# -*- coding: utf-8 -*-
"""Refresh current counts and render the latest explicit review batches."""
import argparse
import collections
import json
from pathlib import Path
import re
import quiz

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    args = parser.parse_args()
    number = args.batch
    questions = quiz.load(ROOT/'data/questions.jsonl')
    reviews = quiz.load(ROOT/'data/reviews.jsonl')
    rb = {r['ID']:r for r in reviews}
    counts = collections.Counter(r['status'] for r in reviews)
    tagging = collections.Counter(r['tag_status'] for r in reviews)
    errors, warnings = quiz.validate(questions,reviews)
    if errors:
        raise ValueError('\n'.join(errors))
    batch = json.loads((ROOT/f'data/audits/batch-{number}.json').read_text(encoding='utf-8'))
    audit_path = ROOT/'data/audits/2026-11-03.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    audit.update({'total':len(questions), 'statuses':{s:counts[s] for s in ('verified','candidate','approved','held','retired')}})
    audit['tagging'].update({'reviewed':tagging['reviewed'],'pending':tagging['pending']})
    audit['batch_'+number] = {k:batch[k] for k in ('reviewed','newly_verified','held_duplicates')}
    audit['batch_'+number].update({'audit':f'data/audits/batch-{number}.json','record':f'docs/batch-{number}.md'})
    audit['structure_validation'] = {'errors':len(errors),'warnings':len(warnings),'scope':'Structure only; not factual verification.'}
    audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path = ROOT/'README.md'
    text = path.read_text(encoding='utf-8')
    for label, value in [('出典照合済み',counts['verified']),('未照合候補',counts['candidate']),('重複保留',counts['held']),('照合済み',counts['verified']),('独立タグ確認済みは',tagging['reviewed'])]:
        text = re.sub(re.escape(label)+r'[\d,]+問',label+f'{value:,}問',text)
    text = re.sub(r'未確認は[\d,]+問',f'未確認は{tagging["pending"]:,}問',text)
    text = re.sub(r'現在[\d,]+問がタグ確認済み',f'現在{tagging["reviewed"]:,}問がタグ確認済み',text)
    text = re.sub(r'独立タグ[\d,]+問の付与記録',f'独立タグ{tagging["reviewed"]:,}問の付与記録',text)
    link = f'- [バッチ{number}の個別照合](docs/batch-{number}.md)\n'
    if link not in text:
        text = text.replace('- [独立タグ',link+'- [独立タグ')
    path.write_text(text,encoding='utf-8')
    path = ROOT/'docs/progress.md'
    text = path.read_text(encoding='utf-8')
    current, history = text.split('## 7,000問到達前の記録',1)
    for label, value in [('出典照合済み',counts['verified']),('未照合候補',counts['candidate']),('重複保留',counts['held']),('独立タグ確認済み',tagging['reviewed']),('未確認',tagging['pending']),('タグ未確認',tagging['pending']),('照合済み',counts['verified'])]:
        current = re.sub(re.escape(label)+r'[\d,]+問',label+f'{value:,}問',current)
    paragraph = f'[バッチ{number}](batch-{number}.md)で{batch["reviewed"]}問を個別に再照合・改稿し、{batch["newly_verified"]}問を新たに照合済みにしました。言い換え重複{batch["held_duplicates"]}問を保留しています。全件照合は未完了です。\n\n'
    if paragraph not in current:
        current += paragraph
    path.write_text(current+'## 7,000問到達前の記録'+history,encoding='utf-8')
    path = ROOT/'docs/review-2026-11-03.md'
    text = path.read_text(encoding='utf-8')
    marker = '<!-- current-review:start -->'
    end_marker = '<!-- current-review:end -->'
    current = (marker+'\n## 現在の照合状況\n\n'
        +f'合計{len(questions):,}行、出典照合済み{counts["verified"]:,}問、'
        +f'未照合候補{counts["candidate"]:,}問、重複保留{counts["held"]:,}問。'
        +f'タグ確認済みは{tagging["reviewed"]:,}問です。全件照合は未完了です。\n\n'
        +f'直近の[バッチ{number}](batch-{number}.md)で{batch["reviewed"]}問を個別確認しました。'
        +'現在の変更前後は各バッチの監査記録と[進捗](progress.md)に記載しています。\n'
        +end_marker+'\n')
    if marker in text:
        text = re.sub(re.escape(marker)+r'.*?'+re.escape(end_marker)+'\n',lambda _:current,text,flags=re.S)
    else:
        title, history = text.split('\n',1)
        history = history.replace('現在は合計7,000問','バッチ018終了時は合計7,000問')
        history = history.replace('現在は7,000問について','この時点では7,000問について')
        text = title+'\n\n'+current+'\n## バッチ018までの記録\n'+history
    path.write_text(text,encoding='utf-8')
    tagged = [q for q in questions if rb[q['ID']]['tag_status']=='reviewed']
    lines = ['# タグ付与記録（2026-11-03）','',f'本文を個別確認した{len(tagged):,}問に、回答対象種別と内容領域の2タグを付けています。残り{tagging["pending"]:,}問は空配列で未審査です。','','| ID | タグ |','| --- | --- |']
    lines += ['| '+q['ID']+' | '+'、'.join(q['タグ'])+' |' for q in tagged]
    lines += ['','ジャンルだけから機械的に付けたタグは審査済みとしていません。各IDのタグ選定方法・確認日を審査記録に保存しています。']
    (ROOT/'docs/tags-2026-11-03.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines = [f'# バッチ{number}：本文・読み・分類の個別照合','',
        f'{batch["checked_on"]}。{batch["reviewed"]}問を個別確認し、うち{batch["newly_verified"]}問を新たに照合済みとしました。重複{batch["held_duplicates"]}問は保留です。',
        '難易度1・2は広い認知が見込めるものに限定し、各問の理由を審査記録へ保存しました。難易度は試遊前の暫定値です。','',
        f'[変更前後と理由](../data/audits/batch-{number}.json)。個別の根拠・該当箇所・取得ハッシュは審査記録と出典台帳を参照してください。資料本文は再配布していません。','',
        '| ID | 正解 | 分類 | 難易度 | 修正理由 |','| --- | --- | --- | --- | --- |']
    for change in batch['changes']:
        if 'after' in change:
            q = change['after']
            lines.append(f'| {q["ID"]} | {q["答えjson"][0]} | {q["ジャンル"]}／{q["サブジャンル"]} | {q["難易度"]} | {change["reason"]} |')
        else:
            lines.append(f'| {change["ID"]} | 保留 | {change.get("duplicate_of", "")}と重複 | — | {change["reason"]} |')
    lines += ['','7,000行への到達と、全件の内容照合完了は区別しています。人による公開承認も別の工程です。']
    (ROOT/f'docs/batch-{number}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('verified',counts['verified'],'candidate',counts['candidate'],'held',counts['held'],'tagged',tagging['reviewed'],'errors',len(errors),'warnings',len(warnings))

if __name__ == '__main__':
    main()
