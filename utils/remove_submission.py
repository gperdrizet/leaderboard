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
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.logger import configure_warnings_logging

# Configure warnings to be captured in logs
configure_warnings_logging()


def list_submissions(db: Database):
    """List all submissions to help identify which one to delete."""
    submissions = db.get_all_submissions()

    print("\nAll Submissions:")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Score':<10} {'Status':<12} {'Timestamp'}")
    print("-" * 80)

    for row in submissions:
        score_str = f"{row['score']:.2f}" if row['score'] is not None else "N/A"
        print(f"{row['id']:<5} {row['username']:<20} {score_str:<10} {row['status']:<12} {row['timestamp']}")


def remove_submission(db: Database, submission_id: int):
    """Remove a submission by ID and update the leaderboard."""
    submission = db.get_submission(submission_id)

    if not submission:
        print(f"\nError: No submission found with ID {submission_id}")
        return

    print(f"\nSubmission to delete:")
    print(f"  ID: {submission_id}")
    print(f"  Username: {submission['username']}")
    print(f"  Score: {submission['score'] if submission['score'] is not None else 'N/A'}")
    print(f"  Status: {submission['status']}")

    confirm = input("\nAre you sure you want to delete this submission? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled.")
        return

    removed = db.remove_submission(submission_id)
    if removed:
        print(f"\nRemoved submission ID {submission_id}")
        print("\nDone!")
    else:
        print(f"\nError: Submission ID {submission_id} could not be removed.")


if __name__ == '__main__':
    db = Database('data/leaderboard.db')

    if len(sys.argv) > 1:
        try:
            submission_id = int(sys.argv[1])
            remove_submission(db, submission_id)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid submission ID")
            print("Usage: python utils/remove_submission.py <submission_id>")
    else:
        list_submissions(db)
        print("\nTo delete a submission, run:")
        print("  python utils/remove_submission.py <submission_id>")
