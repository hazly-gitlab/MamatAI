from typing import List, Dict, Any
from app.tools.registry import handle_web_search
from app.skills.research.source_scorer import score_source

async def search_web_knowledge(query: str, mode: str = "quick") -> List[Dict[str, Any]]:
    """Performs web knowledge research according to research mode (quick, deep, authoritative)."""
    # Execute web search
    search_res = handle_web_search(query)
    raw_results = search_res.get("results", [])

    # Add authoritative PostgreSQL/Python/Security documentation links based on query topics
    query_lower = query.lower()
    if "postgresql" in query_lower or "sql" in query_lower:
        raw_results.append({
            "title": "PostgreSQL Official Documentation: Security & Authentication",
            "snippet": "Enforce pg_hba.conf hostssl restrictions, use scram-sha-256 password encryption, and apply least-privilege role assignments.",
            "url": "https://www.postgresql.org/docs/current/security.html"
        })
    if "redis" in query_lower:
        raw_results.append({
            "title": "Redis Security & Memory Management Guide",
            "snippet": "Require secure auth tokens, bind to local loopback or private VPCs, and enable maxmemory-policy allkeys-lru.",
            "url": "https://redis.io/docs/management/security/"
        })
    if "fastapi" in query_lower or "backend" in query_lower:
        raw_results.append({
            "title": "FastAPI Security & CORS Best Practices",
            "snippet": "Configure CORSMiddleware with specific origins, mandate OAuth2 JWT tokens, and set strict request size limits.",
            "url": "https://fastapi.tiangolo.com/tutorial/security/"
        })

    scored_sources = []
    for item in raw_results:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")

        scoring = score_source(url, title, snippet)

        # Filter for authoritative mode if requested
        if mode == "authoritative" and not scoring["authoritative"]:
            continue

        scored_sources.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "domain": scoring["domain"],
            "authoritative": scoring["authoritative"],
            "score": scoring["score"]
        })

    # Sort sources by authority score
    scored_sources.sort(key=lambda s: s["score"], reverse=True)
    return scored_sources
