#!/usr/bin/env python3
"""Reprocess all notebooks in the submissions directory.

This script will execute and score all notebooks found in data/submissions/
and add them to the database if they're not already there.

Usage:
    python utils/reprocess_submissions.py
"""

import os
import sys
from pathlib import Path
import re

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.notebook_runner import NotebookRunner
from src.scorer import Scorer
from src.leaderboard import LeaderboardManager


def extract_username_from_filename(filename):
    """Extract username from submission filename.
    
    Args:
        filename: Notebook filename (e.g., 'username_20251120_123456.ipynb')
        
    Returns:
        Username or None if pattern doesn't match
    """
    # Format: username_timestamp.ipynb
    match = re.match(r'^(.+?)_\d{8}_\d{6}\.ipynb$', filename)
    if match:
        return match.group(1)
    return None


def reprocess_all_submissions():
    """Reprocess all notebooks in the submissions directory."""
    
    # Initialize components
    db = Database('data/leaderboard.db')
    runner = NotebookRunner('data/outputs', timeout_seconds=300)
    scorer = Scorer(ground_truth_path='data/california_housing.csv')
    leaderboard = LeaderboardManager(db)
    
    submissions_dir = Path('data/submissions')
    
    if not submissions_dir.exists():
        print("Error: Submissions directory does not exist!")
        return
    
    # Get all notebook files
    notebooks = list(submissions_dir.glob('*.ipynb'))
    
    if not notebooks:
        print("No notebooks found in submissions directory")
        return
    
    print(f"Found {len(notebooks)} notebooks to process\n")
    
    processed = 0
    skipped = 0
    errors = 0
    
    for notebook_path in sorted(notebooks):
        filename = notebook_path.name
        username = extract_username_from_filename(filename)
        
        if not username:
            print(f"❌ Could not extract username from: {filename}")
            errors += 1
            continue
        
        print(f"Processing: {filename} (user: {username})")
        
        try:
            # Check if this submission already exists in database
            existing = db.get_user_submissions(username)
            already_exists = any(sub['notebook_path'] == str(notebook_path) for sub in existing)
            
            if already_exists:
                print(f"  ⏭️  Already in database, skipping")
                skipped += 1
                continue
            
            # Execute the notebook
            success, output_path, error_message = runner.execute_notebook(str(notebook_path))
            
            if success and output_path and os.path.exists(output_path):
                # Score the output
                score = scorer.score_notebook(output_path)
                
                # Add to database
                submission_id = db.add_submission(
                    username=username,
                    notebook_path=str(notebook_path),
                    score=score,
                    status='completed'
                )
                
                # Update leaderboard
                db.update_leaderboard(username, submission_id, score)
                
                print(f"  ✅ Score: {score:.2f}, Added to database (ID: {submission_id})")
                processed += 1
            else:
                print(f"  ❌ Execution failed: {error_message}")
                db.add_submission(
                    username=username,
                    notebook_path=str(notebook_path),
                    score=0.0,
                    status='failed',
                    error_message=error_message or 'Notebook execution failed'
                )
                errors += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            try:
                db.add_submission(
                    username=username,
                    notebook_path=str(notebook_path),
                    score=0.0,
                    status='failed',
                    error_message=str(e)
                )
            except:
                pass
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Reprocessing complete!")
    print(f"  Successfully processed: {processed}")
    print(f"  Skipped (already in DB): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total notebooks: {len(notebooks)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    print("This will reprocess all notebooks in data/submissions/")
    print("Notebooks already in the database will be skipped.")
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        reprocess_all_submissions()
    else:
        print("Cancelled")
