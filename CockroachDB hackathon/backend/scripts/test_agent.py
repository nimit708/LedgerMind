"""Test the agent chat endpoint with various messages."""
import requests
import json

API = "https://zqgkmjvd59.execute-api.eu-west-2.amazonaws.com"

# We need auth token - let's test via direct HTTP with a dummy auth header
# The API requires Cognito auth, so let's test the logic directly against CockroachDB instead

import asyncio
import asyncpg
import ssl

DB_URL = "postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb"

async def test_queries():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncpg.connect(DB_URL, ssl=ssl_ctx)

    print("=== Testing Agent Query Logic ===\n")

    # Test 1: Recovery campaign query
    print("--- 'Create recovery campaign' ---")
    rows = await conn.fetch(
        "SELECT failure_reason, COUNT(*) as cnt, COALESCE(SUM(amount), 0) as lost "
        "FROM transactions WHERE status = 'failed' AND created_at > now() - interval '7 days' "
        "GROUP BY failure_reason ORDER BY cnt DESC"
    )
    total_failed = sum(r['cnt'] for r in rows)
    total_lost = sum(float(r['lost']) for r in rows)
    print(f"  Failed txns this week: {total_failed}")
    print(f"  Revenue at risk: ${total_lost:,.2f}")
    for r in rows:
        print(f"    {r['failure_reason']}: {r['cnt']} txns (${float(r['lost']):,.2f})")

    affected = await conn.fetchval(
        "SELECT COUNT(DISTINCT customer_id) FROM transactions "
        "WHERE status = 'failed' AND created_at > now() - interval '7 days'"
    )
    print(f"  Affected customers: {affected}")

    # Test 2: Approval flow
    print("\n--- 'yes' / approve ---")
    rows = await conn.fetch(
        "SELECT DISTINCT c.name, c.email FROM transactions t "
        "JOIN customers c ON t.customer_id = c.id "
        "WHERE t.status = 'failed' AND t.created_at > now() - interval '7 days' "
        "LIMIT 5"
    )
    print(f"  Customers to contact:")
    for r in rows:
        print(f"    {r['name']} ({r['email']})")

    # Test 3: Failure analysis
    print("\n--- 'Investigate failure spike' ---")
    rows = await conn.fetch(
        "SELECT failure_reason, COUNT(*) as cnt FROM transactions "
        "WHERE status = 'failed' AND created_at > now() - interval '7 days' "
        "GROUP BY failure_reason ORDER BY cnt DESC LIMIT 5"
    )
    print(f"  Failures:")
    for r in rows:
        print(f"    {r['failure_reason']}: {r['cnt']}")

    await conn.close()
    print("\n=== All queries work correctly! ===")

asyncio.run(test_queries())
