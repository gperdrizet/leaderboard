#!/usr/bin/env python3
"""Script to remove submissions from the leaderboard database.

Usage:
    1. Run script to list all submissions:
       python utils/remove_submission.py
    
    2. Find the ID of the submission to remove
    
    3. Run with the ID to delete it:
       python utils/remove_submission.py <submission_id>
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import configure_warnings_logging

# Configure warnings to be captured in logs
configure_warnings_logging()


def list_submissions():
    """List all submissions to help identify which one to delete."""
    db_path = Path(__file__).parent.parent / 'data' / 'leaderboard.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, score, status, timestamp 
        FROM submissions 
        ORDER BY timestamp DESC
    ''')
    
    print("\nAll Submissions:")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Score':<10} {'Status':<12} {'Timestamp'}")
    print("-" * 80)
    
    for row in cursor.fetchall():
        score_str = f"{row[2]:.2f}" if row[2] is not None else "N/A"
        print(f"{row[0]:<5} {row[1]:<20} {score_str:<10} {row[3]:<12} {row[4]}")
    
    conn.close()


def remove_submission(submission_id):
    """Remove a submission by ID and update leaderboard.
    
    Args:
        submission_id: The ID of the submission to remove
    """
    db_path = Path(__file__).parent.parent / 'data' / 'leaderboard.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get submission details before deleting
    cursor.execute('SELECT username, score, status FROM submissions WHERE id = ?', (submission_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"\nError: No submission found with ID {submission_id}")
        conn.close()
        return
    
    username, score, status = result
    
    # Confirm deletion
    print(f"\nSubmission to delete:")
    print(f"  ID: {submission_id}")
    print(f"  Username: {username}")
    print(f"  Score: {score if score is not None else 'N/A'}")
    print(f"  Status: {status}")
    
    confirm = input("\nAre you sure you want to delete this submission? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled.")
        conn.close()
        return
    
    # Delete from submissions table
    cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
    
    # Update leaderboard - recalculate best score for this user
    cursor.execute('''
        SELECT MAX(score) as best_score, COUNT(*) as count, id
        FROM submissions 
        WHERE username = ? AND status = 'completed'
    ''', (username,))
    
    leaderboard_data = cursor.fetchone()
    
    if leaderboard_data[0] is not None:
        # User still has completed submissions - find the best submission ID
        cursor.execute('''
            SELECT id FROM submissions 
            WHERE username = ? AND score = ? AND status = 'completed'
            LIMIT 1
        ''', (username, leaderboard_data[0]))
        
        best_submission_id = cursor.fetchone()[0]
        
        # Use Python datetime to ensure consistent format
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        cursor.execute('''
            UPDATE leaderboard 
            SET best_score = ?, submission_count = ?, best_submission_id = ?, last_updated = ?
            WHERE username = ?
        ''', (leaderboard_data[0], leaderboard_data[1], best_submission_id, now, username))
        
        print(f"\nRemoved submission ID {submission_id}")
        print(f"Updated leaderboard for user '{username}':")
        print(f"  New best score: {leaderboard_data[0]:.2f}")
        print(f"  Remaining submissions: {leaderboard_data[1]}")
    else:
        # User has no more completed submissions, remove from leaderboard
        cursor.execute('DELETE FROM leaderboard WHERE username = ?', (username,))
        print(f"\nRemoved submission ID {submission_id}")
        print(f"Removed user '{username}' from leaderboard (no completed submissions remaining)")
    
    conn.commit()
    conn.close()
    
    print("\nDone!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            submission_id = int(sys.argv[1])
            remove_submission(submission_id)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid submission ID")
            print("Usage: python utils/remove_submission.py <submission_id>")
    else:
        list_submissions()
        print("\nTo delete a submission, run:")
        print("  python utils/remove_submission.py <submission_id>")
