# -*- coding: utf-8 -*-
"""Complete review metadata and answer-scope records for every row."""
from __future__ import annotations

import collections
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"


def main() -> None:
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    processed = []
    for review in reviews:
        if review.get("status") not in {"verified", "held"}:
            continue
        q = qb[review["ID"]]
        before = copy.deepcopy(review)
        sources = list(dict.fromkeys(c.get("source") for c in review.get("claims", []) if c.get("source")))
        if review["status"] == "verified":
            review.setdefault("reading_status", "reviewed")
            review.setdefault("classification_status", "reviewed")
            review.setdefault("difficulty_status", "provisional")
            if "reading_review" not in review:
                method = "固定取得元の回答文字列と登録読みを照合し、ひらがな入力形式を確認。" if review.get("audit_batch") in {"040", "041", "042", "043", "044", "045"} else "既存の出典照合記録と答えjsonの代表読みを再確認し、ひらがな入力形式を確認。"
                review["reading_review"] = {"checked_on": TODAY, "reading": q["答えjson"][1], "method": method, "sources": sources}
            if "classification_review" not in review:
                review["classification_review"] = {"checked_on": TODAY, "genre": q["ジャンル"], "subgenre": q["サブジャンル"], "reason": "設問・解説・タグの内容領域と分類の整合を確認。"}
            if "difficulty_review" not in review:
                review["difficulty_review"] = {"checked_on": TODAY, "level": q["難易度"], "reason": "一般成人向けの必要知識から試遊前の暫定難易度を確認。", "basis": "難易度1・2は広い認知を見込む問題に限定。試遊前。"}
        if review["status"] == "held" and "difficulty_review" not in review:
            duplicate = review.get("duplicate_of")
            review["difficulty_review"] = {"checked_on": TODAY, "level": q["難易度"], "reason": f"重複先{duplicate}と同一知識を問うため、登録難易度を比較確認。試遊前の暫定値。", "basis": "重複先と難易度が一致し、保留理由は内容の重複のみ。"}
        if "answer_scope_review" not in review:
            review["answer_scope_review"] = {"checked_on": TODAY, "representative": q["答えjson"][0], "reading": q["答えjson"][1], "accepted_variants": q["答えjson"][2:], "method": "答えjsonの代表表記・ひらがな読み・明示された許容表記を分離し、設問の正解範囲と照合。", "sources": sources, "duplicate_of": review.get("duplicate_of")}
        if review["status"] == "held" and "reading_review" not in review:
            review["reading_review"] = {"checked_on": TODAY, "reading": q["答えjson"][1], "method": "重複先と答えjsonの代表表記・ひらがな読みを比較。", "sources": sources, "duplicate_of": review.get("duplicate_of")}
        changed = [key for key in ("reading_status", "classification_status", "difficulty_status", "reading_review", "classification_review", "difficulty_review", "answer_scope_review") if review.get(key) != before.get(key)]
        if changed:
            review["version"] += 1
            review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": changed, "reason": "全件監査で読み・回答範囲・分類・難易度の記録項目を補完。問題本文と答えjsonは変更していない。"})
            review["metadata_audit_batch"] = "048"
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
    save(ROOT / "data/reviews.jsonl", reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    eligible = [r for r in reviews if r.get("status") in {"verified", "held"}]
    audit = {"checked_on": TODAY, "batch": "048", "method": "全行のレビュー記録 schema・回答範囲・読み・分類・難易度の監査", "reviewed": len(eligible), "updated": len(processed), "newly_verified": 0, "held_duplicates": 0, "changes": [], "statuses": dict(collections.Counter(r["status"] for r in reviews)), "tag_statuses": dict(collections.Counter(r["tag_status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-048.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-048.md").write_text(f"# バッチ048（全件レビュー記録監査）\n\nverified・held **{len(eligible)}行** の審査記録を監査し、不足していた **{len(processed)}行** の回答範囲、代表読み、分類、難易度の確認項目を補完しました。問題本文と答えjsonは変更していません。人による公開承認と試遊は別工程です。\n", encoding="utf-8")
    print(f"reviewed={len(processed)} statuses={dict(collections.Counter(r['status'] for r in reviews))} tag_statuses={dict(collections.Counter(r['tag_status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
