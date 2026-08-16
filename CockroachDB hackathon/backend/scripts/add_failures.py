"""Add synthetic failed transactions with Stripe-style IDs to CockroachDB."""
import asyncio
import asyncpg
import ssl
import uuid
import random
from datetime import datetime, timezone, timedelta

DB_URL = "postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb"

async def add_failures():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncpg.connect(DB_URL, ssl=ssl_ctx)

    sme_row = await conn.fetchrow("SELECT id FROM smes LIMIT 1")
    sme_id = sme_row["id"]

    customers = await conn.fetch("SELECT id, email FROM customers WHERE stripe_customer_id IS NOT NULL")

    failures = [
        ("card_declined", 50.00),
        ("expired_card", 120.00),
        ("insufficient_funds", 30.00),
        ("card_declined", 85.00),
        ("expired_card", 20.00),
        ("card_declined", 175.00),
        ("insufficient_funds", 95.00),
        ("expired_card", 45.00),
    ]

    for reason, amount in failures:
        cust = random.choice(customers)
        pi_id = f"pi_test_failed_{uuid.uuid4().hex[:12]}"
        await conn.execute(
            "INSERT INTO transactions (id, sme_id, stripe_payment_intent_id, customer_id, amount, currency, status, failure_reason, created_at) "
            "VALUES ($1, $2, $3, $4, $5, 'usd', 'failed', $6, $7)",
            uuid.uuid4(), sme_id, pi_id,
            cust["id"], amount, reason,
            datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 120))
        )
        print(f"  x ${amount:.2f} failed ({reason}) -> {cust['email']}")

    await conn.close()
    print("\nDone! 8 failed transactions added to CockroachDB.")

asyncio.run(add_failures())
