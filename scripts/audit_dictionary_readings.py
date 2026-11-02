"""Find reading disagreements and collect exact dictionary headwords for review.

Optional audit dependency: Janome (IPADIC), supplied via --library-directory.
The script never edits the quiz or marks a question verified.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz


def plain(fragment):
    fragment = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", fragment))).strip()


def lookup(row, cache):
    word = row["answer"]
    path = cache / (hashlib.sha256(word.encode("utf-8")).hexdigest() + ".json")
    if path.exists():
        try:
            return {**row, **json.loads(path.read_text(encoding="utf-8"))}
        except json.JSONDecodeError:
            pass
    try:
        request = urllib.request.Request("https://kotobank.jp/word/" + urllib.parse.quote(word), headers={"User-Agent": "GenQuizSourceAudit/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()
            url = response.url
        source = data.decode("utf-8")
        heading_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", source, re.S)
        heading = plain(heading_match.group(1)) if heading_match else ""
        parts = re.match(r"(.*?)\s*（読み）\s*(.*?)(?:\s*（その他表記）.*)?$", heading)
        headword = parts[1].strip() if parts else None
        reading = parts[2].strip() if parts else None
        result = {
            "url": url, "heading": heading, "headword": headword, "dictionary_reading": reading,
            "exact_headword": headword == word, "sha256": hashlib.sha256(data).hexdigest(),
            "checked_on": "2026-11-03", "lookup_status": "found" if parts else "no_reading_heading",
        }
        # Cached bytes are kept outside the repository for inspection.
        (cache / (path.stem + ".html")).write_bytes(data)
    except Exception as error:
        result = {"lookup_status": "unavailable", "error": f"{type(error).__name__}: {error}"}
    path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return {**row, **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library-directory", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.library_directory))
    from janome.tokenizer import Tokenizer
    tokenizer = Tokenizer()
    questions = quiz.load(ROOT / "data/questions.jsonl")
    differences = []
    for question in questions:
        tokens = list(tokenizer.tokenize(question["答えjson"][0]))
        if not all(token.reading != "*" for token in tokens):
            continue
        reading = quiz.normalize("".join(token.reading for token in tokens))
        if reading != quiz.normalize(question["答えjson"][1]):
            differences.append({"ID": question["ID"], "answer": question["答えjson"][0], "stored": question["答えjson"][1], "analyzer": reading})
    args.cache.mkdir(parents=True, exist_ok=True)
    unique_words = {row['answer']: {'answer': row['answer']} for row in differences}
    with ThreadPoolExecutor(max_workers=4) as executor:
        lookups = list(executor.map(lambda row: lookup(row, args.cache), unique_words.values()))
    by_word = {row['answer']: row for row in lookups}
    results = [{**row, **by_word[row['answer']]} for row in differences]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8")
    print("questions", len(questions), "differences", len(differences), "exact_dictionary_headings", sum(r.get("exact_headword", False) for r in results))


if __name__ == "__main__":
    main()
