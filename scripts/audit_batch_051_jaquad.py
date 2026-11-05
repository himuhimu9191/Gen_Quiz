"""Recheck batch 051 against the pinned local JaQuAD checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import quiz
from import_batch_051_jaquad import clean_answer, hiragana, sha256


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_rows(source_root: Path, expected_hashes: dict[str, str]) -> tuple[dict, dict]:
    lookup = {}
    seen_files = set()
    result = {
        "source_files_seen": 0,
        "source_files_expected": len(expected_hashes),
        "source_files_missing": 0,
        "source_file_hash_mismatch": 0,
    }
    for split in ("train", "dev"):
        for path in sorted((source_root / "data" / split).glob("*.json")):
            result["source_files_seen"] += 1
            seen_files.add(path.name)
            expected = expected_hashes.get(path.name)
            if expected and file_hash(path) != expected:
                result["source_file_hash_mismatch"] += 1
            payload = json.loads(path.read_text(encoding="utf-8"))
            for article in payload.get("data", []):
                for paragraph in article.get("paragraphs", []):
                    context = paragraph.get("context", "")
                    for qa in paragraph.get("qas", []):
                        source_id = f"{split}/{path.name}:{qa.get('id')}"
                        lookup[source_id] = (context, qa)
    result["source_files_missing"] = len(set(expected_hashes) - seen_files)
    return lookup, result


def audit(source_root: Path) -> dict:
    manifest_path = ROOT / "data/imports/batch-051-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_hashes = manifest["source_file_sha256"]
    source, result = source_rows(source_root, expected_hashes)
    questions = {
        question["ID"]: question
        for question in quiz.load(ROOT / "data/questions.jsonl")
        if "Q007001" <= question["ID"] <= "Q010500"
    }
    reviews = [
        review
        for review in quiz.load(ROOT / "data/reviews.jsonl")
        if review.get("batch") == "051"
    ]
    result.update({
        "expected_rows": manifest["selected"],
        "rows": len(reviews),
        "question_rows": len(questions),
        "review_row_count_mismatch": abs(len(reviews) - manifest["selected"]),
        "question_row_count_mismatch": abs(len(questions) - manifest["selected"]),
        "source_id_missing": 0,
        "question_mismatch": 0,
        "answer_mismatch": 0,
        "context_hash_mismatch": 0,
        "answer_span_mismatch": 0,
        "reading_mismatch": 0,
    })
    for review in reviews:
        provenance = review["import_provenance"]
        question = questions.get(review["ID"])
        entry = source.get(provenance.get("source_id"))
        if question is None or entry is None:
            result["source_id_missing"] += 1
            continue
        context, source_question = entry
        original_question = provenance["original_question"]
        original_answer = provenance["original_answer"]
        result["question_mismatch"] += int(
            source_question.get("question", "").strip() != original_question
        )
        answers = [
            answer for answer in source_question.get("answers", [])
            if answer.get("text", "").strip()
        ]
        result["answer_mismatch"] += int(not any(
            answer.get("answer_start") == provenance.get("answer_start")
            and answer.get("text", "").strip() == original_answer
            for answer in answers
        ))
        result["context_hash_mismatch"] += int(
            sha256(context) != provenance.get("context_sha256")
        )
        start = provenance.get("answer_start")
        result["answer_span_mismatch"] += int(
            type(start) is not int
            or context[start:start + len(original_answer)] != original_answer
        )
        expected_answer = clean_answer(original_answer)
        result["reading_mismatch"] += int(
            question["答えjson"][:2] != [expected_answer, hiragana(expected_answer)]
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.source_root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    failures = [key for key, value in result.items() if key.endswith("mismatch") or key.endswith("missing")]
    if any(result[key] for key in failures):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
