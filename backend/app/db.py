import sys
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.config import settings
import google.generativeai as genai
from sqlalchemy import String, Text, select, text
from pgvector.sqlalchemy import Vector


# 1. Database Engine & Session Maker Setup
# (This is a skeleton for Teammate A to configure further)
try:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
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
# TODO: Create SQLite-compatible SQLAlchemy models inheriting from Base for:
# - SessionState (storing sessionId, archetype, current document draft)
# - AuditLogs (storing historic Critic scorecard revisions)
# (Note: Use SQLite types. PostgreSQL migrations will be handled 
#  externally by the Team Lead.)
# =====================================================================


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
            model="models/text-embedding-004",
            content=text
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
    """

    if AsyncSessionLocal is None:
        raise RuntimeError("Database session is not initialized.")

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not archetype or not archetype.strip():
        raise ValueError("Archetype cannot be empty.")

    archetype = archetype.strip().lower()
    query = query.strip()

    embedding = await generate_embedding(query)

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
                LIMIT 5
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
        return "No style guide context found."

    return "\n\n".join([row[0] for row in rows])