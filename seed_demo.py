"""Seed the database with realistic demo data for screenshots."""
import asyncio
import uuid
from datetime import date, datetime, timezone, timedelta

import asyncpg


async def main():
    conn = await asyncpg.connect(
        user="contractflow",
        password="contractflow",
        database="contractflow",
        host="localhost",
    )

    now = datetime.now(timezone.utc)

    # Create departments
    dept_legal = uuid.uuid4()
    dept_procurement = uuid.uuid4()
    dept_engineering = uuid.uuid4()
    dept_finance = uuid.uuid4()

    departments = [
        (dept_legal, "Legal", "Corporate legal department"),
        (dept_procurement, "Procurement", "Vendor and supplier management"),
        (dept_engineering, "Engineering", "Software engineering division"),
        (dept_finance, "Finance", "Financial operations and accounting"),
    ]

    for dept_id, name, desc in departments:
        await conn.execute(
            """INSERT INTO departments (id, name, description, is_active, created_at, updated_at)
               VALUES ($1, $2, $3, true, $4, $4)""",
            dept_id, name, desc, now,
        )

    # Create users with argon2 hashed password "demo123"
    # Pre-computed argon2id hash for "demo123"
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    pw_hash = ph.hash("demo1234")

    admin_id = uuid.uuid4()
    approver_id = uuid.uuid4()
    contributor_id = uuid.uuid4()
    viewer_id = uuid.uuid4()

    users = [
        (admin_id, "admin@contractflow.dev", "Pete Shamoon", "super_admin", dept_engineering),
        (approver_id, "sarah.chen@contractflow.dev", "Sarah Chen", "approver", dept_legal),
        (contributor_id, "james.wilson@contractflow.dev", "James Wilson", "contributor", dept_procurement),
        (viewer_id, "maria.garcia@contractflow.dev", "Maria Garcia", "viewer", dept_finance),
    ]

    for uid, email, name, role, dept in users:
        await conn.execute(
            """INSERT INTO users (id, email, display_name, role, password_hash, is_active, department_id, created_at, updated_at)
               VALUES ($1, $2, $3, $4::userrole, $5, true, $6, $7, $7)""",
            uid, email, name, role, pw_hash, dept, now,
        )

    # Create contracts with realistic data
    contracts = [
        ("CF-2026-001", "Azure Enterprise Agreement", "Enterprise cloud services agreement with Microsoft Azure for production infrastructure", "active", date(2026, 1, 1), date(2027, 12, 31), 245000.00, admin_id, dept_engineering),
        ("CF-2026-002", "Datadog Monitoring SaaS", "Application performance monitoring and log management platform", "active", date(2026, 2, 1), date(2027, 1, 31), 36000.00, contributor_id, dept_engineering),
        ("CF-2026-003", "Office Space Lease - Floor 12", "Commercial office lease for headquarters expansion", "pending_approval", date(2026, 4, 1), date(2029, 3, 31), 1850000.00, contributor_id, dept_finance),
        ("CF-2026-004", "Cybersecurity Insurance Policy", "Comprehensive cyber liability and breach response coverage", "active", date(2026, 1, 15), date(2027, 1, 14), 78500.00, approver_id, dept_legal),
        ("CF-2026-005", "AWS Backup DR Agreement", "Disaster recovery and cross-cloud backup services", "draft", date(2026, 5, 1), date(2027, 4, 30), 42000.00, admin_id, dept_engineering),
        ("CF-2026-006", "Legal Counsel Retainer - Baker McKenzie", "Outside counsel retainer for M&A advisory services", "active", date(2025, 7, 1), date(2026, 6, 30), 180000.00, approver_id, dept_legal),
        ("CF-2026-007", "Salesforce CRM License", "Enterprise CRM platform with 150 user licenses", "expired", date(2025, 1, 1), date(2025, 12, 31), 67500.00, contributor_id, dept_procurement),
        ("CF-2026-008", "GitHub Enterprise Cloud", "Source code management and CI/CD platform", "active", date(2026, 3, 1), date(2027, 2, 28), 21600.00, admin_id, dept_engineering),
        ("CF-2026-009", "Cleaning Services - JanPro", "Commercial cleaning services for all office floors", "active", date(2026, 1, 1), date(2026, 12, 31), 14400.00, contributor_id, dept_procurement),
        ("CF-2026-010", "SOC 2 Audit Engagement", "Annual SOC 2 Type II audit by Deloitte", "pending_approval", date(2026, 6, 1), date(2026, 11, 30), 95000.00, approver_id, dept_legal),
        ("CF-2026-011", "Dell Hardware Refresh", "Laptop and workstation procurement for Q3 refresh cycle", "draft", date(2026, 7, 1), date(2026, 9, 30), 128000.00, contributor_id, dept_procurement),
        ("CF-2026-012", "Snowflake Data Warehouse", "Cloud data warehouse for analytics and reporting", "active", date(2026, 2, 15), date(2027, 2, 14), 54000.00, admin_id, dept_engineering),
    ]

    for num, title, desc, status, start, end, value, owner, dept in contracts:
        await conn.execute(
            """INSERT INTO contracts (id, contract_number, title, description, status, start_date, end_date, value_usd, renewal_notice_days, owner_id, department_id, is_deleted, version, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5::contractstatus, $6, $7, $8, 30, $9, $10, false, 1, $11, $11)""",
            uuid.uuid4(), num, title, desc, status, start, end, value, owner, dept, now,
        )

    # Create some audit log entries
    audit_actions = [
        ("login", "user", admin_id, admin_id, "192.168.1.100"),
        ("create", "contract", uuid.uuid4(), admin_id, "192.168.1.100"),
        ("login", "user", approver_id, approver_id, "10.0.0.45"),
        ("approve", "contract", uuid.uuid4(), approver_id, "10.0.0.45"),
        ("create", "contract", uuid.uuid4(), contributor_id, "172.16.0.22"),
        ("upload", "contract", uuid.uuid4(), contributor_id, "172.16.0.22"),
        ("login", "user", viewer_id, viewer_id, "192.168.1.55"),
        ("status_change", "contract", uuid.uuid4(), admin_id, "192.168.1.100"),
    ]

    for action, res_type, res_id, actor, ip in audit_actions:
        await conn.execute(
            """INSERT INTO audit_logs (id, action, resource_type, resource_id, actor_id, ip_address, created_at, updated_at)
               VALUES ($1, $2::auditaction, $3, $4, $5, $6, $7, $7)""",
            uuid.uuid4(), action, res_type, res_id, actor, ip, now - timedelta(hours=len(audit_actions)),
        )
        now = now + timedelta(minutes=15)

    await conn.close()
    print("Demo data seeded successfully!")
    print("Login: admin@contractflow.dev / demo1234")


asyncio.run(main())
