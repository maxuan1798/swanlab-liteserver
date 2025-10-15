#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database initialization script for authentication tables
Run this to create authentication-related tables in MySQL
"""

import sys
from pathlib import Path

from swanboard.db import MySQLConfig

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from . import (
    connect_cloud_db,
    mysql_manager,
    AUTH_MODELS,
    Account,
    Tenant,
    TenantAccountJoin,
    AccountIntegrate,
    RefreshToken,
)

def create_auth_tables():
    """Create all authentication-related tables"""
    print("Connecting to database...")
    config = MySQLConfig(
        host="localhost",
        port=13306,
        user="swanlab_user",
        password="swanlab_user_456",
        database="swanlab_cloud"
    )
    # Connect to database
    connected = connect_cloud_db(config)

    if not connected:
        print("Error: Failed to connect to database")
        print("Please check your MySQL configuration in environment variables:")
        print("  - MYSQL_HOST")
        print("  - MYSQL_PORT")
        print("  - MYSQL_USER")
        print("  - MYSQL_PASSWORD")
        print("  - MYSQL_DATABASE")
        return False

    print("Connected to database successfully")
    print("\nCreating authentication tables...")

    try:
        # Create tables
        mysql_manager.get_database().create_tables(AUTH_MODELS, safe=True)

        print("\nAuthentication tables created successfully:")
        for model in AUTH_MODELS:
            print(f"  ✓ {model._meta.table_name}")

        return True

    except Exception as e:
        print(f"\nError creating tables: {e}")
        return False


def drop_auth_tables():
    """Drop all authentication-related tables (use with caution!)"""
    print("WARNING: This will delete all authentication data!")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != "yes":
        print("Operation cancelled")
        return False

    print("\nConnecting to database...")

    # Connect to database
    db = connect_cloud_db()

    if not db:
        print("Error: Failed to connect to database")
        return False

    print("Connected to database successfully")
    print("\nDropping authentication tables...")

    try:
        # Drop tables in reverse order to handle foreign key constraints
        db.drop_tables(reversed(AUTH_MODELS), safe=True)

        print("\nAuthentication tables dropped successfully:")
        for model in AUTH_MODELS:
            print(f"  ✓ {model._meta.table_name}")

        return True

    except Exception as e:
        print(f"\nError dropping tables: {e}")
        return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Authentication database initialization")
    parser.add_argument(
        "action",
        choices=["create", "drop", "recreate"],
        help="Action to perform (create, drop, or recreate tables)"
    )

    args = parser.parse_args()

    if args.action == "create":
        success = create_auth_tables()
    elif args.action == "drop":
        success = drop_auth_tables()
    elif args.action == "recreate":
        print("Recreating authentication tables...")
        drop_auth_tables()
        success = create_auth_tables()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
