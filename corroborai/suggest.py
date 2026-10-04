"""Local unsupervised text retrieval. Scores are not correctness probabilities."""
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_INFO = {"method": "character TF-IDF + cosine", "fit": "unsupervised, local reference labels only",
              "ngrams": [3, 5], "threshold": 0.30, "margin": 0.03,
              "baseline": "difflib.SequenceMatcher, same candidates and abstention policy",
              "authority": "Investigation suggestions only; never changes a verdict."}


class LabelIndex:
    def __init__(self, labels):
        self.labels = sorted({s for s in labels if s and len(s.strip()) >= 3})
        self.vectorizer = None
        if self.labels:
            self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), strip_accents="unicode")
            self.matrix = self.vectorizer.fit_transform(self.labels)

    def query(self, value, baseline=False):
        if not self.vectorizer or not value:
            return {"status": "abstain", "reason": "No usable label or reference vocabulary.", "candidates": []}
        scores = ([SequenceMatcher(None, value.casefold(), s.casefold(), autojunk=False).ratio() for s in self.labels]
                  if baseline else cosine_similarity(self.vectorizer.transform([value]), self.matrix).ravel().tolist())
        ranked = sorted(zip(self.labels, scores), key=lambda x: (-x[1], x[0]))[:3]
        best = ranked[0][1]
        margin = best - ranked[1][1] if len(ranked) > 1 else best
        allowed = best >= MODEL_INFO["threshold"] and margin >= MODEL_INFO["margin"]
        return {"status": "suggestion" if allowed else "abstain",
                "reason": "Candidate to inspect; not a corrected value or calibrated probability." if allowed else "Weak or ambiguous match; manual review remains necessary.",
                "candidates": [{"label": label, "score": round(float(score), 6)} for label, score in ranked],
                "margin": round(float(margin), 6), "method": "difflib" if baseline else "tfidf_cosine"}
