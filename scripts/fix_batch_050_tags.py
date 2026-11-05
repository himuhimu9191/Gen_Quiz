"""Restore the distinct answer-kind tag after batch 050 source-label cleanup."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import quiz

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-05"
def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    audit_path = ROOT / "data/audits/batch-050.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit_by_id = {change["ID"]: change for change in audit["changes"]}
    review_by_id = {review["ID"]: review for review in reviews}
    changed = []
    for question in questions:
        if len(question["タグ"]) >= 2 or question["ID"] not in audit_by_id:
            continue
        review = review_by_id[question["ID"]]
        area_tag = question["ジャンル"]
        if area_tag == question["タグ"][0]:
            raise ValueError(f"Could not restore distinct tag for {question['ID']}")
        before = copy.deepcopy(question)
        question["タグ"].append(area_tag)
        review["version"] += 1
        review.setdefault("change_history", []).append({
            "version": review["version"],
            "date": TODAY,
            "fields": ["タグ"],
            "reason": "内容領域タグが対象種別タグと重なるため、重複しない上位ジャンルタグを採用。",
        })
        review["tag_review"] = {
            "checked_on": TODAY,
            "method": "内容領域タグが対象種別タグと重なる78問は、上位ジャンルを内容領域タグとして採用。",
            "tags": question["タグ"],
        }
        audit_by_id[question["ID"]]["after"] = copy.deepcopy(question)
        audit_by_id[question["ID"]]["version"] = review["version"]
        audit_by_id[question["ID"]]["fields"] = ["解説", "タグ"]
        changed.append(question["ID"])
    if not changed:
        print("No single-tag rows need repair.")
        return
    errors, _ = quiz.validate(questions, reviews)
    if errors:
        raise ValueError("\n".join(errors[:20]))
    write_jsonl(ROOT / "data/questions.jsonl", questions)
    write_jsonl(ROOT / "data/reviews.jsonl", reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit["tag_repaired"] = len(changed)
    audit["changes"] = list(audit_by_id.values())
    with audit_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"tag_repaired": len(changed), "first": changed[0], "last": changed[-1]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
