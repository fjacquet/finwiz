"""News deduplication and source reliability utilities.

Provides Jaccard similarity-based deduplication (DATA-08) and
source reliability weighting for articles (DATA-09).
Temporal decay and sentiment confidence utilities (Phase 14).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

from finwiz.schemas.sentiment import NewsArticle

DEDUP_THRESHOLD: float = 0.6

# Source reliability weights (DATA-09)
# Higher = more trustworthy financial reporting
SOURCE_RELIABILITY: dict[str, float] = {
    "reuters": 0.95,
    "bloomberg": 0.95,
    "wsj": 0.90,
    "wall_street_journal": 0.90,
    "financial_times": 0.90,
    "cnbc": 0.85,
    "marketwatch": 0.80,
    "finnhub": 0.80,
    "yahoo_finance": 0.75,
    "investing_com": 0.70,
    "gnews": 0.65,
    "rss": 0.50,
    "unknown": 0.40,
}


def _tokenize(text: str) -> set[str]:
    """Tokenize text into a lowercase word set."""
    return set(text.lower().split())


def jaccard_similarity(text_a: str, text_b: str) -> float:
    """Calculate Jaccard similarity between two texts.

    Returns a value between 0.0 (no overlap) and 1.0 (identical word sets).
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def deduplicate_articles(
    articles: list[NewsArticle],
    threshold: float = DEDUP_THRESHOLD,
) -> list[NewsArticle]:
    """Remove duplicate articles using Jaccard similarity on title+summary.

    When duplicates are found, keeps the article with higher source reliability.
    """
    unique: list[NewsArticle] = []
    for article in articles:
        combined = f"{article.title} {article.summary}"
        is_dup = False
        for i, existing in enumerate(unique):
            existing_combined = f"{existing.title} {existing.summary}"
            if jaccard_similarity(combined, existing_combined) >= threshold:
                # Keep the one with higher source reliability
                if article.source_reliability > existing.source_reliability:
                    unique[i] = article
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
    return unique


def get_source_reliability(source: str) -> float:
    """Get reliability weight for a news source.

    Normalizes the source name (lowercase, underscores) and looks up in the
    SOURCE_RELIABILITY table. Unknown sources get 0.40.
    """
    normalized = source.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
    return SOURCE_RELIABILITY.get(normalized, SOURCE_RELIABILITY["unknown"])


def calculate_weighted_sentiment(articles: list[NewsArticle]) -> float:
    """Calculate reliability-weighted average sentiment across articles.

    Articles without a sentiment_score are excluded from the calculation.
    Returns 0.0 if no articles have sentiment scores.
    """
    scored = [a for a in articles if a.sentiment_score is not None]
    if not scored:
        return 0.0
    total_weight = sum(a.source_reliability for a in scored)
    if total_weight == 0:
        return 0.0
    weighted_sum: float = sum(
        a.sentiment_score * a.source_reliability  # type: ignore[misc]
        for a in scored
    )
    return weighted_sum / total_weight


def temporal_decay_weight(published_at: datetime, half_life_hours: float = 48.0) -> float:
    """Calculate exponential temporal decay weight for an article.

    Weight halves every half_life_hours. Brand-new articles get weight ~1.0,
    articles half_life_hours old get 0.5, etc.

    Args:
        published_at: Article publication timestamp (must be timezone-aware or naive UTC)
        half_life_hours: Hours for weight to decay to 50% (default 48h)

    Returns:
        Weight in (0.0, 1.0] -- 1.0 for brand-new, decaying toward 0
    """
    now = datetime.now(tz=UTC)
    # Handle naive datetimes by assuming UTC
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600)
    decay_rate = math.log(2) / half_life_hours
    return math.exp(-decay_rate * age_hours)


def calculate_sentiment_confidence(
    article_count: int,
    source_count: int,
    data_freshness_hours: float,
    min_articles_for_high_confidence: int = 10,
    min_sources_for_max_diversity: int = 3,
    max_freshness_hours: float = 168.0,
) -> float:
    """Calculate confidence in sentiment score based on data quality.

    Confidence is a weighted combination of three factors:
    - Article count coverage (40%): More articles = higher confidence
    - Source diversity (30%): More unique sources = higher confidence
    - Data freshness (30%): Staler data = lower confidence

    Args:
        article_count: Number of articles used
        source_count: Number of unique sources
        data_freshness_hours: Hours since newest article
        min_articles_for_high_confidence: Articles needed for 100% count factor
        min_sources_for_max_diversity: Sources needed for 100% diversity factor
        max_freshness_hours: Freshness window beyond which freshness factor = 0

    Returns:
        Confidence in [0.0, 1.0]
    """
    count_factor = min(1.0, article_count / max(1, min_articles_for_high_confidence))
    diversity_factor = min(1.0, source_count / max(1, min_sources_for_max_diversity))
    freshness_factor = max(0.0, 1.0 - (data_freshness_hours / max(0.001, max_freshness_hours)))

    return count_factor * 0.4 + diversity_factor * 0.3 + freshness_factor * 0.3
