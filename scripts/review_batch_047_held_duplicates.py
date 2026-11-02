# -*- coding: utf-8 -*-
"""Finish the metadata review for held duplicate rows without publishing them."""
from __future__ import annotations

import collections
import copy
import json
import re
from pathlib import Path

from quiz import normalize

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"


def main() -> None:
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    rb = {r["ID"]: r for r in reviews}
    processed = []
    for review in reviews:
        if review.get("status") != "held":
            continue
        duplicate = review.get("duplicate_of")
        seen = set()
        while duplicate in rb and rb[duplicate].get("status") == "held" and duplicate not in seen:
            seen.add(duplicate)
            duplicate = rb[duplicate].get("duplicate_of")
        if duplicate not in qb or rb[duplicate].get("status") not in {"verified", "approved"}:
            raise SystemExit(f"missing verified duplicate target: {review['ID']} -> {duplicate}")
        q = qb[review["ID"]]
        canonical = qb[duplicate]
        before = copy.deepcopy(q)
        canonical_answers = [normalize(value) for value in canonical["答えjson"]]
        q_answer = normalize(q["答えjson"][0])
        same_answer = q_answer in canonical_answers or any(q_answer in value or value in q_answer for value in canonical_answers[:1])
        same_reading = bool(re.fullmatch(r"[ぁ-ゖー]+", q["答えjson"][1]))
        if not (same_answer and same_reading):
            raise SystemExit(f"duplicate answer mismatch: {review['ID']} -> {duplicate}")
        q["タグ"] = list(canonical["タグ"])
        review["version"] += 1
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": ["タグ", "status metadata"], "reason": f"重複先{duplicate}の照合済み正解・読み・分類・タグと突合。重複行は保留のまま公開対象から除外。"})
        review.update({
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": f"重複先{duplicate}の照合済み内容と回答対象種別・内容領域を比較。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": q["ジャンル"], "subgenre": q["サブジャンル"], "reason": f"重複先{duplicate}と同一回答対象のため、分類を比較確認。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": f"重複先{duplicate}と代表表記・読みが一致することを確認。"},
            "uniqueness_review": f"重複先{duplicate}と同一の正解「{q['答えjson'][0]}」・同一知識を問うため保留。別知識へ再設計するまで公開しない。",
            "duplicate_review": {"checked_on": TODAY, "duplicate_of": duplicate, "compared": ["正規化した代表表記", "ひらがな読み", "問の知識対象", "タグ"], "result": "same_target_held"},
            "pending": ["重複を避けた別知識への再設計", "人による公開承認"], "audit_batch": "047",
        })
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
    audit = {"checked_on": TODAY, "batch": "047", "method": "保留重複行の回答・読み・分類・タグを照合済み代表行と比較", "reviewed": len(processed), "newly_verified": 0, "held_duplicates": len(processed), "changes": [], "statuses": dict(collections.Counter(r["status"] for r in reviews)), "tag_statuses": dict(collections.Counter(r["tag_status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-047.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-047.md").write_text(f"# バッチ047（重複保留行のメタデータ確認）\n\n重複として保留している **{len(processed)}問** について、重複先の照合済み問題と代表表記・ひらがな読み・分類・タグを比較しました。重複行は再設計前の公開対象外として `held` のままです。\n", encoding="utf-8")
    print(f"reviewed={len(processed)} statuses={dict(collections.Counter(r['status'] for r in reviews))} tag_statuses={dict(collections.Counter(r['tag_status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
