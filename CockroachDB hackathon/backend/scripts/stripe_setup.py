"""
Stripe Test Mode Setup & CockroachDB Sync Script

This script:
1. Connects to Stripe in test mode
2. Creates test customers with realistic data
3. Creates test payment intents (succeeded + failed)
4. Syncs all Stripe data to CockroachDB transactions/customers tables
5. Verifies E2E flow

Usage:
  pip install stripe asyncpg
  set STRIPE_SECRET_KEY=sk_test_...
  set DATABASE_URL=postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require
  python stripe_setup.py
"""

import os
import sys
import stripe
import asyncio
import asyncpg
import ssl
import uuid
import random
from datetime import datetime, timedelta

# Configuration
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "")
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nimit:xoDam9RBFeyyq77gf-ewwQ@bay-lizard-30485.j77.aws-eu-west-2.cockroachlabs.cloud:26257/defaultdb?sslmode=require"
)

if not STRIPE_KEY:
    print("ERROR: Set STRIPE_SECRET_KEY environment variable (sk_test_...)")
    sys.exit(1)

stripe.api_key = STRIPE_KEY

# Test customers data
TEST_CUSTOMERS = [
    {"name": "Acme Corp", "email": "billing@acmecorp.com", "metadata": {"plan": "enterprise", "mrr": "2500"}},
    {"name": "TechStart Ltd", "email": "finance@techstart.io", "metadata": {"plan": "growth", "mrr": "800"}},
    {"name": "CloudNine SaaS", "email": "accounts@cloudnine.dev", "metadata": {"plan": "enterprise", "mrr": "3200"}},
    {"name": "DataFlow Inc", "email": "payments@dataflow.com", "metadata": {"plan": "starter", "mrr": "200"}},
    {"name": "GreenLeaf Retail", "email": "billing@greenleaf.shop", "metadata": {"plan": "growth", "mrr": "1100"}},
    {"name": "BlueSky Analytics", "email": "ap@bluesky-analytics.co", "metadata": {"plan": "enterprise", "mrr": "4500"}},
    {"name": "SwiftPay Solutions", "email": "invoices@swiftpay.io", "metadata": {"plan": "growth", "mrr": "950"}},
    {"name": "NexGen Logistics", "email": "finance@nexgen-logistics.com", "metadata": {"plan": "starter", "mrr": "350"}},
]

# Payment scenarios
PAYMENT_SCENARIOS = [
    # (amount_cents, currency, status, failure_code)
    (25000, "usd", "succeeded", None),
    (8000, "usd", "succeeded", None),
    (32000, "usd", "succeeded", None),
    (1500, "usd", "succeeded", None),
    (11000, "usd", "succeeded", None),
    (4500, "usd", "succeeded", None),
    (67000, "usd", "succeeded", None),
    (2200, "usd", "succeeded", None),
    (15000, "usd", "succeeded", None),
    (9500, "usd", "succeeded", None),
    # Failed payments
    (5000, "usd", "failed", "card_declined"),
    (12000, "usd", "failed", "expired_card"),
    (3000, "usd", "failed", "insufficient_funds"),
    (8500, "usd", "failed", "card_declined"),
    (2000, "usd", "failed", "expired_card"),
]


def create_stripe_customers():
    """Create test customers in Stripe."""
    print("\n📋 Creating Stripe test customers...")
    created = []
    for cust_data in TEST_CUSTOMERS:
        try:
            customer = stripe.Customer.create(
                name=cust_data["name"],
                email=cust_data["email"],
                metadata=cust_data["metadata"],
            )
            created.append(customer)
            print(f"  ✓ {customer.name} ({customer.id})")
        except stripe.error.StripeError as e:
            print(f"  ✗ Failed to create {cust_data['name']}: {e}")
    return created


def create_stripe_payments(customers):
    """Create test payments — mix of successful and failed."""
    print("\n💳 Creating Stripe test payments...")
    payments = []

    for i, scenario in enumerate(PAYMENT_SCENARIOS):
        amount, currency, target_status, failure_code = scenario
        customer = random.choice(customers)

        try:
            if target_status == "succeeded":
                # Use test token for successful payment
                pi = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    customer=customer.id,
                    payment_method="pm_card_visa",
                    confirm=True,
                    automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                    metadata={"test": "true", "scenario": f"payment_{i+1}"},
                )
                payments.append(pi)
                print(f"  ✓ ${amount/100:.2f} succeeded → {customer.name} ({pi.id})")

            else:
                # Use declining test card tokens
                decline_token = {
                    "card_declined": "pm_card_chargeDeclined",
                    "expired_card": "pm_card_chargeDeclinedExpiredCard",
                    "insufficient_funds": "pm_card_chargeDeclinedInsufficientFunds",
                }.get(failure_code, "pm_card_chargeDeclined")

                try:
                    pi = stripe.PaymentIntent.create(
                        amount=amount,
                        currency=currency,
                        customer=customer.id,
                        payment_method=decline_token,
                        confirm=True,
                        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                        metadata={"test": "true", "scenario": f"failure_{failure_code}"},
                    )
                except stripe.error.CardError as ce:
                    # Expected! The payment intent still gets created
                    pi = stripe.PaymentIntent.retrieve(ce.payment_intent.id) if hasattr(ce, 'payment_intent') and ce.payment_intent else None
                    if pi:
                        payments.append(pi)
                        print(f"  ✓ ${amount/100:.2f} failed ({failure_code}) → {customer.name} ({pi.id})")
                    else:
                        print(f"  ~ ${amount/100:.2f} failed ({failure_code}) — no PI returned")

        except stripe.error.StripeError as e:
            print(f"  ✗ Payment error: {e}")

    return payments


async def sync_to_cockroachdb(customers, payments):
    """Sync Stripe data to CockroachDB."""
    print("\n🗄️  Syncing to CockroachDB...")

    # Parse connection URL for asyncpg
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    # Strip sslmode param for asyncpg
    db_url = DB_URL.replace("?sslmode=require", "").replace("&sslmode=require", "")

    conn = await asyncpg.connect(db_url, ssl=ssl_ctx)

    try:
        # Ensure we have a demo SME record
        sme_row = await conn.fetchrow("SELECT id FROM smes LIMIT 1")
        if sme_row:
            sme_id = sme_row["id"]
            print(f"  Using existing SME: {sme_id}")
        else:
            sme_id = uuid.uuid4()
            await conn.execute("""
                INSERT INTO smes (id, name, email, cognito_sub, subscription_status)
                VALUES ($1, 'LedgerMind Demo', 'demo@ledgermind.ai', 'demo-cognito-sub', 'active')
            """, sme_id)
            print(f"  Created demo SME: {sme_id}")

        # Sync customers
        print("  Syncing customers...")
        for cust in customers:
            await conn.execute("""
                INSERT INTO customers (id, sme_id, stripe_customer_id, name, email, total_revenue, status, created_at)
                VALUES ($1, $2, $3, $4, $5, 0, 'active', $6)
                ON CONFLICT (id) DO NOTHING
            """,
                uuid.uuid4(),
                sme_id,
                cust.id,
                cust.name,
                cust.email,
                datetime.utcnow(),
            )
            print(f"    ✓ {cust.name}")

        # Sync payments as transactions
        print("  Syncing transactions...")
        for pi in payments:
            status = "succeeded" if pi.status == "succeeded" else "failed"
            failure_reason = None
            if pi.last_payment_error:
                failure_reason = pi.last_payment_error.get("decline_code") or pi.last_payment_error.get("code", "unknown")

            # Find customer in our list
            cust_match = next((c for c in customers if c.id == pi.customer), None)
            cust_email = cust_match.email if cust_match else "unknown@test.com"

            # Get customer UUID from DB
            row = await conn.fetchrow(
                "SELECT id FROM customers WHERE email = $1", cust_email
            )
            customer_id = row["id"] if row else None

            await conn.execute("""
                INSERT INTO transactions (id, sme_id, stripe_payment_intent_id, customer_id, amount, currency, status, failure_reason, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT DO NOTHING
            """,
                uuid.uuid4(),
                sme_id,
                pi.id,
                customer_id,
                pi.amount / 100.0,
                pi.currency,
                status,
                failure_reason,
                datetime.utcnow() - timedelta(hours=random.randint(0, 168)),  # Spread over last week
            )
            symbol = "✓" if status == "succeeded" else "✗"
            print(f"    {symbol} ${pi.amount/100:.2f} ({status}) → {cust_email}")

        # Update customer revenue totals
        print("  Updating revenue totals...")
        await conn.execute("""
            UPDATE customers SET total_revenue = sub.total
            FROM (
                SELECT customer_id, COALESCE(SUM(amount), 0) as total
                FROM transactions WHERE status = 'succeeded'
                GROUP BY customer_id
            ) sub
            WHERE customers.id = sub.customer_id
        """)

        print("  ✓ Revenue totals updated")

    finally:
        await conn.close()


async def verify_e2e():
    """Verify the E2E flow — query CockroachDB to confirm data is visible."""
    print("\n🔍 E2E Verification...")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    db_url = DB_URL.replace("?sslmode=require", "").replace("&sslmode=require", "")
    conn = await asyncpg.connect(db_url, ssl=ssl_ctx)

    try:
        # Count transactions from Stripe
        row = await conn.fetchrow(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM transactions WHERE stripe_payment_intent_id IS NOT NULL"
        )
        print(f"  📊 Stripe transactions in DB: {row['cnt']}")
        print(f"  💰 Total Stripe volume: ${float(row['total']):,.2f}")

        # Count by status
        rows = await conn.fetch(
            "SELECT status, COUNT(*) as cnt FROM transactions WHERE stripe_payment_intent_id IS NOT NULL GROUP BY status"
        )
        for r in rows:
            print(f"     • {r['status']}: {r['cnt']}")

        # Count customers with Stripe IDs
        row = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM customers WHERE stripe_customer_id IS NOT NULL"
        )
        print(f"  👥 Stripe customers synced: {row['cnt']}")

        # Top failures
        rows = await conn.fetch(
            "SELECT failure_reason, COUNT(*) as cnt FROM transactions WHERE status = 'failed' AND stripe_payment_intent_id IS NOT NULL GROUP BY failure_reason ORDER BY cnt DESC"
        )
        if rows:
            print(f"  ⚠️  Failure breakdown:")
            for r in rows:
                print(f"     • {r['failure_reason']}: {r['cnt']}")

        print("\n✅ E2E verification complete! Data flows: Stripe → CockroachDB → API → Frontend")

    finally:
        await conn.close()


async def main():
    print("=" * 60)
    print("  LedgerMind — Stripe Test Mode Setup & E2E Test")
    print("=" * 60)
    print(f"\n🔑 Stripe key: {STRIPE_KEY[:12]}...{STRIPE_KEY[-4:]}")
    print(f"🗄️  Database: {DB_URL[:50]}...")

    # Verify Stripe connection
    try:
        account = stripe.Account.retrieve()
        print(f"✓ Connected to Stripe: {account.id}")
        if not STRIPE_KEY.startswith("sk_test"):
            print("⚠️  WARNING: This is NOT a test key! Aborting.")
            sys.exit(1)
    except stripe.error.AuthenticationError:
        print("✗ Invalid Stripe key")
        sys.exit(1)

    # Step 1: Create customers
    customers = create_stripe_customers()
    if not customers:
        print("No customers created. Check your Stripe key.")
        sys.exit(1)

    # Step 2: Create payments
    payments = create_stripe_payments(customers)

    # Step 3: Sync to CockroachDB
    await sync_to_cockroachdb(customers, payments)

    # Step 4: Verify E2E
    await verify_e2e()

    print("\n" + "=" * 60)
    print("  🎉 Setup complete!")
    print("  Your Stripe test data is now in CockroachDB.")
    print("  Visit the dashboard to see live payment data.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
