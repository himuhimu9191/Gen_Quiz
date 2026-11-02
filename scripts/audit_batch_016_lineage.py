"""Audit batch 016 against the pinned local source datasets.

This records source-lineage and answer-span results but deliberately leaves
questions candidate until facts, readings, classification, tags, and quality
are checked independently.
"""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP = Path(os.environ["TEMP"]) / "genquiz_sources"
TODAY = "2026-11-03"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def main():
    questions = {q["ID"]: q for q in read_jsonl(ROOT / "data/questions.jsonl")}
    reviews = read_jsonl(ROOT / "data/reviews.jsonl")
    batch = [r for r in reviews if r.get("batch") == "016"]

    aio = {}
    for line in (TEMP.parent / "aio_02_train.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        aio[row["qid"]] = row

    jqac = {}
    for path in sorted((TEMP / "jqac" / "jqac").glob("*.csv")):
        if path.name.startswith("._"):
            continue
        with path.open(encoding="utf-8", newline="") as stream:
            for index, row in enumerate(csv.DictReader(stream), start=1):
                jqac[f"{path.stem}:{index}"] = row

    jsquad = {}
    for name in ("train-v1.3.json", "valid-v1.3.json", "test-v1.3.json"):
        data = json.loads((TEMP / "jglue" / "datasets" / "jsquad-v1.3" / name).read_text(encoding="utf-8"))
        for article in data["data"]:
            for paragraph_index, paragraph in enumerate(article["paragraphs"]):
                for qa in paragraph["qas"]:
                    jsquad[f"{name}:{qa['id']}"] = {
                        "title": article["title"], "paragraph_index": paragraph_index,
                        "context": paragraph["context"], "qa": qa,
                    }

    summary = {
        "checked_on": TODAY,
        "batch": "016",
        "total": len(batch),
        "sources": {"aio": 0, "jqac": 0, "jsquad": 0},
        "matches": {"source_hash": 0, "prompt": 0, "answer": 0, "answer_span": 0, "article_title": 0, "reference_url": 0},
        "prompt_mismatches": [],
        "missing": [],
        "reading_check": {"method": "Stored second answer must consist of hiragana or the prolonged sound mark; pronunciation is not checked", "format_valid": 0, "format_invalid": 0},
        "note": "Lineage and answer-span checks do not establish factual correctness, natural Japanese, unique answerability, pronunciation, classification, difficulty, tags, or human approval.",
    }

    for review in batch:
        qid = review["ID"]
        question = questions[qid]
        provenance = review["import_provenance"]
        source_id = provenance["source_id"]
        alignment = {"checked_on": TODAY, "source_id": source_id, "dataset": provenance["dataset"]}
        if provenance["dataset"].startswith("AI王"):
            summary["sources"]["aio"] += 1
            row = aio.get(source_id)
            if row is None:
                summary["missing"].append(qid)
                alignment["missing"] = True
            else:
                prompt_match = row.get("question") == question["問"]
                answer_match = bool(row.get("answers")) and row["answers"][0] == question["答えjson"][0]
                hash_match = sha256_json(row) == provenance.get("source_question_sha256")
                alignment.update({"source_hash_match": hash_match, "prompt_match": prompt_match, "answer_match": answer_match})
                summary["matches"]["source_hash"] += int(hash_match)
                summary["matches"]["prompt"] += int(prompt_match)
                summary["matches"]["answer"] += int(answer_match)
                if not prompt_match:
                    summary["prompt_mismatches"].append({"ID": qid, "source_id": source_id, "reason": "reviewed question wording"})
        elif provenance["dataset"].startswith("Japanese Question"):
            summary["sources"]["jqac"] += 1
            row = jqac.get(source_id)
            if row is None:
                summary["missing"].append(qid)
                alignment["missing"] = True
            else:
                prompt_match = row["Question (What, Who, Where, Whose, How, Yes/No)"].strip() == question["問"]
                answer_match = row["Answer"].strip() == question["答えjson"][0]
                reference_match = row["URL (Original Content)"].strip() == provenance.get("reference_url")
                alignment.update({"prompt_match": prompt_match, "answer_match": answer_match, "reference_url_match": reference_match})
                summary["matches"]["prompt"] += int(prompt_match)
                summary["matches"]["answer"] += int(answer_match)
                summary["matches"]["reference_url"] += int(reference_match)
        else:
            summary["sources"]["jsquad"] += 1
            row = jsquad.get(source_id)
            if row is None:
                summary["missing"].append(qid)
                alignment["missing"] = True
            else:
                qa = row["qa"]
                prompt_match = qa["question"].strip() == question["問"]
                answer_match = question["答えjson"][0] in {a["text"].strip() for a in qa["answers"] if a.get("text", "").strip()}
                answer_span_match = all(row["context"][a["answer_start"]:a["answer_start"] + len(a["text"])] == a["text"] for a in qa["answers"] if a.get("text", "").strip())
                title_match = row["title"] == provenance.get("article_title")
                alignment.update({"prompt_match": prompt_match, "answer_match": answer_match, "answer_span_match": answer_span_match, "article_title_match": title_match})
                summary["matches"]["prompt"] += int(prompt_match)
                summary["matches"]["answer"] += int(answer_match)
                summary["matches"]["answer_span"] += int(answer_span_match)
                summary["matches"]["article_title"] += int(title_match)

        reading = question["答えjson"][1]
        valid = bool(reading) and all("ぁ" <= char <= "ゖ" or char == "ー" for char in reading)
        summary["reading_check"]["format_valid" if valid else "format_invalid"] += 1
        alignment["reading_format_valid"] = valid
        review["source_alignment"] = alignment
        if review["status"] == "candidate":
            review["pending"] = [
                "出典本文による事実確認", "正解の一意性・許容表記の審査",
                "ひらがな読みの個別校正", "ジャンル・サブジャンル・難易度の再審査",
                "タグの確認", "人による最終審査",
            ]

    (ROOT / "data/reviews.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in reviews), encoding="utf-8")
    (ROOT / "data/audits/batch-016-lineage.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
