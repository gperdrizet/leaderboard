#!/usr/bin/env python3
"""Fix submissions stuck in 'running' status.

This script finds all submissions with status 'running' and updates them
to 'failed' status with an appropriate error message.

Usage:
    python utils/clean_running_submissions.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.logger import configure_warnings_logging

# Configure warnings to be captured in logs
configure_warnings_logging()


def fix_running_submissions():
    """Update all submissions with 'running' status to 'failed'."""
    db = Database('data/leaderboard.db')

    all_submissions = db.get_all_submissions()
    running = [s for s in all_submissions if s['status'] == 'running']

    if not running:
        print("\nNo running submissions found.")
        return

    print(f"\nFound {len(running)} running submission(s):")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Timestamp'}")
    print("-" * 80)
    for sub in running:
        print(f"{sub['id']:<5} {sub['username']:<20} {sub['timestamp']}")

    print("\nThese will be marked as 'failed' with error message:")
    print("  'Execution timeout or interrupted'")

    for sub in running:
        db.update_submission(
            sub['id'],
            status='failed',
            error_message='Execution timeout or interrupted'
        )

    print(f"\n✅ Updated {len(running)} submission(s) from 'running' to 'failed'")


if __name__ == '__main__':
    print("This will update all 'running' submissions to 'failed' status")
    response = input("\nContinue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        fix_running_submissions()
    else:
        print("Cancelled")
