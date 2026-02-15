"""
Script to run database migrations only.
Used during deployment.
"""
import sys
from server import check_and_run_migrations

print("Running database migrations...")
if check_and_run_migrations():
    print("✅ Migrations completed successfully.")
    sys.exit(0)
else:
    print("❌ Migrations failed.")
    sys.exit(1)
