from urllib.parse import urlparse
from typing import Dict, Any

AUTHORITATIVE_DOMAINS = [
    "postgresql.org", "docs.python.org", "fastapi.tiangolo.com",
    "github.com", "redis.io", "docker.com", "kubernetes.io",
    "developer.mozilla.org", "wikipedia.org", "gov", "edu", "org"
]

def score_source(url: str, title: str, snippet: str) -> Dict[str, Any]:
    """Calculates trust and authority score for a research web source."""
    domain = ""
    try:
        domain = urlparse(url).hostname or ""
    except Exception:
        pass

    authoritative = False
    score = 0.70

    # Check domain authority
    for auth_dom in AUTHORITATIVE_DOMAINS:
        if domain == auth_dom or domain.endswith(f".{auth_dom}"):
            authoritative = True
            score += 0.20
            break

    # Check title/snippet keywords relevance
    keywords = ["official", "documentation", "security", "recommendation", "best practice", "guide"]
    for kw in keywords:
        if kw in title.lower() or kw in snippet.lower():
            score += 0.03

    final_score = min(round(score, 2), 0.99)

    return {
        "domain": domain,
        "authoritative": authoritative,
        "score": final_score
    }
