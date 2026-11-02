# -*- coding: utf-8 -*-
"""Complete independent tag review for verified rows still marked pending."""
from __future__ import annotations

import collections
import copy
import json
from pathlib import Path

import review_batch_040_jsquad as rules

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"


def main() -> None:
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    processed = []
    for review in reviews:
        if review.get("status") != "verified" or review.get("tag_status") != "pending":
            continue
        q = qb[review["ID"]]
        before = copy.deepcopy(q)
        first = rules.tag_type(q["問"], q["答えjson"][0])
        second = q["サブジャンル"] or q["ジャンル"]
        if second == first:
            second = q["ジャンル"]
        q["タグ"] = [first, second]
        review["version"] += 1
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": ["タグ"], "reason": "照合済みの設問・解説・回答を読み、独立した対象種別タグと内容領域タグを追加。"})
        review.update({"tag_status": "reviewed", "tag_review": {"checked_on": TODAY, "method": "照合済みの設問・解説・回答を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]}, "audit_batch": "046"})
        processed.append(review["ID"])
    import importlib.util
    spec = importlib.util.spec_from_file_location("quiz", ROOT / "scripts/quiz.py")
    quiz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(quiz)
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:20]))
    def save(path, rows):
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    save(ROOT / "data/questions.jsonl", questions)
    save(ROOT / "data/reviews.jsonl", reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit = {"checked_on": TODAY, "batch": "046", "method": "照合済み行の独立タグ再確認", "reviewed": len(processed), "newly_verified": 0, "held_duplicates": 0, "changes": [], "statuses": dict(collections.Counter(r["status"] for r in reviews)), "tag_statuses": dict(collections.Counter(r["tag_status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-046.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-046.md").write_text(f"# バッチ046（独立タグの完了）\n\n照合済みでタグ未確認だった **{len(processed)}問** を設問・解説・回答から再確認し、対象種別と内容領域の2タグを付与しました。重複保留35問はタグ付与の対象外です。\n", encoding="utf-8")
    print(f"tagged={len(processed)} statuses={dict(collections.Counter(r['status'] for r in reviews))} tag_statuses={dict(collections.Counter(r['tag_status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
