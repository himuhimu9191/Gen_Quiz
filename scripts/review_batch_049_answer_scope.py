# -*- coding: utf-8 -*-
"""Remove generic series suffixes from answers when the prompt asks for the series name."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"

UPDATES = {
    "Q000028": {
        "old": ["レイトン教授シリーズ", "れいとんきょうじゅしりーず"],
        "new": ["レイトン教授", "れいとんきょうじゅ"],
        "reason": "設問はレベルファイブのゲームシリーズ名を尋ねており、末尾の一般分類語「シリーズ」は正解名に含めない。",
    },
    "Q005723": {
        "old": ["スーパーロボット大戦シリーズ", "すーぱーろぼっとたいせんしりーず"],
        "new": ["スーパーロボット大戦", "すーぱーろぼっとたいせん"],
        "reason": "設問の「何大戦シリーズか」はシリーズ名を尋ねており、末尾の一般分類語「シリーズ」は正解名に含めない。",
    },
}


def main() -> None:
    questions_path = ROOT / "data/questions.jsonl"
    reviews_path = ROOT / "data/reviews.jsonl"
    questions = [json.loads(line) for line in questions_path.read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in reviews_path.read_text(encoding="utf-8").splitlines() if line]
    question_by_id = {q["ID"]: q for q in questions}
    changed = []
    for qid, update in UPDATES.items():
        q = question_by_id[qid]
        review = next(r for r in reviews if r["ID"] == qid)
        if q["答えjson"] != update["old"]:
            raise SystemExit(f"unexpected answer for {qid}: {q['答えjson']}")
        before = copy.deepcopy(q["答えjson"])
        q["答えjson"] = update["new"]
        old_rejected = list(review.get("rejected_aliases", []))
        rejected = [a for a in old_rejected if a != update["new"][0]]
        old_full = update["old"][0]
        if old_full not in rejected:
            rejected.append(old_full)
        review["rejected_aliases"] = rejected
        review["answer_alias_review"] = {
            "checked_on": TODAY,
            "reason": "設問が尋ねる固有名詞を代表表記とし、一般分類語「シリーズ」を不許可表記として登録。",
        }
        review["uniqueness_review"] = update["reason"]
        review["reading_review"]["reading"] = update["new"][1]
        review["reading_review"]["method"] = "代表解答から一般分類語「シリーズ」を除いたひらがな読みを確認。"
        review["answer_scope_review"].update({
            "checked_on": TODAY,
            "representative": update["new"][0],
            "reading": update["new"][1],
            "accepted_variants": [],
            "method": "設問が求める固有名詞と一般分類語を分離し、シリーズ語を答えの範囲から除外。",
            "source_answer": update["old"][0],
            "scope_adjustment": "設問中の一般分類語「シリーズ」を代表解答から除外。",
        })
        review["version"] += 1
        review.setdefault("change_history", []).append({
            "version": review["version"],
            "date": TODAY,
            "fields": ["答えjson", "rejected_aliases", "reading_review", "answer_scope_review", "uniqueness_review"],
            "reason": update["reason"],
        })
        review["answer_scope_audit_batch"] = "049"
        changed.append({"ID": qid, "before": before, "after": update["new"], "reason": update["reason"]})

    import importlib.util
    spec = importlib.util.spec_from_file_location("quiz", ROOT / "scripts/quiz.py")
    quiz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(quiz)
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:20]))

    def save(path: Path, rows) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

    save(questions_path, questions)
    save(reviews_path, reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit = {
        "checked_on": TODAY,
        "batch": "049",
        "method": "設問が求めるシリーズ名から一般分類語「シリーズ」を除外する回答範囲監査",
        "reviewed": len(changed),
        "newly_verified": 0,
        "held_duplicates": 0,
        "changes": changed,
        "warnings": len(warnings),
    }
    (ROOT / "data/audits/batch-049.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-049.md").write_text(
        "# バッチ049（シリーズ名の回答範囲修正）\n\n"
        f"設問が求めるシリーズ名のうち **{len(changed)}問** で、答えに付いていた一般分類語「シリーズ」を除外しました。"
        "読みと不許可表記も更新し、作品名そのものだけを正解にします。\n\n"
        "[監査記録](../data/audits/batch-049.json)。人による公開承認と試遊は別工程です。\n",
        encoding="utf-8",
    )
    print(f"updated={len(changed)} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
