# -*- coding: utf-8 -*-
"""Fetch bounded reading material for human/model review; never edit quiz statuses."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import quiz
from audit_dictionary_readings import lookup, plain

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start',type=int,default=1)
    parser.add_argument('--limit',type=int,default=100)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    reviews = {r['ID']:r for r in quiz.load(ROOT/'data/reviews.jsonl')}
    selected = [q for q in quiz.load(ROOT/'data/questions.jsonl')
                if int(q['ID'][1:]) >= args.start and reviews[q['ID']]['status']=='candidate'][:args.limit]
    dc = Path(os.environ['TEMP'])/'genquiz_dictionary_cache'
    dc.mkdir(exist_ok=True)
    words = list(dict.fromkeys(q['答えjson'][0] for q in selected))
    metadata = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = pool.map(lambda w:lookup({'answer':w},dc),words)
        for i, result in enumerate(results,1):
            metadata[result['answer']] = result
            if i%25==0:
                print('fetched',i,'/',len(words),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8') as out:
        for q in selected:
            word = q['答えjson'][0]
            m = metadata[word]
            body = ''
            if m.get('lookup_status')=='found':
                path = dc/(hashlib.sha256(word.encode('utf-8')).hexdigest()+'.html')
                html = path.read_text(encoding='utf-8')
                body = plain(' '.join(re.findall(r'<article\b.*?</article>',html,re.S)))[:1600]
            out.write(json.dumps({'question':q,'dictionary':m,'body':body},ensure_ascii=False)+'\n')
    print('prepared',len(selected),'IDs',selected[0]['ID'] if selected else None,
          selected[-1]['ID'] if selected else None,'output',args.output,flush=True)

if __name__=='__main__':
    main()
