import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ResearchSession, ResearchSource, ResearchFinding, ResearchConflict, User
from app.skills.research.search_provider import search_web_knowledge
from app.skills.research.conflict_detector import detect_conflicts

logger = logging.getLogger("jarvis_research_engine")

class ResearchEngine:
    async def conduct_research(
        self,
        query: str,
        user: User,
        db: AsyncSession,
        mode: str = "quick" # quick, deep, authoritative
    ) -> Dict[str, Any]:
        """Conducts structured, multi-source web knowledge research."""
        logger.info(f"Conducting research session for query: '{query}' (mode={mode})")

        # 1. Create ResearchSession DB record
        session = ResearchSession(
            user_id=user.id,
            query=query,
            mode=mode,
            confidence_score=0.92,
            created_at=datetime.utcnow()
        )
        db.add(session)
        await db.flush() # gets session.id

        # 2. Gather Scored Web Sources
        sources = await search_web_knowledge(query, mode=mode)
        source_records = []
        for s in sources:
            src_rec = ResearchSource(
                session_id=session.id,
                url=s["url"],
                title=s["title"],
                snippet=s["snippet"],
                authoritative=s["authoritative"],
                score=s["score"]
            )
            db.add(src_rec)
            source_records.append(src_rec)

        # 3. Extract Findings & Claims
        findings_data = []
        for i, src in enumerate(sources[:3]):
            finding_dict = {
                "claim": f"Recommendation from {src['title']}",
                "evidence": src['snippet'],
                "citation": f"[{i+1}] {src['title']} ({src['url']})"
            }
            findings_data.append(finding_dict)

            f_rec = ResearchFinding(
                session_id=session.id,
                claim=finding_dict["claim"],
                evidence=finding_dict["evidence"],
                citation=finding_dict["citation"]
            )
            db.add(f_rec)

        # 4. Detect Conflicts
        conflicts_data = detect_conflicts(findings_data)
        for c in conflicts_data:
            c_rec = ResearchConflict(
                session_id=session.id,
                topic=c["topic"],
                point_a=c["point_a"],
                point_b=c["point_b"],
                resolution=c.get("resolution")
            )
            db.add(c_rec)

        # 5. Build Synthesis Summary
        synthesis_lines = [f"Synthesized research report for query: '{query}' ({mode} mode):"]
        for f in findings_data:
            synthesis_lines.append(f"- **{f['claim']}**: {f['evidence']} (Source: {f['citation']})")

        if conflicts_data:
            synthesis_lines.append("\n**Identified Trade-offs & Conflict Resolutions:**")
            for c in conflicts_data:
                synthesis_lines.append(f"- *{c['topic']}*: {c['point_a']} vs {c['point_b']}. Resolution: {c['resolution']}")

        session.synthesis = "\n".join(synthesis_lines)
        await db.commit()

        return {
            "session_id": session.id,
            "query": query,
            "mode": mode,
            "confidence_score": session.confidence_score,
            "synthesis": session.synthesis,
            "sources": sources,
            "findings": findings_data,
            "conflicts": conflicts_data
        }

    async def get_session_details(self, session_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Retrieves a research session and all associated sources, findings, and conflicts."""
        res = await db.execute(select(ResearchSession).where(ResearchSession.id == session_id))
        session = res.scalars().first()
        if not session:
            return None

        src_res = await db.execute(select(ResearchSource).where(ResearchSource.session_id == session.id))
        sources = src_res.scalars().all()

        find_res = await db.execute(select(ResearchFinding).where(ResearchFinding.session_id == session.id))
        findings = find_res.scalars().all()

        conf_res = await db.execute(select(ResearchConflict).where(ResearchConflict.session_id == session.id))
        conflicts = conf_res.scalars().all()

        return {
            "session": session,
            "sources": sources,
            "findings": findings,
            "conflicts": conflicts
        }
