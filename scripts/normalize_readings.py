"""Normalize stored readings to hiragana, keeping facts and review states separate."""
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz

TODAY = "2026-11-03"
# Explicit readings for symbols, a numeral, and source-confirmed misread words.
# These are item-level decisions, not generic pronunciation substitutions.
CORRECTIONS = {
    "Q001025": ("しゃるけぜろよん", "https://www.descente.co.jp/jp/press_releases/post-44162/", "シャルケ04(ゼロヨン)の表記"),
    "Q001566": ("だめんずうぉーかー", None, "既存の発音を保ち、長音に使われた波ダッシュを長音符に統一"),
    "Q002095": ("こころ", None, "既存表記「こゝろ」の同音反復記号を展開"),
    "Q002703": ("ななお", "https://nanao-fc.com/contents/menu/87767", "公式名称NANAOと菜々緒の対応"),
    "Q002762": ("いだてんとうきょうおりむぴっくばなし", "https://www.nhk-ep.com/products/detail/h23680AA", "紹介文の東京オリムピック噺（ばなし）"),
    "Q002767": ("がーるずあんどぱんつぁー", "https://www.kadokawa.co.jp/product/301602000311/", "電子版名のガールズアンドパンツァー"),
    "Q002870": ("わかおかみはしょうがくせい", "https://www.kodansha.co.jp/comic/products/0000043613", "タイトル読みワカオカミハショウガクセイ"),
}


def normalize_reading(value):
    value = unicodedata.normalize("NFKC", value)
    value = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in value)
    return re.sub(r"[\s=☆!！]", "", value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    by_id = {r["ID"]: r for r in reviews}
    changes = []
    unresolved = []
    for question in questions:
        qid = question["ID"]
        before = question["答えjson"][1]
        if re.fullmatch(r"[ぁ-ゖー]+", before):
            continue
        after = normalize_reading(before)
        evidence = None
        reason = "既存の読みの発音を変えずにカタカナをひらがなへ変換し、読み上げない空白・区切り記号・装飾記号を除去。事実・分類・難易度・タグの確認とは別。"
        if qid in CORRECTIONS:
            after, url, locator = CORRECTIONS[qid]
            reason = locator + "。ひらがな入力に対応する読みを登録。問題全体の事実照合とは別。"
            if url:
                evidence = {"source": url, "locator": locator, "checked_on": TODAY}
        if not re.fullmatch(r"[ぁ-ゖー]+", after):
            unresolved.append({"ID": qid, "before": before, "suggested": after})
            continue
        review = by_id[qid]
        changes.append({"ID": qid, "answer": question["答えjson"][0], "before": before, "after": after,
                        "previous_version": review["version"], "reason": reason, "evidence": evidence})
        question["答えjson"][1] = after
        review["version"] += 1
        review.setdefault("change_history", []).append({
            "version": review["version"], "date": TODAY, "fields": ["答えjson"], "reason": reason,
        })
        review["reading_format_review"] = {"checked_on": TODAY, "batch": "019", "before": before, "after": after, "scope": "hiragana input representation"}
        if evidence:
            review["reading_format_review"]["evidence"] = evidence
    if unresolved:
        raise ValueError("Readings need manual decisions: " + json.dumps(unresolved, ensure_ascii=True))
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise ValueError("\n".join(errors))
    if args.apply:
        if not changes:
            print("No reading format changes needed")
            return
        for name, rows in (("questions", questions), ("reviews", reviews)):
            (ROOT / f"data/{name}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        (ROOT / "data/audits/batch-019-reading-format.json").write_text(json.dumps({
            "checked_on": TODAY, "total_checked": len(questions), "changed": len(changes),
            "invalid_remaining": 0, "scope": "Reading format and the explicitly cited pronunciation fixes only. Review statuses were preserved.",
            "changes": changes,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for state, filename in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
            quiz.export_csv(questions, reviews, state, ROOT / f"data/quiz_{filename}.csv")
    print("checked", len(questions), "changes", len(changes), "unresolved", len(unresolved), "applied", args.apply)


if __name__ == "__main__":
    main()
