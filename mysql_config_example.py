#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL Database Connection Example for SwanBoard

Set environment variables for MySQL configuration:
export MYSQL_DATABASE=swanlab
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
"""

from swanboard.db.db_connect import connect
import os

# Example 1: Connect using environment variables (used by SwanBoardCallback)
print("=== Using Environment Variables ===")
os.environ['MYSQL_DATABASE'] = 'swanlab'
os.environ['MYSQL_USER'] = 'root'
os.environ['MYSQL_PASSWORD'] = ''  # Set your password here
os.environ['MYSQL_HOST'] = 'localhost'
os.environ['MYSQL_PORT'] = '3306'

db_config = {
    'database': os.getenv('MYSQL_DATABASE', 'swanlab'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'autocreate': True
}

try:
    db = connect(**db_config)
    print("✓ Successfully connected using environment variables")
except Exception as e:
    print(f"✗ Failed to connect: {e}")

# Example 2: Connect to existing MySQL database directly
print("\n=== Direct Connection (No Auto-create) ===")
try:
    db = connect(
        database="swanlab_db",
        user="root",
        password="your_password",
        host="localhost",
        port=3306,
        autocreate=False
    )
    print("✓ Successfully connected to existing MySQL database")
except ConnectionError as e:
    print(f"✗ Failed to connect: {e}")

# Example 3: Auto-create MySQL database if it doesn't exist
print("\n=== Auto-create Database ===")
try:
    db = connect(
        database="swanlab_db",
        user="root",
        password="your_password",
        host="localhost",
        port=3306,
        autocreate=True
    )
    print("✓ Successfully connected to MySQL database (auto-created if needed)")
except Exception as e:
    print(f"✗ Failed to connect: {e}")

# Example 4: Subsequent connections (reuse previous config)
print("\n=== Reusing Configuration ===")
try:
    db = connect()  # Uses previously set configuration
    print("✓ Successfully reconnected using cached configuration")
except Exception as e:
    print(f"✗ Failed to reconnect: {e}")