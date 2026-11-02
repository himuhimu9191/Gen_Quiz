"""Apply the source review for batch 018 without approving public release."""
import collections
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
sys.path.insert(0, str(ROOT / "scripts"))
import quiz

SOURCES = [
    {
        "source_type": "web",
        "url": "https://openstax.org/books/biology-2e/pages/8-1-overview-of-photosynthesis",
        "publisher": "OpenStax / Rice University",
        "section": "Biology 2e, 8.1 Overview of Photosynthesis",
        "sha256": "e68bc87f203937f2d5bce1fbb03135b09107f74231f1382f0c25ca1a3d1684e5",
        "checked_on": TODAY,
        "method": "本文を読み、葉緑体・光合成・チラコイド・ストロマの説明を照合。",
        "read_sections": ["paragraphs 51-56"],
    },
    {
        "source_type": "web",
        "url": "https://kotobank.jp/word/%E8%91%89%E7%B7%91%E4%BD%93-145897?s=yap",
        "publisher": "コトバンク（小学館デジタル大辞泉、精選版 日本国語大辞典）",
        "section": "葉緑体",
        "sha256": "fd419ecae98c72d9e571fefd8714a1378bbdb5b9c5be9942cb3eca80ad4f33dd",
        "checked_on": TODAY,
        "method": "辞書本文で読みと葉緑体の定義を照合。",
        "read_sections": ["デジタル大辞泉「葉緑体」", "精選版 日本国語大辞典「葉緑体」"],
    },
    {
        "source_type": "web",
        "url": "https://www.meihaku.jp/sword-basic/about-mineuchi/",
        "publisher": "名古屋刀剣博物館／名古屋刀剣ワールド",
        "section": "峰打ちとは",
        "sha256": "eabbd9faeb8935dc9ff53fc5b7c8ef870f059b133a2ef681bca59658f01e6a92",
        "checked_on": TODAY,
        "method": "博物館解説本文を読み、峰・棟の位置と峰打ちの定義を照合。",
        "read_sections": ["峰打ちの定義", "峰打ちはどうやるのか"],
    },
    {
        "source_type": "web",
        "url": "https://imidas.jp/kojiten/detail/W-32-0-396-06.html",
        "publisher": "imidas 広辞典",
        "section": "峰打ち",
        "sha256": "b46fabde68a0864a3e67e6b70e4b39c3ed7a141d7aa732d54eb78f0329605ecc",
        "checked_on": TODAY,
        "method": "辞書項目で見出しの読みと意味を照合。",
        "read_sections": ["見出し「峰打ち（みねうち）」"],
    },
    {
        "source_type": "web",
        "url": "https://kotobank.jp/word/%E5%88%87%E6%8D%A8%E5%BE%A1%E5%85%8D-1159878",
        "publisher": "コトバンク（精選版 日本国語大辞典、改訂新版 世界大百科事典ほか）",
        "section": "切捨御免",
        "sha256": "01112bb83782dbc994f40257e40bfa83677c50446626c505d10212824403c353",
        "checked_on": TODAY,
        "method": "辞書・百科事典本文を読み、読み、特権の条件と制限を照合。",
        "read_sections": ["精選版 日本国語大辞典「切捨御免」", "改訂新版 世界大百科事典「切捨御免」"],
    },
]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def claim(text, source, locator, coverage):
    return {"claim": text, "source": source, "locator": locator, "checked_on": TODAY, "coverage": coverage}


def record_change(review, fields, reason):
    review["version"] += 1
    review.setdefault("change_history", []).append({
        "version": review["version"], "date": TODAY, "fields": fields, "reason": reason,
    })


def verify(review, sources, claims, uniqueness, tags, method):
    review.update({
        "status": "verified",
        "difficulty_status": "provisional",
        "research_entrypoints": sources,
        "claims": claims,
        "uniqueness_review": uniqueness,
        "pending": ["人による最終審査", "試遊で難易度を調整"],
        "reading_status": "reviewed",
        "classification_status": "reviewed",
        "tag_status": "reviewed",
        "tag_review": {"checked_on": TODAY, "method": method, "tags": tags},
        "verified_on": TODAY,
        "verified_by": "assistant",
        "verification_basis": "記録した辞書・専門資料の本文を読み、設問、解説、答え、読み、分類、一意性を照合。難易度は試遊前の暫定評価。人による公開承認は別。",
        "audit_batch": "018",
    })


def main():
    if sys.argv[1:] == ["--update-metadata"]:
        sources_path = ROOT / "data/sources.jsonl"
        sources = read_jsonl(sources_path)
        reviewed_urls = {source["url"] for source in SOURCES}
        for source in sources:
            if source.get("url") in reviewed_urls:
                source["source_type"] = "web"
        write_jsonl(sources_path, sources)
        audit_path = ROOT / "data/audits/2026-11-03.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        reviews = read_jsonl(ROOT / "data/reviews.jsonl")
        counts = collections.Counter(row["status"] for row in reviews)
        status_counts = {status: counts[status] for status in ("verified", "candidate", "approved", "held", "retired")}
        audit["statuses"] = status_counts
        audit["batch_018"]["statuses"] = status_counts
        audit["batch_018"]["source_lineage_recheck"] = {
            "aio": {"rows": 1036, "source_hash_matches": 1036, "prompt_and_answer_match": 1033},
            "jqac": {"rows": 125, "prompt_match": 125, "answer_match": 125, "reference_match": 125},
            "jsquad": {"rows": 2331, "article_title_match": 2331, "answer_match": 2331, "answer_span_match": 2331, "prompt_exact_match": 2328},
            "note": "Source lineage and answer spans match the pinned/cached datasets; this does not verify the underlying facts, standalone quiz quality, or pronunciation. Pykakasi output matched all 3,492 imported readings before manual review, but spot checks found incorrect readings.",
        }
        note = " Batch 018 directly checked Q003521, Q003545 and Q003551 against the cited textbook, museum and dictionary text; Q004237 is held as a duplicate of Q003551. The source-lineage checks for batch 016 verify transcription and answer spans only, not question quality or facts."
        if note not in audit["verification_scope"]:
            audit["verification_scope"] += note
        audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("updated source metadata and audit scope")
        return

    questions_path = ROOT / "data/questions.jsonl"
    reviews_path = ROOT / "data/reviews.jsonl"
    sources_path = ROOT / "data/sources.jsonl"
    questions = read_jsonl(questions_path)
    reviews = read_jsonl(reviews_path)
    question_by_id = {row["ID"]: row for row in questions}
    review_by_id = {row["ID"]: row for row in reviews}
    targets = ("Q003521", "Q003545", "Q003551", "Q004237")
    if any(review_by_id[qid].get("audit_batch") == "018" for qid in targets):
        raise SystemExit("batch 018 has already been applied")

    openstax, kotobank_leaf, meihaku, imidas, kotobank_kirisute = [s["url"] for s in SOURCES]
    updates = {
        "Q003521": {
            "fields": ["サブジャンル", "問", "解説", "答えjson", "タグ"],
            "reason": "OpenStaxの光合成章と辞書の定義・読みを照合し、誤読「ようりょくからだ」を「ようりょくたい」に修正。分類を生物に具体化。",
            "question": {
                "ジャンル": "理系", "サブジャンル": "生物", "難易度": 3,
                "問": "ラメラ、ストロマ、チラコイドなどの内部構造を持ち、植物細胞で光合成を行う細胞小器官は何でしょう？",
                "解説": "葉緑体は植物細胞内で光合成を行う細胞小器官です。内部にはストロマやチラコイドがあります。",
                "答えjson": ["葉緑体", "ようりょくたい"], "タグ": ["用語", "細胞生物学"],
            },
            "claims": [
                claim("植物の光合成は葉緑体で行われ、葉緑体にはチラコイドとストロマがある。", openstax, "Biology 2e 8.1, paragraphs 51-56", ["問", "解説", "答えjson"]),
                claim("「葉緑体」の読みは「ようりょくたい」。", kotobank_leaf, "デジタル大辞泉・精選版 日本国語大辞典「葉緑体」", ["答えjson"]),
            ],
            "uniqueness": "植物細胞内で光合成を行い、ストロマとチラコイドを持つ細胞小器官は葉緑体に限定される。回答範囲は名称全体。",
            "method": "専門教材と国語辞典を読み、回答対象種別と細胞生物学のタグを付与。",
        },
        "Q003545": {
            "fields": ["ジャンル", "サブジャンル", "難易度", "問", "解説", "答えjson", "タグ"],
            "reason": "刀剣専門資料と辞書で定義・読みを照合。誤読を修正し、目的を断定しない設問と日本文化の分類へ改めた。",
            "question": {
                "ジャンル": "文系", "サブジャンル": "日本文化", "難易度": 2,
                "問": "日本刀の刃ではなく、その反対側の峰（棟）で相手を打つことを何というでしょう？",
                "解説": "峰打ちは、刃の反対側にある峰（棟）で相手を打つことです。打ちどころによっては重傷につながるため、必ず安全とは限りません。",
                "答えjson": ["峰打ち", "みねうち"], "タグ": ["用語", "刀剣知識"],
            },
            "claims": [
                claim("峰打ちは、日本刀の刃の反対側にある棟（峰）で相手を打つこと。", meihaku, "「峰打ちの定義」「峰打ちはどうやるのか」", ["問", "解説", "答えjson"]),
                claim("「峰打ち」の読みは「みねうち」。", imidas, "広辞典 見出し「峰打ち」", ["答えjson"]),
            ],
            "uniqueness": "刃の反対側にある峰（棟）で打つ行為を問うため「峰打ち」に限定される。回答範囲は語全体で、略称は含めない。",
            "method": "刀剣博物館の解説と辞書を読み、回答対象種別と刀剣知識のタグを付与。",
        },
        "Q003551": {
            "fields": ["ジャンル", "サブジャンル", "問", "解説", "答えjson", "タグ"],
            "reason": "辞書・百科事典本文に基づき、条件と事後調査のある制度として設問を限定。自動読みの誤りと分類を修正。",
            "question": {
                "ジャンル": "文系", "サブジャンル": "日本史", "難易度": 3,
                "問": "江戸時代、武士に無礼を働いた庶民を、やむを得ず斬り殺しても処罰されないことがあった特権を何というでしょう？",
                "解説": "切捨御免は無礼討を認めた武士の特権ですが、無制限ではありません。正当な理由や証拠を説明できない場合などは処罰されました。",
                "答えjson": ["切捨御免", "きりすてごめん"], "タグ": ["制度", "江戸時代史"],
            },
            "claims": [
                claim("切捨御免は江戸時代の武士の特権の一つで、町人・農民などが無礼を働いた場合にやむを得ず斬り殺しても処罰されないことがあったが、みだりな殺害や証拠を説明できない場合は処罰された。", kotobank_kirisute, "精選版 日本国語大辞典・改訂新版 世界大百科事典「切捨御免」", ["問", "解説", "答えjson"]),
                claim("「切捨御免」の読みは「きりすてごめん」。", kotobank_kirisute, "見出し、精選版 日本国語大辞典・改訂新版 世界大百科事典", ["答えjson"]),
            ],
            "uniqueness": "江戸時代に無礼討を認めた武士の特権を指す語として「切捨御免」に限定。資料にある別表記「斬捨御免」もひらがな読みは同じため、入力は「きりすてごめん」で一致する。",
            "method": "複数の辞書・百科事典項目を読み、回答対象種別と江戸時代史のタグを付与。",
        },
    }

    for qid, update in updates.items():
        question = question_by_id[qid]
        old = question.copy()
        question.update(update["question"])
        review = review_by_id[qid]
        record_change(review, update["fields"], update["reason"])
        review["pending"] = ["人による最終審査", "試遊で難易度を調整"]
        verify(review, [source["url"] for source in SOURCES if source["url"] in update["claims"][0]["source"] or source["url"] in {c["source"] for c in update["claims"]}], update["claims"], update["uniqueness"], question["タグ"], update["method"])

    duplicate = "Q004237"
    question_by_id[duplicate]["答えjson"] = ["切捨御免", "きりすてごめん"]
    duplicate_review = review_by_id[duplicate]
    record_change(duplicate_review, ["答えjson", "status"], "Q003551と同じ切捨御免を問う重複問題のため保留。辞書で確認した正しい読みも反映。")
    duplicate_review.update({
        "status": "held",
        "pending": ["Q003551と内容が重複。独自の問いに再設計するか統合する必要がある"],
        "reading_status": "reviewed",
        "reading_review": {"source": kotobank_kirisute, "locator": "見出し「切捨御免（きりすてごめん）」", "checked_on": TODAY},
        "duplicate_of": "Q003551",
        "audit_batch": "018",
    })

    source_rows = read_jsonl(sources_path)
    known_urls = {row.get("url") for row in source_rows}
    source_rows.extend(source for source in SOURCES if source["url"] not in known_urls)
    write_jsonl(sources_path, source_rows)
    write_jsonl(questions_path, questions)
    write_jsonl(reviews_path, reviews)

    counts = collections.Counter(row["status"] for row in reviews)
    status_counts = {status: counts[status] for status in ("verified", "candidate", "approved", "held", "retired")}
    tag_counts = collections.Counter(row["tag_status"] for row in reviews)
    audit_path = ROOT / "data/audits/2026-11-03.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["statuses"] = status_counts
    audit["tagging"]["reviewed"] = tag_counts["reviewed"]
    audit["tagging"]["pending"] = tag_counts["pending"]
    audit["batch_018"] = {
        "reviewed": ["Q003521", "Q003545", "Q003551"],
        "held_duplicates": [{"ID": "Q004237", "duplicate_of": "Q003551"}],
        "statuses": status_counts,
        "tagged": 3,
        "source_lineage_recheck": {
            "aio": {"rows": 1036, "source_hash_matches": 1036, "prompt_and_answer_match": 1033},
            "jqac": {"rows": 125, "prompt_match": 125, "answer_match": 125, "reference_match": 125},
            "jsquad": {"rows": 2331, "article_title_match": 2331, "answer_match": 2331, "answer_span_match": 2331, "prompt_exact_match": 2328},
            "note": "Source lineage and answer spans match the pinned/cached datasets; this does not verify the underlying facts, standalone quiz quality, or pronunciation. Pykakasi output matched all 3,492 imported readings before manual review, but spot checks found incorrect readings.",
        },
        "reading_corrections": {
            "Q003521": ["ようりょくからだ", "ようりょくたい"],
            "Q003545": ["みねうちち", "みねうち"],
            "Q003551": ["せつしゃごめん", "きりすてごめん"],
            "Q004237": ["せつしゃごめん", "きりすてごめん"],
        },
        "record": "docs/batch-018.md",
    }
    audit["verification_scope"] += " Batch 018 directly checked Q003521, Q003545 and Q003551 against the cited textbook, museum and dictionary text; Q004237 is held as a duplicate of Q003551. The source-lineage checks for batch 016 verify transcription and answer spans only, not question quality or facts."
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    quiz.export_csv(questions, reviews, "all", ROOT / "data/quiz_all.csv")
    quiz.export_csv(questions, reviews, "candidate", ROOT / "data/quiz_candidates.csv")
    quiz.export_csv(questions, reviews, "verified", ROOT / "data/quiz_verified.csv")
    print("updated", ", ".join(updates), "held", duplicate, "statuses", status_counts, "tags", dict(tag_counts))


if __name__ == "__main__":
    main()
