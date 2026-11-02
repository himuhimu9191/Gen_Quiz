"""Validate, export and judge the Japanese quiz dataset (stdlib only)."""
import argparse
import collections
import csv
import datetime
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('ID', 'ジャンル', 'サブジャンル', '難易度', '問', '解説', '答えjson', 'タグ')
GENRES = ('アニメ＆ゲーム', '文系', '理系', '生活', '雑学', 'エンタメ＆スポーツ', '社会')
STATES = {'candidate', 'verified', 'approved', 'held', 'retired'}


def normalize(value):
    """Normalize notation only; do not guess readings or accept substrings."""
    value = unicodedata.normalize('NFKC', value).casefold()
    value = ''.join(chr(ord(c) - 0x60) if '\u30a1' <= c <= '\u30f6' else c for c in value)
    return re.sub(r'[\s・･]', '', value)


def accepts(answers, response):
    key = normalize(response)
    return bool(key) and key in {normalize(x) for x in answers}


def load(path):
    with Path(path).open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate(questions, reviews):
    errors, warnings = [], []
    ids = set()
    review_ids = [r.get('ID') for r in reviews]
    if len(set(review_ids)) != len(review_ids):
        errors.append('審査記録のID重複')
    by_id = {r.get('ID'): r for r in reviews}
    prompts = set()
    answers_seen = {}
    for q in questions:
        qid = q.get('ID', '?')
        if tuple(q) != FIELDS:
            errors.append(f'{qid}: 列または列順が仕様と異なる')
        if not isinstance(qid, str) or not re.fullmatch(r'Q\d{6}', qid):
            errors.append(f'{qid}: ID形式不正')
        if qid in ids:
            errors.append(f'{qid}: ID重複')
        ids.add(qid)
        if q.get('ジャンル') not in GENRES or type(q.get('難易度')) is not int or q.get('難易度') not in range(1, 6):
            errors.append(f'{qid}: 分類不正')
        for name in ('サブジャンル', '問', '解説'):
            if not isinstance(q.get(name), str) or not q[name].strip():
                errors.append(f'{qid}: {name}が空または文字列でない')
        prompt = normalize(q.get('問', ''))
        if prompt in prompts:
            errors.append(f'{qid}: 同一問題文')
        prompts.add(prompt)
        length = len(q.get('問', ''))
        if length < 35 or length > 100:
            warnings.append(f'{qid}: 問題文{length}文字（要確認）')
        answers = q.get('答えjson')
        if not isinstance(answers, list) or len(answers) < 2 or any(not isinstance(a, str) or not a.strip() for a in answers):
            errors.append(f'{qid}: 代表表記と読みを含む配列が必要')
        else:
            # The required first two entries may normalize to the same value.
            keys = [normalize(a) for a in answers]
            if len(set(keys[2:])) != len(keys[2:]) or any(k in keys[:2] for k in keys[2:]):
                errors.append(f'{qid}: 不要な許容表記の重複')
            main = keys[0]
            if main in answers_seen:
                warnings.append(f'{qid}: 正解対象が{answers_seen[main]}と共通（要確認）')
            answers_seen[main] = qid
        tags = q.get('タグ')
        if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            errors.append(f'{qid}: タグは空でない文字列の配列が必要')
        elif len({normalize(tag) for tag in tags}) != len(tags):
            errors.append(f'{qid}: タグ重複')
        r = by_id.get(qid)
        if r is None:
            errors.append(f'{qid}: 審査記録なし')
            continue
        if r.get('status') not in STATES:
            errors.append(f'{qid}: 審査状態不正')
        if r.get('tag_status') not in {'pending', 'reviewed'}:
            errors.append(f'{qid}: タグ審査状態不正')
        elif r['tag_status'] == 'reviewed' and not tags:
            errors.append(f'{qid}: タグ審査済みだがタグなし')
        elif r['tag_status'] == 'pending' and tags:
            errors.append(f'{qid}: 未審査タグが登録されている')
        if type(r.get('version')) is not int or r['version'] < 1:
            errors.append(f'{qid}: 版番号不正')
        if isinstance(answers, list):
            for alias in r.get('rejected_aliases', []):
                if accepts(answers, alias):
                    errors.append(f'{qid}: 不許可の略称が正解に含まれている: {alias}')
        if r.get('status') in {'verified', 'approved'}:
            claims = r.get('claims', [])
            if not claims:
                errors.append(f'{qid}: 確認済みの根拠なし')
            for claim in claims:
                if not all(claim.get(k) for k in ('claim', 'source', 'locator', 'checked_on')):
                    errors.append(f'{qid}: 事実照合記録が不完全')
                try:
                    datetime.date.fromisoformat(claim.get('checked_on', ''))
                except (ValueError, TypeError):
                    errors.append(f'{qid}: 事実確認日の形式不正')
            if not r.get('uniqueness_review'):
                errors.append(f'{qid}: 一意性審査なし')
        if r.get('status') == 'approved':
            if not r.get('reviewer') or not r.get('reviewed_on'):
                errors.append(f'{qid}: 人の承認記録なし')
            if r.get('time_sensitive') and not all(r.get(f) for f in ('reference_date', 'recheck_on')):
                errors.append(f'{qid}: 時点依存の基準日・再確認日なし')
        for field in ('reviewed_on', 'recheck_on', 'reference_date'):
            if r.get(field):
                try:
                    datetime.date.fromisoformat(r[field])
                except (ValueError, TypeError):
                    errors.append(f'{qid}: {field}の形式不正')
    for qid in set(review_ids) - ids:
        errors.append(f'{qid}: 問題のない審査記録')
    return errors, warnings


def export_csv(questions, reviews, status, output):
    errors, _ = validate(questions, reviews)
    if errors:
        raise ValueError('\n'.join(errors))
    allowed = {r['ID'] for r in reviews if status == 'all' or r['status'] == status}
    rows = [q for q in questions if q['ID'] in allowed]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        for q in rows:
            writer.writerow({**q,
                             '答えjson': json.dumps(q['答えjson'], ensure_ascii=False),
                             'タグ': json.dumps(q['タグ'], ensure_ascii=False)})
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate')
    exp = sub.add_parser('export')
    exp.add_argument('--status', choices=sorted(STATES | {'all'}), default='approved')
    exp.add_argument('--output', required=True)
    judge = sub.add_parser('judge')
    judge.add_argument('id')
    judge.add_argument('response')
    args = parser.parse_args()
    questions = load(ROOT / 'data/questions.jsonl')
    reviews = load(ROOT / 'data/reviews.jsonl')
    errors, warnings = validate(questions, reviews)
    if errors:
        for error in errors:
            print('ERROR:', error)
        return 1
    if args.command == 'validate':
        print(f'{len(questions)}問 / 構造検証エラー0件（事実確認の合格ではありません）')
        print('状態:', dict(collections.Counter(r['status'] for r in reviews)))
        tag_counts = collections.Counter(r['tag_status'] for r in reviews)
        print(f"タグ: {tag_counts['reviewed']}問確認済み / {tag_counts['pending']}問未確認")
        counts = collections.Counter((q['ジャンル'], q['難易度']) for q in questions)
        for genre in GENRES:
            print(genre, [counts[genre, n] for n in range(1, 6)])
        for warning in warnings:
            print('WARNING:', warning)
    elif args.command == 'export':
        print(f'{export_csv(questions, reviews, args.status, args.output)}問を出力（{args.status}）: {args.output}')
    else:
        q = next((q for q in questions if q['ID'] == args.id), None)
        if q is None:
            parser.error('指定したIDがありません')
        result = accepts(q['答えjson'], args.response)
        print('正解' if result else '不正解')
        return 0 if result else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
