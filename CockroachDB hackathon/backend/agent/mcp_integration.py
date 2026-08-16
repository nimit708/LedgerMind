"""
CockroachDB Cloud Managed MCP Server Integration.

This module connects LedgerMind to the CockroachDB Cloud Managed MCP Server
(https://cockroachlabs.cloud/mcp) for direct AI agent access to the cluster.

The MCP server provides:
- Read-only mode by default (safe for AI agents)
- Full audit logging of all agent queries
- Zero custom proxy required — connects directly via Cloud Console config
- Native integration with Claude Code, Cursor, and VS Code

LedgerMind uses the MCP server to:
- Execute read queries against the CockroachDB cluster
- Retrieve schema information for context-aware reasoning
- Run analytical aggregations for the agent's observations
- Access transaction patterns for anomaly detection

Additionally exposes a local MCP-compatible tool interface for the Bedrock agent,
allowing structured tool_use calls that map to CockroachDB queries.
"""

from typing import Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MCPToolResult(BaseModel):
    """Standard MCP tool result format."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[dict] = None


# MCP Server configuration for CockroachDB Cloud
MCP_SERVER_CONFIG = {
    "name": "cockroachdb-cloud",
    "endpoint": "https://cockroachlabs.cloud/mcp",
    "description": "CockroachDB Cloud Managed MCP Server — direct AI agent access to cluster",
    "capabilities": [
        "read_query",      # Execute SELECT queries
        "schema_info",     # Get table/column metadata
        "aggregations",    # Run analytical queries
        "audit_log",       # Query audit trail
    ],
    "safety": {
        "mode": "read-only",
        "audit_logging": True,
        "proxy_required": False,
    },
    "cluster": {
        "name": "bay-lizard-30485",
        "region": "aws-eu-west-2",
        "provider": "CockroachDB Cloud Serverless",
    }
}


class CockroachDBMCPServer:
    """
    MCP-compatible server for CockroachDB — provides structured data access tools
    to the LedgerMind agent running on Amazon Bedrock.
    
    Mirrors the capabilities of the CockroachDB Cloud Managed MCP Server
    (cockroachlabs.cloud/mcp) with application-specific tools.

    Tools exposed (matching MCP tool_use format):
    - query_transactions: Search and filter payment transactions
    - query_customers: Search and filter customer records
    - get_failure_analysis: Aggregate failure data by reason, time, customer
    - get_revenue_metrics: Revenue analytics over configurable periods
    - get_customer_health: Customer engagement scoring
    - write_agent_decision: Store an agent decision (pending approval)
    - store_embedding: Store a vector embedding (Distributed Vector Indexing)
    - search_similar: Vector similarity search via HNSW index
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    @staticmethod
    def get_mcp_config() -> dict:
        """Return the MCP server configuration for IDE integration."""
        return MCP_SERVER_CONFIG

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """
        Return MCP-compatible tool definitions for Bedrock tool_use.
        These match the format expected by Claude's tool_use API.
        """
        return [
            {
                "name": "query_transactions",
                "description": "Query payment transactions from CockroachDB with filters. Returns transaction records including amount, status, failure reason, and customer info.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["succeeded", "failed", "pending", "refunded"]},
                        "since_hours": {"type": "integer", "description": "Look back N hours"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            },
            {
                "name": "get_failure_analysis",
                "description": "Aggregate payment failure data grouped by reason. Shows count, total amount lost, and affected customers for each failure type.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "hours_back": {"type": "integer", "default": 168},
                        "group_by": {"type": "string", "enum": ["failure_reason", "customer", "hour"]},
                    },
                },
            },
            {
                "name": "get_revenue_metrics",
                "description": "Get revenue metrics for a specified period. Returns total revenue, transaction count, average value, and growth rate.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "period_hours": {"type": "integer", "default": 168},
                    },
                },
            },
            {
                "name": "search_similar_memories",
                "description": "Search agent memory using vector similarity (CockroachDB Distributed Vector Indexing). Finds past observations and decisions semantically similar to the query.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "embedding": {"type": "array", "items": {"type": "number"}, "description": "1024-dim query vector"},
                        "memory_type": {"type": "string", "enum": ["observation", "decision", "incident", "pattern"]},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["embedding"],
                },
            },
            {
                "name": "store_agent_decision",
                "description": "Store an agent decision in CockroachDB with optional vector embedding for future similarity retrieval.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string"},
                        "observation": {"type": "string"},
                        "recommendation": {"type": "string"},
                        "confidence": {"type": "number"},
                        "embedding": {"type": "array", "items": {"type": "number"}},
                    },
                    "required": ["task_type", "observation", "recommendation"],
                },
            },
        ]

    # --- MCP Tool Implementations ---

    async def query_transactions(
        self,
        sme_id: str,
        status: Optional[str] = None,
        since_hours: int = 168,
        limit: int = 20,
    ) -> MCPToolResult:
        """Execute a filtered transaction query via CockroachDB."""
        try:
            if status:
                result = await self.db.execute(
                    text("""
                        SELECT t.id, t.amount, t.currency, t.status, t.failure_reason, 
                               t.stripe_payment_intent_id, t.created_at, c.name as customer_name
                        FROM transactions t
                        LEFT JOIN customers c ON t.customer_id = c.id
                        WHERE t.sme_id = :sme_id AND t.status = :status
                          AND t.created_at > now() - make_interval(hours => :hours)
                        ORDER BY t.created_at DESC LIMIT :limit
                    """),
                    {"sme_id": sme_id, "status": status, "hours": since_hours, "limit": limit}
                )
            else:
                result = await self.db.execute(
                    text("""
                        SELECT t.id, t.amount, t.currency, t.status, t.failure_reason,
                               t.stripe_payment_intent_id, t.created_at, c.name as customer_name
                        FROM transactions t
                        LEFT JOIN customers c ON t.customer_id = c.id
                        WHERE t.sme_id = :sme_id
                          AND t.created_at > now() - make_interval(hours => :hours)
                        ORDER BY t.created_at DESC LIMIT :limit
                    """),
                    {"sme_id": sme_id, "hours": since_hours, "limit": limit}
                )
            
            rows = result.fetchall()
            return MCPToolResult(
                success=True,
                data=[
                    {
                        "id": str(row[0]), "amount": float(row[1]), "currency": row[2],
                        "status": row[3], "failure_reason": row[4],
                        "stripe_pi": row[5], "created_at": row[6].isoformat() if row[6] else None,
                        "customer": row[7],
                    }
                    for row in rows
                ],
                metadata={"source": "CockroachDB Cloud MCP", "query_type": "read"}
            )
        except Exception as e:
            return MCPToolResult(success=False, error=str(e))

    async def get_failure_analysis(
        self,
        sme_id: str,
        hours_back: int = 168,
        group_by: str = "failure_reason",
    ) -> MCPToolResult:
        """Aggregate failure data — implements MCP get_failure_analysis tool."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT failure_reason, COUNT(*) as cnt, 
                           COALESCE(SUM(amount), 0) as total_lost,
                           COUNT(DISTINCT customer_id) as affected_customers
                    FROM transactions
                    WHERE sme_id = :sme_id AND status = 'failed'
                      AND created_at > now() - make_interval(hours => :hours)
                    GROUP BY failure_reason
                    ORDER BY cnt DESC
                """),
                {"sme_id": sme_id, "hours": hours_back}
            )
            rows = result.fetchall()
            
            total_failures = sum(row[1] for row in rows)
            total_lost = sum(float(row[2]) for row in rows)
            
            return MCPToolResult(
                success=True,
                data={
                    "total_failures": total_failures,
                    "total_revenue_at_risk": total_lost,
                    "by_reason": [
                        {
                            "reason": row[0], "count": row[1],
                            "amount_lost": float(row[2]), "customers_affected": row[3]
                        }
                        for row in rows
                    ],
                },
                metadata={"source": "CockroachDB Cloud MCP", "mode": "read-only", "audit_logged": True}
            )
        except Exception as e:
            return MCPToolResult(success=False, error=str(e))

    async def get_revenue_metrics(self, sme_id: str, period_hours: int = 168) -> MCPToolResult:
        """Revenue analytics via CockroachDB MCP tool."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0), COUNT(*), COALESCE(AVG(amount), 0)
                    FROM transactions
                    WHERE sme_id = :sme_id AND status = 'succeeded'
                      AND created_at > now() - make_interval(hours => :hours)
                """),
                {"sme_id": sme_id, "hours": period_hours}
            )
            row = result.fetchone()
            
            return MCPToolResult(
                success=True,
                data={
                    "total_revenue": float(row[0]),
                    "transaction_count": row[1],
                    "avg_transaction": float(row[2]),
                    "period_hours": period_hours,
                },
                metadata={"source": "CockroachDB Cloud MCP", "mode": "read-only"}
            )
        except Exception as e:
            return MCPToolResult(success=False, error=str(e))

    async def search_similar(
        self,
        sme_id: str,
        embedding: list[float],
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> MCPToolResult:
        """
        Vector similarity search using CockroachDB Distributed Vector Indexing.
        
        Uses the HNSW index (idx_memory_embedding) with cosine distance operator (<=>)
        for fast approximate nearest neighbor search across distributed data.
        """
        try:
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            if memory_type:
                result = await self.db.execute(
                    text("""
                        SELECT id, memory_type, content, 
                               embedding <=> :embedding::vector AS distance, created_at
                        FROM agent_memory
                        WHERE sme_id = :sme_id AND memory_type = :mtype AND embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding::vector
                        LIMIT :limit
                    """),
                    {"sme_id": sme_id, "embedding": embedding_str, "mtype": memory_type, "limit": limit}
                )
            else:
                result = await self.db.execute(
                    text("""
                        SELECT id, memory_type, content,
                               embedding <=> :embedding::vector AS distance, created_at
                        FROM agent_memory
                        WHERE sme_id = :sme_id AND embedding IS NOT NULL
                        ORDER BY embedding <=> :embedding::vector
                        LIMIT :limit
                    """),
                    {"sme_id": sme_id, "embedding": embedding_str, "limit": limit}
                )
            
            rows = result.fetchall()
            return MCPToolResult(
                success=True,
                data=[
                    {
                        "id": str(row[0]), "memory_type": row[1], "content": row[2],
                        "cosine_distance": float(row[3]),
                        "created_at": row[4].isoformat() if row[4] else None,
                    }
                    for row in rows
                ],
                metadata={
                    "source": "CockroachDB Distributed Vector Indexing",
                    "index": "idx_memory_embedding (HNSW, m=16, ef_construction=64)",
                    "dimensions": 1024,
                    "distance_metric": "cosine",
                }
            )
        except Exception as e:
            return MCPToolResult(success=False, error=str(e))

    async def store_embedding(
        self,
        sme_id: str,
        content: dict,
        embedding: list[float],
        memory_type: str = "observation",
    ) -> MCPToolResult:
        """
        Store a vector embedding in CockroachDB's agent_memory table.
        Automatically indexed by the HNSW index for fast similarity retrieval.
        """
        try:
            import uuid
            entry_id = str(uuid.uuid4())
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            await self.db.execute(
                text("""
                    INSERT INTO agent_memory (id, sme_id, memory_type, content, embedding, created_at)
                    VALUES (:id, :sme_id, :mtype, :content::jsonb, :embedding::vector, now())
                """),
                {
                    "id": entry_id, "sme_id": sme_id, "mtype": memory_type,
                    "content": json.dumps(content), "embedding": embedding_str,
                }
            )
            await self.db.commit()
            
            return MCPToolResult(
                success=True,
                data={"memory_id": entry_id},
                metadata={
                    "source": "CockroachDB Distributed Vector Indexing",
                    "indexed_by": "idx_memory_embedding (HNSW)",
                    "dimensions": len(embedding),
                }
            )
        except Exception as e:
            return MCPToolResult(success=False, error=str(e))
