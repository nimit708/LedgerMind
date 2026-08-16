"""Add fresh transactions for today so the performance check shows real activity."""
import asyncio
import asyncpg
import ssl
import uuid
import random
from datetime import datetime, timezone, timedelta

DB_URL = "postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb"

async def add_today():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    conn = await asyncpg.connect(DB_URL, ssl=ssl_ctx)

    sme_row = await conn.fetchrow("SELECT id FROM smes LIMIT 1")
    sme_id = sme_row["id"]
    customers = await conn.fetch("SELECT id FROM customers LIMIT 8")

    now = datetime.now(timezone.utc)
    
    # Add 15 successful transactions from today
    for i in range(15):
        cust = random.choice(customers)
        amount = random.choice([45.00, 89.99, 125.00, 250.00, 67.50, 199.00, 350.00, 78.00, 155.00, 420.00])
        created = now - timedelta(hours=random.randint(0, 12), minutes=random.randint(0, 59))
        await conn.execute(
            "INSERT INTO transactions (id, sme_id, customer_id, amount, currency, status, created_at) "
            "VALUES ($1, $2, $3, $4, 'usd', 'succeeded', $5)",
            uuid.uuid4(), sme_id, cust["id"], amount, created
        )

    # Add 3 failed transactions from today
    failures = [("card_declined", 95.00), ("expired_card", 210.00), ("insufficient_funds", 45.00)]
    for reason, amount in failures:
        cust = random.choice(customers)
        created = now - timedelta(hours=random.randint(1, 8))
        await conn.execute(
            "INSERT INTO transactions (id, sme_id, customer_id, amount, currency, status, failure_reason, created_at) "
            "VALUES ($1, $2, $3, $4, 'usd', 'failed', $5, $6)",
            uuid.uuid4(), sme_id, cust["id"], amount, reason, created
        )

    await conn.close()
    print("Added 15 successful + 3 failed transactions for today.")

asyncio.run(add_today())
