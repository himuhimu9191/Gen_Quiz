"""Record the scope of reading-only batches 019 and 020."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit_path = ROOT / 'data/audits/2026-11-03.json'
audit = json.loads(audit_path.read_text(encoding='utf-8'))
for number, filename in [('019', 'batch-019-reading-format.json'), ('020', 'batch-020-reading-review.json')]:
    batch = json.loads((ROOT / 'data/audits' / filename).read_text(encoding='utf-8'))
    audit['batch_' + number] = {
        'reading_changes': len(batch['changes']),
        'record': 'docs/batch-' + number + '.md',
        'audit': 'data/audits/' + filename,
        'scope': 'Canonical reading only; fact verification states, classification, difficulty and tags preserved.',
    }
audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
path = ROOT / 'docs/progress.md'
text = path.read_text(encoding='utf-8').replace('タグ未確認6,969問', 'タグ未確認6,966問')
paragraph = '全7,000問の代表読みを形式点検し、[バッチ019](batch-019.md)で86問をひらがな入力向けに修正しました。[バッチ020](batch-020.md)では同一辞書見出しを個別に選定し、171問の誤読を校正しました。これらは読みのみの修正で、設問全体の照合件数は増やしていません。\n\n'
if paragraph not in text:
    text = text.replace('## 7,000問到達前の記録', paragraph + '## 7,000問到達前の記録')
path.write_text(text, encoding='utf-8')
path = ROOT / 'README.md'
text = path.read_text(encoding='utf-8')
line = '- [バッチ019の読み形式86問修正](docs/batch-019.md)\n- [バッチ020の辞書読み171問校正](docs/batch-020.md)\n'
if line not in text:
    text = text.replace('- [独立タグ34問の付与記録]', line + '- [独立タグ34問の付与記録]')
path.write_text(text, encoding='utf-8')
