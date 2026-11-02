# -*- coding: utf-8 -*-
"""Cache dictionary pages selected for batch 028 before editorial review."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_dictionary_readings import lookup, plain

DC = Path(os.environ['TEMP']) / 'genquiz_dictionary_cache'
OUT = Path(os.environ['TEMP']) / 'genquiz_primary_028'
OUT.mkdir(exist_ok=True)
WORDS = [
    'コルコバード', 'ねぶた', 'ダイヤモンド', 'おニャン子クラブ',
    'ンジャメナ', 'マー油', 'タージマハル', 'ハエ', 'キリギリス',
    'ドナルドダック', 'シーマン', 'ピッツバーグパイレーツ', 'ポーション',
    'テキサスホールデム', 'プロレス', 'ルービックキューブ', 'アメリカンフットボール',
    'ヒトカラ', 'コブクロ', 'ピーターラビット', 'ごきぶりポーカー', '舞祭組',
    'ジェームズボンド', 'ブルースリー', 'ナショナルバスケットボールアソシエーション',
    'アースウィンドアンドファイアー', 'マカロニペンギン',
]

def main():
    results = []
    views = []
    for word in WORDS:
        result = lookup({'answer': word}, DC)
        results.append(result)
        if result.get('lookup_status') == 'found':
            path = DC / (hashlib.sha256(word.encode('utf-8')).hexdigest() + '.html')
            if path.exists():
                views.append(word + '\n' + plain(path.read_text(encoding='utf-8', errors='ignore'))[:5000])
    (OUT / 'dictionary_views.txt').write_text('\n\n'.join(views), encoding='utf-8')
    (OUT / 'lookup_results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('found', sum(r.get('lookup_status') == 'found' for r in results), 'of', len(results))
    print('missing', [r['answer'] for r in results if r.get('lookup_status') != 'found'])

if __name__ == '__main__':
    main()
