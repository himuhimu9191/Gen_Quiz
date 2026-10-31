import csv
import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quiz', ROOT / 'scripts/quiz.py')
quiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quiz)


class QuizTest(unittest.TestCase):
    def test_notation_and_explicit_variants(self):
        answers = ['ベートーヴェン', 'べーとーゔぇん', 'ベートーベン']
        for response in ['ベートー・ヴェン', 'べーとーべん', ' ﾍﾞｰﾄｰｳﾞｪﾝ ']:
            self.assertTrue(quiz.accepts(answers, response))
        for response in ['', 'べん', 'ルートヴィヒ', 'ベートーヴェンです']:
            self.assertFalse(quiz.accepts(answers, response))

    def test_proper_names_require_full_names(self):
        by_id = {q['ID']: q for q in quiz.load(ROOT / 'data/questions.jsonl')}
        cases = [('Q000006', 'マインクラフト', 'マイクラ'),
                 ('Q000014', 'あつまれどうぶつの森', 'あつ森'),
                 ('Q000017', 'ドラゴンクエスト', 'ドラクエ'),
                 ('Q000274', 'ショーシャンクの空に', 'ショーシャンク')]
        for qid, full, shortened in cases:
            self.assertTrue(quiz.accepts(by_id[qid]['答えjson'], full), qid)
            self.assertFalse(quiz.accepts(by_id[qid]['答えjson'], shortened), qid)
        for r in quiz.load(ROOT / 'data/reviews.jsonl'):
            for alias in r.get('rejected_aliases', []):
                self.assertFalse(quiz.accepts(by_id[r['ID']]['答えjson'], alias), r['ID'])

    def test_trial_balance_and_integrity(self):
        questions = quiz.load(ROOT / 'data/questions.jsonl')
        reviews = quiz.load(ROOT / 'data/reviews.jsonl')
        errors, _ = quiz.validate(questions, reviews)
        self.assertEqual(errors, [])
        trial = [q for q in questions if 1 <= int(q['ID'][1:]) <= 350]
        self.assertEqual(len(trial), 350)
        for genre in quiz.GENRES:
            for level in range(1, 6):
                self.assertEqual(sum(q['ジャンル'] == genre and q['難易度'] == level for q in trial), 10)

    def test_no_answer_given_in_question(self):
        for q in quiz.load(ROOT / 'data/questions.jsonl'):
            for answer in q['答えjson']:
                # A short term may legitimately be part of another word.
                if len(quiz.normalize(answer)) >= 3:
                    question = q['問']
                    # Treat katakana words as units: ラクトース is not given
                    # merely because the separate word ガラクトース occurs.
                    for token in re.findall(r'[ァ-ヺー]+', question):
                        if quiz.normalize(answer) != quiz.normalize(token) and quiz.normalize(answer) in quiz.normalize(token):
                            question = question.replace(token, '')
                    self.assertNotIn(quiz.normalize(answer), quiz.normalize(question), q['ID'])
            self.assertFalse(any('・' in a or '･' in a for a in q['答えjson']), q['ID'])

    def test_committed_csv_matches_master(self):
        questions = quiz.load(ROOT / 'data/questions.jsonl')
        candidate_ids = {r['ID'] for r in quiz.load(ROOT / 'data/reviews.jsonl') if r['status'] == 'candidate'}
        with (ROOT / 'data/quiz_candidates.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            row['難易度'] = int(row['難易度'])
            row['答えjson'] = json.loads(row['答えjson'])
        self.assertEqual(rows, [q for q in questions if q['ID'] in candidate_ids])

    def test_approval_requires_evidence(self):
        questions = quiz.load(ROOT / 'data/questions.jsonl')[:1]
        reviews = copy.deepcopy(quiz.load(ROOT / 'data/reviews.jsonl')[:1])
        reviews[0]['status'] = 'approved'
        errors, _ = quiz.validate(questions, reviews)
        self.assertTrue(any('根拠なし' in e for e in errors))
        self.assertTrue(any('人の承認記録なし' in e for e in errors))

    def test_csv_roundtrip_and_release_filter(self):
        questions = quiz.load(ROOT / 'data/questions.jsonl')
        reviews = quiz.load(ROOT / 'data/reviews.jsonl')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'quiz.csv'
            self.assertEqual(quiz.export_csv(questions, reviews, 'approved', target), 0)
            candidate_ids = {r['ID'] for r in reviews if r['status'] == 'candidate'}
            candidates = [q for q in questions if q['ID'] in candidate_ids]
            self.assertEqual(quiz.export_csv(questions, reviews, 'candidate', target), len(candidates))
            with target.open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(list(rows[0]), list(quiz.FIELDS))
            self.assertEqual(json.loads(rows[0]['答えjson']), candidates[0]['答えjson'])
            self.assertEqual(rows[0]['問'], candidates[0]['問'])
            self.assertEqual(quiz.export_csv(questions, reviews, 'all', target), len(questions))

    def test_verified_claims_have_traceable_sources(self):
        sources = quiz.load(ROOT / 'data/sources.jsonl')
        by_url = {s['url']: s for s in sources}
        self.assertEqual(len(by_url), len(sources))
        verified = [r for r in quiz.load(ROOT / 'data/reviews.jsonl') if r['status'] == 'verified']
        self.assertGreater(len(verified), 0)
        for review in verified:
            self.assertIsNone(review['reviewer'])
            self.assertIsNone(review['reviewed_on'])
            for claim in review['claims']:
                self.assertIn(claim['source'], by_url, review['ID'])
                source = by_url[claim['source']]
                self.assertRegex(source['sha256'], r'^[a-f0-9]{64}$')
                self.assertRegex(source['repository_commit'], r'^[a-f0-9]{40}$')
                self.assertIn(source['repository_commit'], source['url'])

    def test_all_and_verified_csv_match_master(self):
        questions = quiz.load(ROOT / 'data/questions.jsonl')
        reviews = quiz.load(ROOT / 'data/reviews.jsonl')
        by_id = {r['ID']: r for r in reviews}
        for status in ('all', 'verified'):
            with (ROOT / f'data/quiz_{status}.csv').open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.DictReader(stream))
            for row in rows:
                row['難易度'] = int(row['難易度'])
                row['答えjson'] = json.loads(row['答えjson'])
            expected = [q for q in questions if status == 'all' or by_id[q['ID']]['status'] == status]
            self.assertEqual(rows, expected)


if __name__ == '__main__':
    unittest.main()
