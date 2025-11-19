"""Unit tests for database module."""

import unittest
import os
import tempfile
import shutil
from datetime import datetime

from src.database import Database


class TestDatabase(unittest.TestCase):
    """Test cases for Database class."""
    
    def setUp(self):
        """Set up test database before each test."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_leaderboard.db")
        self.db = Database(self.db_path)
    
    def tearDown(self):
        """Clean up test database after each test."""
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_database_creation(self):
        """Test database and tables are created."""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_add_submission(self):
        """Test adding a submission."""
        submission_id = self.db.add_submission(
            username="testuser",
            notebook_path="/path/to/notebook.ipynb",
            status="pending"
        )
        self.assertIsInstance(submission_id, int)
        self.assertGreater(submission_id, 0)
    
    def test_get_submission(self):
        """Test retrieving a submission."""
        # Add a submission
        submission_id = self.db.add_submission(
            username="testuser",
            notebook_path="/path/to/notebook.ipynb",
            status="pending"
        )
        
        # Retrieve it
        submission = self.db.get_submission(submission_id)
        self.assertIsNotNone(submission)
        self.assertEqual(submission['username'], "testuser")
        self.assertEqual(submission['status'], "pending")
    
    def test_update_submission(self):
        """Test updating a submission."""
        # Add a submission
        submission_id = self.db.add_submission(
            username="testuser",
            notebook_path="/path/to/notebook.ipynb",
            status="pending"
        )
        
        # Update it
        self.db.update_submission(
            submission_id,
            status="completed",
            score=85.5
        )
        
        # Verify update
        submission = self.db.get_submission(submission_id)
        self.assertEqual(submission['status'], "completed")
        self.assertEqual(submission['score'], 85.5)
    
    def test_get_user_submissions(self):
        """Test retrieving all submissions for a user."""
        # Add multiple submissions
        self.db.add_submission("user1", "/path/notebook1.ipynb", "completed", score=80.0)
        self.db.add_submission("user1", "/path/notebook2.ipynb", "completed", score=90.0)
        self.db.add_submission("user2", "/path/notebook3.ipynb", "completed", score=75.0)
        
        # Get user1's submissions
        submissions = self.db.get_user_submissions("user1")
        self.assertEqual(len(submissions), 2)
        self.assertTrue(all(s['username'] == "user1" for s in submissions))
    
    def test_update_leaderboard_new_user(self):
        """Test adding a new user to leaderboard."""
        # Add submission
        submission_id = self.db.add_submission(
            "newuser", "/path/notebook.ipynb", "completed", score=85.0
        )
        
        # Update leaderboard
        self.db.update_leaderboard("newuser", submission_id, 85.0)
        
        # Verify leaderboard entry
        leaderboard = self.db.get_leaderboard()
        self.assertEqual(len(leaderboard), 1)
        self.assertEqual(leaderboard[0]['username'], "newuser")
        self.assertEqual(leaderboard[0]['best_score'], 85.0)
        self.assertEqual(leaderboard[0]['submission_count'], 1)
    
    def test_update_leaderboard_better_score(self):
        """Test updating leaderboard with better score."""
        # Add first submission
        submission_id1 = self.db.add_submission(
            "user1", "/path/notebook1.ipynb", "completed", score=80.0
        )
        self.db.update_leaderboard("user1", submission_id1, 80.0)
        
        # Add second submission with better score
        submission_id2 = self.db.add_submission(
            "user1", "/path/notebook2.ipynb", "completed", score=90.0
        )
        self.db.update_leaderboard("user1", submission_id2, 90.0)
        
        # Verify best score updated
        leaderboard = self.db.get_leaderboard()
        self.assertEqual(len(leaderboard), 1)
        self.assertEqual(leaderboard[0]['best_score'], 90.0)
        self.assertEqual(leaderboard[0]['submission_count'], 2)
    
    def test_update_leaderboard_worse_score(self):
        """Test updating leaderboard with worse score doesn't change best."""
        # Add first submission
        submission_id1 = self.db.add_submission(
            "user1", "/path/notebook1.ipynb", "completed", score=90.0
        )
        self.db.update_leaderboard("user1", submission_id1, 90.0)
        
        # Add second submission with worse score
        submission_id2 = self.db.add_submission(
            "user1", "/path/notebook2.ipynb", "completed", score=80.0
        )
        self.db.update_leaderboard("user1", submission_id2, 80.0)
        
        # Verify best score unchanged
        leaderboard = self.db.get_leaderboard()
        self.assertEqual(len(leaderboard), 1)
        self.assertEqual(leaderboard[0]['best_score'], 90.0)
        self.assertEqual(leaderboard[0]['submission_count'], 2)
    
    def test_get_leaderboard_ordering(self):
        """Test leaderboard is ordered by score descending."""
        # Add submissions for multiple users
        for i, score in enumerate([75.0, 90.0, 85.0]):
            submission_id = self.db.add_submission(
                f"user{i}", f"/path/notebook{i}.ipynb", "completed", score=score
            )
            self.db.update_leaderboard(f"user{i}", submission_id, score)
        
        # Get leaderboard
        leaderboard = self.db.get_leaderboard()
        
        # Verify ordering (should be 90, 85, 75)
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]['best_score'], 90.0)
        self.assertEqual(leaderboard[1]['best_score'], 85.0)
        self.assertEqual(leaderboard[2]['best_score'], 75.0)
        
        # Verify ranks
        self.assertEqual(leaderboard[0]['rank'], 1)
        self.assertEqual(leaderboard[1]['rank'], 2)
        self.assertEqual(leaderboard[2]['rank'], 3)
    
    def test_get_leaderboard_with_limit(self):
        """Test leaderboard limit parameter."""
        # Add multiple users
        for i in range(10):
            submission_id = self.db.add_submission(
                f"user{i}", f"/path/notebook{i}.ipynb", "completed", score=float(i)
            )
            self.db.update_leaderboard(f"user{i}", submission_id, float(i))
        
        # Get top 5
        leaderboard = self.db.get_leaderboard(limit=5)
        self.assertEqual(len(leaderboard), 5)
    
    def test_get_user_rank(self):
        """Test getting user rank."""
        # Add users
        for i, score in enumerate([75.0, 90.0, 85.0]):
            submission_id = self.db.add_submission(
                f"user{i}", f"/path/notebook{i}.ipynb", "completed", score=score
            )
            self.db.update_leaderboard(f"user{i}", submission_id, score)
        
        # Get user1's rank (should be 1 with score 90)
        result = self.db.get_user_rank("user1")
        self.assertIsNotNone(result)
        rank, user_data = result
        self.assertEqual(rank, 1)
        self.assertEqual(user_data['best_score'], 90.0)
    
    def test_get_user_rank_nonexistent(self):
        """Test getting rank for non-existent user."""
        result = self.db.get_user_rank("nonexistent")
        self.assertIsNone(result)
    
    def test_get_all_submissions(self):
        """Test getting all submissions across users."""
        # Add submissions
        self.db.add_submission("user1", "/path/notebook1.ipynb", "completed", score=80.0)
        self.db.add_submission("user2", "/path/notebook2.ipynb", "completed", score=90.0)
        self.db.add_submission("user1", "/path/notebook3.ipynb", "failed")
        
        # Get all
        submissions = self.db.get_all_submissions()
        self.assertEqual(len(submissions), 3)
    
    def test_get_all_submissions_with_limit(self):
        """Test getting all submissions with limit."""
        # Add multiple submissions
        for i in range(10):
            self.db.add_submission(f"user{i}", f"/path/notebook{i}.ipynb", "completed")
        
        # Get limited
        submissions = self.db.get_all_submissions(limit=5)
        self.assertEqual(len(submissions), 5)
    
    def test_clear_leaderboard(self):
        """Test clearing all data."""
        # Add some data
        submission_id = self.db.add_submission(
            "user1", "/path/notebook.ipynb", "completed", score=80.0
        )
        self.db.update_leaderboard("user1", submission_id, 80.0)
        
        # Clear
        self.db.clear_leaderboard()
        
        # Verify empty
        leaderboard = self.db.get_leaderboard()
        submissions = self.db.get_all_submissions()
        self.assertEqual(len(leaderboard), 0)
        self.assertEqual(len(submissions), 0)
    
    def test_submission_with_error_message(self):
        """Test adding submission with error message."""
        submission_id = self.db.add_submission(
            username="testuser",
            notebook_path="/path/to/notebook.ipynb",
            status="failed",
            error_message="Execution timeout"
        )
        
        submission = self.db.get_submission(submission_id)
        self.assertEqual(submission['status'], "failed")
        self.assertEqual(submission['error_message'], "Execution timeout")


if __name__ == '__main__':
    unittest.main()
