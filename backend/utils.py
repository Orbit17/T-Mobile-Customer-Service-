import re
from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from textblob import TextBlob
except Exception:  # pragma: no cover
    TextBlob = None


URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"[@#]\w+")
EMOJI_RE = re.compile(
    "["  # basic emoji ranges
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

POSITIVE_WORDS = {
    "great",
    "awesome",
    "love",
    "fast",
    "amazing",
    "super",
    "excellent",
    "happy",
    "kudos",
    "thank",
}
NEGATIVE_WORDS = {
    "outage",
    "down",
    "slow",
    "terrible",
    "bad",
    "angry",
    "hate",
    "billing",
    "charge",
    "dropped",
    "no service",
    "latency",
}

TOPIC_RULES = {
    "outage": {"outage", "down", "no service", "tower", "coverage"},
    "speed": {"slow", "speed", "latency", "ping", "buffer"},
    "billing": {"billing", "charge", "payment", "credit"},
    "support": {"support", "agent", "ticket", "help"},
}

TOPIC_SEVERITY = {
    "outage": 1.0,
    "speed": 0.8,
    "billing": 0.6,
    "support": 0.4,
    "other": 0.3,
}


def clean_text(text: str) -> str:
    text = URL_RE.sub("", text)
    text = MENTION_RE.sub("", text)
    text = EMOJI_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_sentiment(text: str) -> float:
    if not text:
        return 0.0
    if TextBlob is not None:
        try:
            return float(TextBlob(text).sentiment.polarity)
        except Exception:
            pass
    # Fallback: simple lexicon
    lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in lower)
    if pos == 0 and neg == 0:
        return 0.0
    return float((pos - neg) / max(1, pos + neg))


def extract_keywords_texts(texts: List[str], top_k: int = 5) -> List[List[str]]:
    # Fit a TF-IDF vectorizer for the batch, then pick top terms per doc
    if not texts:
        return []
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        stop_words="english",
        lowercase=True,
        min_df=1,
    )
    tfidf = vectorizer.fit_transform(texts)
    feature_names = np.array(vectorizer.get_feature_names_out())
    results: List[List[str]] = []
    for row in tfidf:
        if row.nnz == 0:
            results.append([])
            continue
        row = row.tocoo()
        if row.nnz <= top_k:
            idxs = row.col
        else:
            # pick top_k indices by score
            idxs = row.col[np.argsort(row.data)[-top_k:]]
        keywords = [feature_names[i] for i in idxs]
        results.append(keywords)
    return results


def classify_topic_from_keywords(keywords: List[str]) -> str:
    if not keywords:
        return "other"
    lower_set = set([k.lower() for k in keywords])
    best_topic = "other"
    best_count = 0
    for topic, words in TOPIC_RULES.items():
        overlap = len(lower_set.intersection(words))
        if overlap > best_count:
            best_count = overlap
            best_topic = topic
    return best_topic


def topic_severity(topic: str) -> float:
    return float(TOPIC_SEVERITY.get(topic, TOPIC_SEVERITY["other"]))


