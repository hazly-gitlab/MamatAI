from typing import List, Dict, Any

def detect_conflicts(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyzes research claims to identify conflicting views or trade-offs."""
    conflicts = []

    claims_text = " ".join([f"{f.get('claim', '')} {f.get('evidence', '')}".lower() for f in findings])

    if "ssl" in claims_text and "performance" in claims_text:
        conflicts.append({
            "topic": "SSL Encryption vs Network Overhead",
            "point_a": "Enforcing full SSL mode enhances transport security against MITM attacks.",
            "point_b": "TLS handshake and packet encryption can introduce a slight 2-5% latency overhead on small queries.",
            "resolution": "Use connection pooling with persistent TLS connections to negate handshake overhead."
        })

    if "connection pool" in claims_text and "max connections" in claims_text:
        conflicts.append({
            "topic": "Connection Pool Sizing vs Resource Limits",
            "point_a": "Larger connection pool sizes reduce connection waiting time during high concurrency bursts.",
            "point_b": "Excessive database connection pools consume higher RAM and can exhaust OS socket limits.",
            "resolution": "Set pool size to match physical core capacity and rely on PgBouncer / Redis queuing for excess traffic."
        })

    return conflicts
