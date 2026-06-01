#!/usr/bin/env python3
"""
Database Migration Script
Run schema migrations for Sovereign Grid
Version: 31.0
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.supabase_client import supabase


def run_migrations():
    """Run all pending migrations"""
    print("🔄 Running database migrations...")
    
    migrations_dir = Path(__file__).parent.parent / "database" / "schemas"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    
    for sql_file in sql_files:
        print(f"  📄 Running {sql_file.name}...")
        with open(sql_file, "r") as f:
            sql = f.read()
        
        try:
            supabase.table("_migrations").insert({"name": sql_file.name}).execute()
            print(f"  ✅ {sql_file.name} completed")
        except Exception as e:
            print(f"  ❌ {sql_file.name} failed: {e}")
            return False
    
    print("✅ All migrations completed successfully!")
    return True


def create_migration(name: str):
    """Create a new migration file"""
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.sql"
    filepath = Path(__file__).parent.parent / "database" / "schemas" / filename
    
    with open(filepath, "w") as f:
        f.write(f"-- Migration: {name}\n")
        f.write(f"-- Created: {datetime.datetime.now().isoformat()}\n")
        f.write("\n")
    
    print(f"✅ Created migration: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument("command", choices=["up", "create"], help="Command to run")
    parser.add_argument("--name", help="Migration name (for create)")
    
    args = parser.parse_args()
    
    if args.command == "up":
        success = run_migrations()
        sys.exit(0 if success else 1)
    elif args.command == "create":
        if not args.name:
            print("❌ Please provide --name for migration")
            sys.exit(1)
        create_migration(args.name)


if __name__ == "__main__":
    main()
