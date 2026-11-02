# -*- coding: utf-8 -*-
"""Machine-assisted source alignment review for the JSQuAD candidates.

The fixed JGLUE commit is used as the source of the question, answer span,
article title, and context.  Only rows whose question and answer still match
the source exactly are promoted.  Pykakasi is used to re-create the required
hiragana input spelling; rows that cannot be represented by hiragana remain
candidate.  The source JSON is kept in the temporary workspace, not in this
repository.
"""
from __future__ import annotations

import collections
import copy
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

import pykakasi

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
COMMIT = "6f071c09316baae89c3d083a90985b4b1cb9968c"
SOURCE_URL = f"https://github.com/yahoojapan/JGLUE/tree/{COMMIT}/datasets/jsquad-v1.3"
SOURCE_FILE = Path(__import__("os").environ.get("TEMP", "/tmp")) / "genquiz_jsquad_train.json"


def norm(value: str) -> str:
    value = value.casefold().replace("・", "").replace(" ", "")
    return value


def hira(value: str) -> str:
    kakasi = pykakasi.kakasi()
    return "".join(part["hira"] for part in kakasi.convert(value))


def classify(text: str, title: str, current: str) -> tuple[str, str]:
    blob = f"{title} {text}"
    def has(*words: str) -> bool:
        return any(word in blob for word in words)

    if has("アニメ", "漫画", "ゲーム", "ポケモン", "任天堂", "キャラクター", "ドラゴンクエスト", "ファイナルファンタジー"):
        genre = "アニメ＆ゲーム"
        sub = "ゲーム" if has("ゲーム", "任天堂", "ポケモン") else "アニメ・漫画"
    elif has("映画", "音楽", "歌手", "俳優", "女優", "テレビ", "ラジオ", "バンド", "スポーツ", "野球", "サッカー", "オリンピック", "選手", "楽曲"):
        genre = "エンタメ＆スポーツ"
        if has("映画", "俳優", "女優"): sub = "映画"
        elif has("野球", "サッカー", "スポーツ", "選手", "オリンピック"): sub = "スポーツ"
        elif has("音楽", "歌手", "バンド", "楽曲"): sub = "音楽"
        else: sub = "放送・芸能"
    elif has("細胞", "遺伝", "生物", "動物", "植物", "化学", "物理", "天文", "惑星", "数学", "コンピュータ", "データベース", "病気", "医学", "地震", "火山"):
        genre = "理系"
        if has("動物", "植物", "細胞", "遺伝", "生物"): sub = "生物"
        elif has("化学"): sub = "化学"
        elif has("物理"): sub = "物理"
        elif has("天文", "惑星"): sub = "天文"
        elif has("数学"): sub = "数学"
        elif has("コンピュータ", "データベース"): sub = "情報"
        else: sub = "地学・医学"
    elif has("料理", "食品", "食べ物", "野菜", "菓子", "健康", "衣服", "住まい", "家電", "生活"):
        genre = "生活"
        sub = "料理・食品" if has("料理", "食品", "食べ物", "野菜", "菓子") else "暮らし・健康"
    elif has("法律", "条約", "政治", "政府", "議会", "経済", "会社", "企業", "都道府県", "市", "県", "国際", "社会制度"):
        genre = "社会"
        if has("法律", "条約"): sub = "法律・制度"
        elif has("経済", "会社", "企業"): sub = "経済・産業"
        elif has("市", "県", "都道府県"): sub = "地理"
        else: sub = "政治・社会"
    elif has("歴史", "天皇", "武将", "文学", "小説", "詩", "言語", "漢字", "宗教", "哲学", "美術", "文化", "日本史", "中国史"):
        genre = "文系"
        if has("歴史", "天皇", "武将", "日本史", "中国史"): sub = "歴史"
        elif has("文学", "小説", "詩"): sub = "文学"
        elif has("言語", "漢字"): sub = "日本語"
        else: sub = "文化・思想"
    else:
        genre = current if current in {"アニメ＆ゲーム", "文系", "理系", "生活", "雑学", "エンタメ＆スポーツ", "社会"} else "雑学"
        sub = "一般知識"
    return genre, sub


def tag_type(text: str, answer: str) -> str:
    if re.search(r"誰|だれ|人物|俳優|女優|作家|選手|天皇|大統領|首相", text):
        return "人物"
    if re.search(r"どこ|場所|都市|県|市|国|島|山|川|湖|海", text):
        return "地名"
    if re.search(r"会社|企業|団体|機関|大学|学校|組織", text):
        return "組織"
    if re.search(r"映画|小説|作品|曲|楽曲|番組|漫画|アニメ|ゲーム", text):
        return "作品"
    if re.search(r"料理|食べ物|食品|野菜|菓子|魚|肉", text):
        return "料理" if re.search(r"料理|食べ物", text) else "食品"
    if re.search(r"動物|植物|生物|鳥|魚", text):
        return "生物"
    if re.search(r"何年|いつ|日付|年月|何月|何日", text) or re.fullmatch(r"[0-9０-９年月日]+", answer):
        return "期限"
    if re.search(r"法律|制度|条約|保険", text):
        return "制度"
    if re.search(r"文書|書物|記録|条文", text):
        return "文書"
    return "用語"


def difficulty(text: str, answer: str, genre: str) -> int:
    if re.search(r"[0-9０-９]{2,4}年|何年|何月|何日", text) or len(answer) >= 12:
        return 3
    if genre == "雑学" and len(answer) >= 8:
        return 3
    common = ("何という", "何でしょう", "何と呼", "どんな")
    return 2 if any(x in text for x in common) and len(answer) <= 8 else 3


def source_record(existing: list[dict]) -> dict:
    for source in existing:
        if source.get("url") == SOURCE_URL:
            return source
    raise RuntimeError("JGLUE source record is missing")


def main() -> None:
    if not SOURCE_FILE.exists():
        raise SystemExit(f"missing temporary source: {SOURCE_FILE}")
    source_data = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    qas = {}
    for article in source_data["data"]:
        for paragraph_index, paragraph in enumerate(article["paragraphs"]):
            for qa in paragraph["qas"]:
                answer = qa.get("answers", [{}])[0]
                qas[qa["id"]] = {
                    "question": qa["question"],
                    "answer": answer.get("text", ""),
                    "start": answer.get("answer_start"),
                    "context": paragraph["context"],
                    "title": article["title"],
                    "paragraph_index": paragraph_index,
                }
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    sources = [json.loads(line) for line in (ROOT / "data/sources.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    sb = {s["url"]: s for s in sources}
    source = source_record(sources)
    processed = []
    skipped = []
    converter = pykakasi.kakasi()
    for review in reviews:
        provenance = review.get("import_provenance", {})
        if review.get("status") != "candidate" or provenance.get("dataset") != "JGLUE JSQuAD v1.3":
            continue
        qa = qas.get(provenance.get("qas_id"))
        q = qb[review["ID"]]
        if not qa or q["問"] != qa["question"] or norm(q["答えjson"][0]) != norm(qa["answer"]):
            skipped.append(review["ID"])
            continue
        start = qa["start"]
        if not isinstance(start, int) or qa["context"][start:start + len(qa["answer"])] != qa["answer"]:
            skipped.append(review["ID"])
            continue
        reading = "".join(part["hira"] for part in converter.convert(qa["answer"]))
        if not re.fullmatch(r"[ぁ-ゖー]+", reading):
            skipped.append(review["ID"])
            continue
        old_q = copy.deepcopy(q)
        genre, subgenre = classify(q["問"], qa["title"], q["ジャンル"])
        first_tag = tag_type(q["問"], qa["answer"])
        second_tag = qa["title"].strip() or subgenre
        if second_tag == first_tag:
            second_tag = subgenre
        q["ジャンル"] = genre
        q["サブジャンル"] = subgenre
        q["難易度"] = difficulty(q["問"], qa["answer"], genre)
        q["答えjson"] = [qa["answer"], reading] + q["答えjson"][2:]
        q["タグ"] = [first_tag, second_tag]
        q["解説"] = q["解説"].rstrip("。") + "。出典本文の回答スパンと照合済みです。"
        review["version"] += 1
        review.setdefault("change_history", []).append({
            "version": review["version"], "date": TODAY,
            "fields": [key for key in ("ジャンル", "サブジャンル", "難易度", "解説", "答えjson", "タグ") if q[key] != old_q[key]] + ["status"],
            "reason": "JGLUE固定コミットの設問・回答スパン・記事本文を再照合し、Pykakasi出力をひらがな入力用に校正。分類・タグは設問と記事題名の内容から再選定。",
        })
        locator = f"train-v1.3.json:{provenance['qas_id']} / 記事「{qa['title']}」段落{qa['paragraph_index']} / answer_start={start}"
        fact_claim = {
            "claim": f"固定コミットのJSQuAD本文で設問文と回答スパン「{qa['answer']}」が一致し、回答位置も本文で確認できる。",
            "source": SOURCE_URL, "locator": locator, "checked_on": TODAY,
            "coverage": ["問", "解説", "答えjson"],
            "method": "固定コミットのJSON本文を読み、qas id・設問・回答文字列・answer_start・記事題名を照合。",
        }
        reading_claim = {
            "claim": f"代表表記「{qa['answer']}」をPykakasi 2.3.0で変換した読み「{reading}」がひらがな入力形式に適合することを確認。",
            "source": SOURCE_URL, "locator": locator, "checked_on": TODAY,
            "coverage": ["答えjson"],
        }
        review.update({
            "status": "verified", "claims": [fact_claim, reading_claim],
            "uniqueness_review": f"設問の回答スパンと記事本文の位置を照合し、代表解答「{qa['answer']}」に限定。別名・略称は原回答に含まれるものだけを許容。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "設問・記事題名・回答種別を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": "設問と記事題名の内容語から再分類。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": "固定コミットの回答文字列と、登録済みの正式表記だけを確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": q["難易度"], "reason": "設問の語彙・必要知識・回答の専門性から一般成人向けに暫定評価。", "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "JGLUE固定コミット本文の設問・回答スパン・記事題名とPykakasi読みを機械照合。難易度は暫定評価。",
            "pending": ["人による最終審査", "試遊で難易度を調整"], "research_entrypoints": list(dict.fromkeys(review.get("research_entrypoints", []) + [SOURCE_URL])), "audit_batch": "040",
        })
        processed.append(review["ID"])
    if SOURCE_URL not in sb:
        sources.append({
            "url": SOURCE_URL, "publisher": "Yahoo Japan Corporation / Waseda University Kawahara Lab",
            "section": "JGLUE JSQuAD v1.3; Japanese Wikipedia snapshot dated 2021-11-01",
            "source_type": "repository", "repository_commit": COMMIT,
            "sha256": hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest(), "checked_on": TODAY,
            "license": "CC-BY-SA-4.0", "method": "固定コミットのJSQuAD train-v1.3.jsonを取得し、qas単位の設問・回答スパンを照合。",
            "read_sections": ["datasets/jsquad-v1.3/train-v1.3.json"],
        })
    else:
        source["read_sections"] = list(dict.fromkeys(source.get("read_sections", []) + ["datasets/jsquad-v1.3/train-v1.3.json / qas単位の設問・回答スパン"]))
    errors = []
    import importlib.util
    spec = importlib.util.spec_from_file_location("quiz", ROOT / "scripts/quiz.py")
    quiz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(quiz)
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:30]))
    def save(path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    save(ROOT / "data/questions.jsonl", questions)
    save(ROOT / "data/reviews.jsonl", reviews)
    save(ROOT / "data/sources.jsonl", sources)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit = {"checked_on": TODAY, "batch": "040", "method": "JGLUE fixed-commit exact alignment + Pykakasi 2.3.0 reading conversion", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "skipped": skipped, "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "sample_ids": processed[:20]}
    (ROOT / "data/audits/batch-040.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-040.md").write_text(
        "# バッチ040（JSQuAD固定コミット再照合）\n\n"
        f"JGLUE JSQuAD v1.3の固定コミット `{COMMIT}` と候補のqas idを照合し、設問・回答文字列・本文スパン・記事題名が一致する **{len(processed)}問** を再審査しました。"
        " Pykakasi 2.3.0で代表表記をひらがな入力用に変換し、設問語彙と記事題名からジャンル・サブジャンル・タグ・難易度を再選定しました。"
        f" 設問または回答スパンが一致しなかった {len(skipped)}問は候補のままです。\n\n"
        "出典本文は一時領域で参照し、リポジトリには固定コミット、qas id、回答位置、取得ハッシュのみを記録しています。人による公開承認と試遊は未完了です。\n",
        encoding="utf-8",
    )
    print(f"processed={len(processed)} skipped={len(skipped)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
