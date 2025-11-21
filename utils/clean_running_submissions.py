#!/usr/bin/env python3
"""Fix submissions stuck in 'running' status.

This script finds all submissions with status 'running' and updates them
to 'failed' status with an appropriate error message.

Usage:
    python utils/fix_running_submissions.py
"""

import sqlite3
from pathlib import Path


def fix_running_submissions():
    """Update all submissions with 'running' status to 'failed'."""
    db_path = Path(__file__).parent.parent / 'data' / 'leaderboard.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find all running submissions
    cursor.execute('''
        SELECT id, username, notebook_path, timestamp 
        FROM submissions 
        WHERE status = 'running'
    ''')
    
    running_submissions = cursor.fetchall()
    
    if not running_submissions:
        print("\nNo running submissions found.")
        conn.close()
        return
    
    print(f"\nFound {len(running_submissions)} running submission(s):")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Timestamp'}")
    print("-" * 80)
    for sub in running_submissions:
        print(f"{sub[0]:<5} {sub[1]:<20} {sub[3]}")
    
    print("\nThese will be marked as 'failed' with error message:")
    print("  'Execution timeout or interrupted'")
    
    # Update them to failed
    cursor.execute('''
        UPDATE submissions 
        SET status = 'failed',
            error_message = 'Execution timeout or interrupted'
        WHERE status = 'running'
    ''')
    
    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()
    
    print(f"\n✅ Updated {rows_updated} submission(s) from 'running' to 'failed'")


if __name__ == '__main__':
    print("This will update all 'running' submissions to 'failed' status")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        fix_running_submissions()
    else:
        print("Cancelled")
