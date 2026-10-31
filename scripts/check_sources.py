"""Re-fetch cited source versions and compare bytes; this does not verify facts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def raw_url(url):
    parts = urlsplit(url)
    if parts.scheme != 'https':
        raise ValueError('HTTPSの出典が必要です')
    if parts.hostname == 'github.com':
        owner, repo, blob, commit, *path = parts.path.strip('/').split('/')
        if blob != 'blob':
            raise ValueError('固定版のファイルURLが必要です')
        return f'https://raw.githubusercontent.com/{owner}/{repo}/{commit}/' + '/'.join(path)
    return url


def check(source):
    try:
        request = Request(raw_url(source['url']), headers={'User-Agent': 'GenQuizSourceCheck/1.0'})
        with urlopen(request, timeout=30) as response:
            data = response.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != source['sha256']:
            return source['url'], '保存したSHA-256と不一致'
        return source['url'], None
    except Exception as error:
        return source['url'], f'{type(error).__name__}: {error}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sources = [json.loads(line) for line in (root / 'data/sources.jsonl').read_text().splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check, sources))
    failures = [(url, error) for url, error in results if error]
    for url, error in failures:
        print(f'ERROR: {url}: {error}')
    print(f'出典本文の再取得・ハッシュ一致: {len(results) - len(failures)}/{len(results)}件')
    print('この確認は資料の復元性の検査です。事実照合や公開承認を自動実施するものではありません。')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
