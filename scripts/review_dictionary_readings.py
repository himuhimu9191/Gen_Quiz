"""Apply individually selected canonical-reading corrections from dictionary headings.

Only terms in the explicit decision list are changed. Homonyms, valid alternate
readings, incomplete headword readings, and unresolved entries are excluded.
Review state, genre, difficulty and tags are preserved.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz

TODAY = "2026-11-03"
ACCEPTED_TERMS = set("""
鳩時計 鏡開き 平敦盛 高瀬舟 三種の神器 今井正 三すくみ 冬虫夏草 日時計 痛車
千利休 軍艦巻 桜島 種子島 辰吉丈一郎 源義経 小野小町 弁才天 君の名は 阿寒湖
辻村深月 塵芥集 天目山 恵方巻 かき氷 洞庭湖 万城目学 林子平 角田光代 五重塔
八丈島 前田山英五郎 中馬庚 凝灰岩 熊谷一弥 在原業平 冷や汁 塵劫記 役所広司 小野道風
国際通り 火垂るの墓 菅原道真 富嶽三十六景 内村光良 衣替え 壬生寺 当麻蹴速 寿福寺 十三湖
宇治十帖 藤原公任 三井高利 新村出 婚姻色 三白眼 乾燥帯 岸部一徳 十津川村 乗鞍岳
七里ヶ浜 お市の方 万国旗 替え玉 食物繊維 藤原道長 離島 枯山水 水無月 海の日 鹿児島県
綱引き 近代五種競技 佐田岬半島 霊巌洞 無量大数 北斗七星 宮古島 徳川家継 平重盛 大向う
伊集院静 あだち充 心中天網島 非核三原則 秋芳洞 慈照寺 羽生結弦 けん玉 堀内健 冠番組
面取り 目安箱 無洗米 千社札 休肝日 安宅の関 徳川家治 伊藤博文 日本国有鉄道 徳川家達
平城京 どんでん返し 千と千尋の神隠し 大赤斑 前説 走高跳 将棋倒し 五人組 人差し指 空手道
徳川家慶 全粒粉 ふみの日 尚巴志王 園子温 大窪寺 杜子春 寄木細工 大洋島 右翼手
国司 座敷童子 青銅器時代 費用対効果 法相宗 中小企業等協同組合 万暦版大蔵経 大正新脩大蔵経
大蔵経 硝酸塩 公田官物率法 越後国 磐舟柵 募集型企画旅行 あだ名 菅義偉 預言者 東京大学史料編纂所
土井たか子 宮沢俊義 伏見城 共観福音書 武器輸出三原則 探検家 鹿児島市 土砂崩れ 盧溝橋事件 公共職業安定所
""".split())


def main():
    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    sources = quiz.load(ROOT / "data/sources.jsonl")
    source_by_url = {r["url"]: r for r in sources}
    review_by_id = {r["ID"]: r for r in reviews}
    findings = quiz.load(ROOT / "data/audits/reading-differences-2026-11-03.jsonl")
    finding_by_id = {row["ID"]: row for row in findings}
    changes = []
    for question in questions:
        if question["答えjson"][0] not in ACCEPTED_TERMS:
            continue
        finding = finding_by_id.get(question["ID"])
        if not finding or not finding.get("exact_headword"):
            continue
        after = quiz.normalize(finding["dictionary_reading"])
        before = question["答えjson"][1]
        if before == after:
            continue
        if not re.fullmatch(r"[ぁ-ゖー]+", after):
            raise ValueError("Dictionary reading is not a complete kana reading: " + question["ID"])
        if before != finding["stored"]:
            raise ValueError("The audited quiz reading has changed: " + question["ID"])
        review = review_by_id[question["ID"]]
        previous_version = review["version"]
        previous_status = review["status"]
        question["答えjson"][1] = after
        # A formerly explicit alias may now duplicate the corrected reading.
        answer_keys = {quiz.normalize(a) for a in question["答えjson"][:2]}
        aliases = []
        for alias in question["答えjson"][2:]:
            key = quiz.normalize(alias)
            if key not in answer_keys:
                aliases.append(alias)
                answer_keys.add(key)
        question["答えjson"][2:] = aliases
        review["version"] += 1
        evidence = {"source": finding["url"], "locator": "見出し「" + finding["heading"] + "」", "checked_on": TODAY, "source_sha256": finding["sha256"]}
        review["canonical_reading_review"] = {"batch": "020", "before": before, "after": after, **evidence, "scope": "代表表記と同じ見出しの読みを照合。設問全体の事実・許容表記の審査とは別。"}
        review.setdefault("change_history", []).append({
            "version": review["version"], "date": TODAY, "fields": ["答えjson"],
            "reason": f"辞書の同一見出しの読みと照合し、代表解答のひらがな読みを「{before}」から「{after}」へ校正。問題全体の照合状態は保持。",
        })
        if previous_status in {"verified", "approved"}:
            review.setdefault("claims", []).append({"claim": "代表解答の読みは「" + after + "」。", **{k: evidence[k] for k in ("source", "locator", "checked_on")}, "coverage": ["答えjson"]})
        if finding["url"] not in source_by_url:
            source = {
                "url": finding["url"], "publisher": "コトバンク（収録辞典の出典表示を参照）", "source_type": "web",
                "section": finding["heading"], "sha256": finding["sha256"], "checked_on": TODAY,
                "method": "代表解答と完全一致する辞書見出しと読みを確認。本文の他の事実を照合したという意味ではない。",
                "read_sections": ["見出しと（読み）欄"],
            }
            sources.append(source)
            source_by_url[finding["url"]] = source
        changes.append({"ID": question["ID"], "answer": question["答えjson"][0], "before": before, "after": after, "previous_version": previous_version, "version": review["version"], "status_preserved": previous_status, "evidence": evidence})

    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise ValueError("\n".join(errors))
    if not changes:
        print("No selected canonical-reading corrections remain")
        return
    for name, rows in (("questions", questions), ("reviews", reviews), ("sources", sources)):
        (ROOT / f"data/{name}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (ROOT / "data/audits/batch-020-reading-review.json").write_text(json.dumps({
        "checked_on": TODAY, "changed": len(changes), "scope": "Manually selected complete dictionary headwords; canonical reading only. Quiz review states, tags, difficulty and genres were preserved.", "changes": changes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for state, filename in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, state, ROOT / f"data/quiz_{filename}.csv")
    print("reading_corrections", len(changes), "states_preserved", dict(collections.Counter(r["status"] for r in reviews)))


if __name__ == "__main__":
    main()
