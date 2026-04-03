"""Database seeder — ensures demo data exists in the database.

Called from bootstrap.py on startup. All seeding logic from bootstrap.py
is preserved here.  The governance_repository no longer needs to load
in-memory seed data in its constructor.
"""

from __future__ import annotations

from app.db.bootstrap import initialize_database


def ensure_demo_data_seeded() -> None:
    """Ensure demo data is present in the database.

    This delegates to the existing ``initialize_database()`` function in
    ``bootstrap.py`` which already handles idempotent seeding of all demo
    entities (tenants, users, teams, templates, requests, runs, artifacts,
    review queue, promotions, checks, capabilities, policies, transition
    gates, integrations, and audit events).

    This function exists as the canonical entry point for seed management
    so that callers don't need to know about ``bootstrap.py`` internals.
    """
    initialize_database()
