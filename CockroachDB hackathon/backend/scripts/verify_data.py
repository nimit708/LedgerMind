"""Quick verification of all CockroachDB data."""
import asyncio
import asyncpg
import ssl

DB_URL = "postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb"

async def verify():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncpg.connect(DB_URL, ssl=ssl_ctx)

    print("=== CockroachDB Data Summary ===\n")

    # Transactions
    row = await conn.fetchrow("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE status = 'succeeded') as ok, COUNT(*) FILTER (WHERE status = 'failed') as failed, COALESCE(SUM(amount), 0) as volume FROM transactions")
    print(f"Transactions: {row['total']} total ({row['ok']} succeeded, {row['failed']} failed)")
    print(f"Total volume: ${float(row['volume']):,.2f}")

    # Stripe-linked
    row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM transactions WHERE stripe_payment_intent_id IS NOT NULL")
    print(f"Stripe-linked transactions: {row['cnt']}")

    # Customers
    row = await conn.fetchrow("SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE stripe_customer_id IS NOT NULL) as stripe FROM customers")
    print(f"\nCustomers: {row['total']} total ({row['stripe']} with Stripe ID)")

    # Failures by reason
    rows = await conn.fetch("SELECT failure_reason, COUNT(*) as cnt FROM transactions WHERE status = 'failed' GROUP BY failure_reason ORDER BY cnt DESC")
    print(f"\nFailure breakdown:")
    for r in rows:
        print(f"  {r['failure_reason']}: {r['cnt']}")

    # Top customers by revenue
    rows = await conn.fetch("SELECT name, email, total_revenue FROM customers ORDER BY total_revenue DESC LIMIT 5")
    print(f"\nTop customers:")
    for r in rows:
        print(f"  {r['name']} ({r['email']}) - ${float(r['total_revenue']):,.2f}")

    await conn.close()

asyncio.run(verify())
