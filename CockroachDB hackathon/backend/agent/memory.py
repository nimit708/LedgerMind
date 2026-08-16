"""
LedgerMind Agentic Memory — CockroachDB-backed structured + semantic memory.

Uses CockroachDB Distributed Vector Indexing:
- VECTOR(1024) columns with HNSW indexes for fast similarity search
- Stores agent observations, decisions, and outcomes as embeddings
- Enables semantic retrieval: "find past incidents similar to this one"
- No separate vector store needed — everything in one distributed database

The agent uses CockroachDB as its memory system:
- Structured memory: decisions, baselines, outcomes, approvals
- Semantic memory: vector embeddings for similarity-based retrieval (pgvector)
- Episodic memory: past incidents and their resolutions
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from enum import Enum
import uuid
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MemoryType(str, Enum):
    OBSERVATION = "observation"
    DECISION = "decision"
    OUTCOME = "outcome"
    BASELINE = "baseline"
    INCIDENT = "incident"
    PATTERN = "pattern"


class AgentMemoryEntry(BaseModel):
    """A single memory entry stored in CockroachDB."""
    id: str = None
    sme_id: str
    memory_type: MemoryType
    content: dict
    embedding: Optional[list[float]] = None
    created_at: datetime = None
    metadata: Optional[dict] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class DecisionMemory(BaseModel):
    """Records an agent decision and the SME's response."""
    task_type: str
    observation: str
    analysis: str
    recommendation: str
    approval_status: str  # pending, approved, rejected
    sme_feedback: Optional[str] = None
    outcome: Optional[dict] = None
    outcome_score: Optional[float] = None


class BaselineMemory(BaseModel):
    """Learned baseline for comparison."""
    metric_name: str
    normal_range_low: float
    normal_range_high: float
    sample_size: int
    last_updated: datetime
    confidence: float


class AgenticMemoryStore:
    """
    CockroachDB-backed memory store using Distributed Vector Indexing.
    
    Leverages:
    - pgvector VECTOR(1024) columns for embedding storage
    - HNSW indexes (idx_memory_embedding, idx_decisions_embedding) for fast ANN search
    - Cosine distance operator (<=>) for semantic similarity
    - All vector data co-located with operational data — no separate vector DB needed
    """

    def __init__(self, db_session):
        self.db = db_session

    async def store_observation(self, sme_id: str, observation: dict, embedding: Optional[list[float]] = None) -> str:
        """
        Store a new observation with optional vector embedding.
        Uses CockroachDB's distributed vector indexing for later retrieval.
        """
        entry_id = str(uuid.uuid4())
        content_json = json.dumps(observation)

        if embedding:
            # Store with embedding for semantic search via pgvector HNSW index
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await self.db.execute(
                text("""
                    INSERT INTO agent_memory (id, sme_id, memory_type, content, embedding, created_at)
                    VALUES (:id, :sme_id, 'observation', :content::jsonb, :embedding::vector, now())
                """),
                {"id": entry_id, "sme_id": sme_id, "content": content_json, "embedding": embedding_str}
            )
        else:
            await self.db.execute(
                text("""
                    INSERT INTO agent_memory (id, sme_id, memory_type, content, created_at)
                    VALUES (:id, :sme_id, 'observation', :content::jsonb, now())
                """),
                {"id": entry_id, "sme_id": sme_id, "content": content_json}
            )
        await self.db.commit()
        return entry_id

    async def store_decision(self, sme_id: str, decision: DecisionMemory, embedding: Optional[list[float]] = None) -> str:
        """
        Store an agent decision with vector embedding for future similarity matching.
        The embedding enables finding "similar past decisions" via HNSW index.
        """
        decision_id = str(uuid.uuid4())

        if embedding:
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            await self.db.execute(
                text("""
                    INSERT INTO agent_decisions 
                    (id, sme_id, task_type, observation, analysis, recommendation, 
                     confidence, risk_level, approval_status, embedding, created_at)
                    VALUES (:id, :sme_id, :task_type, :observation, :analysis, :recommendation,
                            0.7, 'medium', :status, :embedding::vector, now())
                """),
                {
                    "id": decision_id, "sme_id": sme_id,
                    "task_type": decision.task_type,
                    "observation": decision.observation,
                    "analysis": decision.analysis,
                    "recommendation": decision.recommendation,
                    "status": decision.approval_status,
                    "embedding": embedding_str,
                }
            )
        else:
            await self.db.execute(
                text("""
                    INSERT INTO agent_decisions 
                    (id, sme_id, task_type, observation, analysis, recommendation, 
                     confidence, risk_level, approval_status, created_at)
                    VALUES (:id, :sme_id, :task_type, :observation, :analysis, :recommendation,
                            0.7, 'medium', :status, now())
                """),
                {
                    "id": decision_id, "sme_id": sme_id,
                    "task_type": decision.task_type,
                    "observation": decision.observation,
                    "analysis": decision.analysis,
                    "recommendation": decision.recommendation,
                    "status": decision.approval_status,
                }
            )
        await self.db.commit()
        return decision_id

    async def store_outcome(self, decision_id: str, outcome: dict, score: float):
        """Store the outcome of an approved action — enables the agent to learn."""
        await self.db.execute(
            text("""
                UPDATE agent_decisions 
                SET outcome = :outcome::jsonb, outcome_score = :score, outcome_checked_at = now()
                WHERE id = :id
            """),
            {"id": decision_id, "outcome": json.dumps(outcome), "score": score}
        )
        await self.db.commit()

    async def retrieve_relevant_memories(
        self,
        sme_id: str,
        query_embedding: list[float],
        memory_types: Optional[list[MemoryType]] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve memories semantically similar to the query using CockroachDB's
        Distributed Vector Indexing (pgvector HNSW).
        
        Uses cosine distance (<=>) for similarity ranking.
        The HNSW index (idx_memory_embedding) provides fast approximate nearest neighbor search.
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        if memory_types:
            type_list = ",".join(f"'{t.value}'" for t in memory_types)
            result = await self.db.execute(
                text(f"""
                    SELECT id, memory_type, content, embedding <=> :embedding::vector AS distance, created_at
                    FROM agent_memory
                    WHERE sme_id = :sme_id AND memory_type IN ({type_list})
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """),
                {"sme_id": sme_id, "embedding": embedding_str, "limit": limit}
            )
        else:
            result = await self.db.execute(
                text("""
                    SELECT id, memory_type, content, embedding <=> :embedding::vector AS distance, created_at
                    FROM agent_memory
                    WHERE sme_id = :sme_id AND embedding IS NOT NULL
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """),
                {"sme_id": sme_id, "embedding": embedding_str, "limit": limit}
            )

        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "memory_type": row[1],
                "content": row[2],
                "distance": float(row[3]),
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ]

    async def get_similar_past_decisions(
        self,
        sme_id: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        """
        Find past decisions similar to the current situation.
        Uses the idx_decisions_embedding HNSW index for fast similarity search.
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        result = await self.db.execute(
            text("""
                SELECT id, task_type, observation, analysis, recommendation,
                       approval_status, outcome_score,
                       embedding <=> :embedding::vector AS distance
                FROM agent_decisions
                WHERE sme_id = :sme_id AND embedding IS NOT NULL
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {"sme_id": sme_id, "embedding": embedding_str, "limit": limit}
        )

        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "task_type": row[1],
                "observation": row[2],
                "analysis": row[3],
                "recommendation": row[4],
                "approval_status": row[5],
                "outcome_score": float(row[6]) if row[6] else None,
                "distance": float(row[7]),
            }
            for row in rows
        ]

    async def get_baselines(self, sme_id: str) -> list[dict]:
        """Get learned baselines for this SME."""
        result = await self.db.execute(
            text("""
                SELECT metric_name, normal_range_low, normal_range_high, 
                       mean_value, std_deviation, sample_size, confidence
                FROM agent_baselines WHERE sme_id = :sme_id
            """),
            {"sme_id": sme_id}
        )
        rows = result.fetchall()
        return [
            {
                "metric_name": row[0],
                "normal_range_low": float(row[1]),
                "normal_range_high": float(row[2]),
                "mean_value": float(row[3]),
                "std_deviation": float(row[4]),
                "sample_size": row[5],
                "confidence": float(row[6]),
            }
            for row in rows
        ]

    async def get_similar_past_incidents(
        self, sme_id: str, current_incident: dict, query_embedding: Optional[list[float]] = None, limit: int = 5
    ) -> list[dict]:
        """
        Find past incidents similar to the current one.
        Uses vector similarity search on the agent_memory table's HNSW index.
        """
        if not query_embedding:
            return []

        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        result = await self.db.execute(
            text("""
                SELECT id, content, embedding <=> :embedding::vector AS distance, created_at
                FROM agent_memory
                WHERE sme_id = :sme_id AND memory_type = 'incident'
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """),
            {"sme_id": sme_id, "embedding": embedding_str, "limit": limit}
        )

        rows = result.fetchall()
        return [
            {"id": str(row[0]), "content": row[1], "distance": float(row[2]), "created_at": row[3].isoformat() if row[3] else None}
            for row in rows
        ]

    async def update_baseline(self, sme_id: str, metric_name: str, values: dict):
        """Update a learned baseline using UPSERT (CockroachDB native)."""
        await self.db.execute(
            text("""
                UPSERT INTO agent_baselines 
                (id, sme_id, metric_name, normal_range_low, normal_range_high, 
                 mean_value, std_deviation, sample_size, confidence, last_updated)
                VALUES (gen_random_uuid(), :sme_id, :metric, :low, :high, :mean, :std, :samples, :conf, now())
            """),
            {
                "sme_id": sme_id, "metric": metric_name,
                "low": values["normal_range_low"], "high": values["normal_range_high"],
                "mean": values["mean_value"], "std": values["std_deviation"],
                "samples": values["sample_size"], "conf": values["confidence"],
            }
        )
        await self.db.commit()
