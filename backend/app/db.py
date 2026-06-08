import sys
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings
import google.generativeai as genai
from sqlalchemy import String, Text, select, text, Integer, JSON
from pgvector.sqlalchemy import Vector


# 1. Database Engine & Session Maker Setup
# (This is a skeleton for Teammate A to configure further)
try:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=10,
        max_overflow=20
    )
    genai.configure(api_key=settings.GEMINI_API_KEY)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
except Exception as e:
    print(f"Database initialization warning: {e}", file=sys.stderr)
    AsyncSessionLocal = None

class Base(DeclarativeBase):
    pass

class StyleGuideEmbedding(Base):
    __tablename__ = "style_guide_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    archetype: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)

    embedding: Mapped[List[float]] = mapped_column(Vector(768))

# =====================================================================
# TASK ASSIGNMENT: Goli Manohar
# SQLite-compatible SQLAlchemy models inheriting from Base:
# =====================================================================

class SessionState(Base):
    __tablename__ = "session_states"

    session_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    archetype: Mapped[str] = mapped_column(String(50), nullable=False)
    document_content: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="idle")
    loop_count: Mapped[int] = mapped_column(Integer, default=0)
    max_loops: Mapped[int] = mapped_column(Integer, default=3)
    payload_text: Mapped[str] = mapped_column(Text, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    current_step: Mapped[str] = mapped_column(String(100), nullable=True)
    scorecard: Mapped[dict] = mapped_column(JSON, nullable=True)
    trace: Mapped[list] = mapped_column(JSON, nullable=True)

class AuditLogs(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(50), nullable=False)
    loop_count: Mapped[int] = mapped_column(Integer, default=0)
    scorecard: Mapped[dict] = mapped_column(JSON, nullable=False)


# =====================================================================
# TASK ASSIGNMENT: TEAMMATE C (Intermediate/Strong Teammate)
# TODO: Integrate pgvector extensions and build vector lookup pipelines
# =====================================================================

async def generate_embedding(text: str) -> List[float]:
    """
    Generate Gemini embeddings and truncate to 768 dimensions.
    """

    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    try:
        response = genai.embed_content(
            model="models/gemini-embedding-2",
            content=text,
            output_dimensionality=768
        )

    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {str(e)}")

    embedding = response.get("embedding")

    if not embedding:
        raise ValueError("Failed to generate embedding.")

    if len(embedding) < 768:
        raise ValueError("Embedding dimension is smaller than 768.")

    return embedding[:768]

async def index_style_guide(content: str, archetype: str):
    """
    Index style-guide content into pgvector storage.
    """

    if AsyncSessionLocal is None:
        raise RuntimeError("Database session is not initialized.")
    
    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")
    
    if not archetype or not archetype.strip():
        raise ValueError("Archetype cannot be empty.")
    
    archetype = archetype.strip().lower()

    embedding = await generate_embedding(content)

    async with AsyncSessionLocal() as session:

        entry = StyleGuideEmbedding(
            archetype=archetype,
            content=content,
            embedding=embedding
        )

        try:
            session.add(entry)
            await session.commit()

        except Exception as e:

            await session.rollback()

            raise RuntimeError(
                f"Style guide indexing failed: {str(e)}"
            )

async def retrieve_context(query: str, archetype: str) -> str:
    """
    Hybrid semantic + lexical retrieval using pgvector + PostgreSQL full-text search.
    Optimized to restrict context window sizes and reduce latency.
    """

    if AsyncSessionLocal is None:
        raise RuntimeError("Database session is not initialized.")

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not archetype or not archetype.strip():
        raise ValueError("Archetype cannot be empty.")

    archetype = archetype.strip().lower()
    query = query.strip()

    try:
        embedding = await generate_embedding(query)
    except Exception as e:
        print(f"RAG: Failed to generate search embedding: {e}", file=sys.stderr)
        return "No style guide context available (Embedding error)."

    async with AsyncSessionLocal() as session:

        try:

            sql = text("""
                SELECT content
                FROM style_guide_embeddings
                WHERE archetype = :archetype
                ORDER BY
                    (
                        embedding <=> CAST(:embedding AS vector)
                    ) +
                    (
                        1 - ts_rank(
                            to_tsvector('english', content),
                            plainto_tsquery('english', :query)
                        )
                    )
                ASC
                LIMIT 3
            """)

            result = await session.execute(
                sql,
                {
                    "archetype": archetype,
                    "embedding": embedding,
                    "query": query
                }
            )

            rows = result.fetchall()

        except Exception as e:
            raise RuntimeError(
                f"Hybrid retrieval failed: {str(e)}"
            )

    if not rows:
        print(f"RAG audit: query='{query[:40]}...', archetype='{archetype}' -> 0 matches found.", file=sys.stderr)
        return "No style guide context found."

    # Audit logging for validation
    print(f"RAG audit: query='{query[:40]}...', archetype='{archetype}' -> {len(rows)} matches found:", file=sys.stderr)
    retrieved_parts = []
    for idx, row in enumerate(rows):
        content_snippet = row[0][:100].replace('\n', ' ')
        print(f"  Match {idx+1}: {content_snippet}...", file=sys.stderr)
        # Clamps individual context sizes to 1500 chars to avoid API cost & latency blowups
        retrieved_parts.append(row[0][:1500])

    return "\n\n".join(retrieved_parts)

async def seed_style_guides():
    """
    Seeds default style guide documents for each archetype if the table is empty.
    """
    if AsyncSessionLocal is None:
        return

    async with AsyncSessionLocal() as session:
        try:
            # Check if any embeddings exist
            result = await session.execute(select(StyleGuideEmbedding).limit(1))
            if result.scalars().first():
                return  # already seeded

            print("Seeding default style guides into PostgreSQL...", file=sys.stderr)
            
            seeds = [
                {
                    "archetype": "technical",
                    "content": (
                        "DocuFlow Technical Specification Style Guide:\n"
                        "- Structure: Always include an Executive Summary, System Architecture, API Specifications, and Security section.\n"
                        "- API Design: Specify JSON formats, endpoint HTTP verbs, and request/response payloads explicitly.\n"
                        "- Latency: Target execution and endpoint latency must remain under 150ms.\n"
                        "- Rate Limiting: Specify Token Bucket or Leaky Bucket algorithms for endpoint protection.\n"
                        "- Infrastructure: Detail Docker, PostgreSQL, and cache components clearly."
                    )
                },
                {
                    "archetype": "legal",
                    "content": (
                        "DocuFlow Legal Contract and Agreement Rubric:\n"
                        "- Sovereignty: Must enforce strict EU Data Sovereignty protocols and specify localized data hosting.\n"
                        "- Compliance: Explicitly state compliance with GDPR regulations, data processing addendums, and privacy policies.\n"
                        "- Liability: General liability caps must be included and capped at fees paid in the trailing 12 months.\n"
                        "- Confidentiality: NDA agreements must restrict disclosures to defined business purposes and enforce 5-year survival terms.\n"
                        "- Jurisdiction: Explicitly govern agreements under standard EU or Delaware law."
                    )
                },
                {
                    "archetype": "financial",
                    "content": (
                        "DocuFlow Fiscal and Financial Writing Guidelines:\n"
                        "- Accuracy: Financial figures and transaction metrics must be precise, using up to 4 decimal places.\n"
                        "- Statements: Earnings and audit documents must compile standard Balance Sheet, Income Statement, and Cash Flow metrics.\n"
                        "- Disclosure: Always append a forward-looking statement risk warning regarding economic fluctuations.\n"
                        "- Terminology: Use standard GAAP or IFRS terms (e.g. EBITDA, Revenue, Cost of Goods Sold).\n"
                        "- Audits: Include transaction audit trails, compliance ledger logs, and revision loop summaries."
                    )
                },
                {
                    "archetype": "creative",
                    "content": (
                        "DocuFlow Creative and Marketing Copywriting Guidelines:\n"
                        "- Tone: Bold, premium, engaging, and action-oriented brand voice. Avoid dry academic or technical jargon.\n"
                        "- Structure: Apply the AIDA (Attention, Interest, Desire, Action) framework to structure pitches and landing pages.\n"
                        "- Readability: Keep sentences short (under 25 words) and use bullet points or bold text for key benefits.\n"
                        "- Content: Focus on customer pain points, value propositions, and clear CTAs (Call to Actions).\n"
                        "- Aesthetics: Use rich, modern visual analogies and describe premium design tokens like Obsidian Glass and Aurora Glow."
                    )
                }
            ]

            for s in seeds:
                # Generate embedding
                embedding = await generate_embedding(s["content"])
                entry = StyleGuideEmbedding(
                    archetype=s["archetype"],
                    content=s["content"],
                    embedding=embedding
                )
                session.add(entry)
                
            await session.commit()
            print("Successfully seeded all 4 document archetypes.", file=sys.stderr)
        except Exception as e:
            await session.rollback()
            print(f"Failed to seed style guides: {e}", file=sys.stderr)