"""Unit tests for leaderboard module."""

import unittest
import os
import tempfile
import shutil
import pandas as pd

from src.database import Database
from src.leaderboard import LeaderboardManager


class TestLeaderboardManager(unittest.TestCase):
    """Test cases for LeaderboardManager class."""
    
    def setUp(self):
        """Set up test database and leaderboard manager before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_leaderboard.db")
        self.db = Database(self.db_path)
        self.lm = LeaderboardManager(self.db)
    
    def tearDown(self):
        """Clean up test database after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def add_test_submissions(self):
        """Helper to add test submissions to database."""
        users = [
            ("alice", 95.0),
            ("bob", 85.0),
            ("charlie", 90.0)
        ]
        
        for username, score in users:
            submission_id = self.db.add_submission(
                username=username,
                notebook_path=f"/path/{username}.ipynb",
                status="completed",
                score=score
            )
            self.db.update_leaderboard(username, submission_id, score)
    
    def test_get_leaderboard_df_empty(self):
        """Test getting empty leaderboard as DataFrame."""
        df = self.lm.get_leaderboard_df()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
        self.assertIn('Rank', df.columns)
        self.assertIn('Username', df.columns)
        self.assertIn('Best Score', df.columns)
    
    def test_get_leaderboard_df_with_data(self):
        """Test getting leaderboard DataFrame with data."""
        self.add_test_submissions()
        df = self.lm.get_leaderboard_df()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn('Rank', df.columns)
        self.assertIn('Username', df.columns)
        self.assertIn('Best Score', df.columns)
        self.assertIn('Submissions', df.columns)
        self.assertIn('Last Updated', df.columns)
    
    def test_get_leaderboard_df_ordering(self):
        """Test leaderboard DataFrame is ordered correctly."""
        self.add_test_submissions()
        df = self.lm.get_leaderboard_df()
        
        # Should be ordered by score descending
        self.assertEqual(df.iloc[0]['Username'], 'alice')  # 95.0
        self.assertEqual(df.iloc[1]['Username'], 'charlie')  # 90.0
        self.assertEqual(df.iloc[2]['Username'], 'bob')  # 85.0
        
        # Check ranks
        self.assertEqual(df.iloc[0]['Rank'], 1)
        self.assertEqual(df.iloc[1]['Rank'], 2)
        self.assertEqual(df.iloc[2]['Rank'], 3)
    
    def test_get_leaderboard_df_with_limit(self):
        """Test leaderboard DataFrame with limit."""
        self.add_test_submissions()
        df = self.lm.get_leaderboard_df(limit=2)
        
        self.assertEqual(len(df), 2)
    
    def test_get_user_stats_existing_user(self):
        """Test getting statistics for existing user."""
        self.add_test_submissions()
        
        # Add another submission for alice
        submission_id = self.db.add_submission(
            "alice", "/path/alice2.ipynb", "completed", score=92.0
        )
        self.db.update_leaderboard("alice", submission_id, 92.0)
        
        stats = self.lm.get_user_stats("alice")
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['username'], 'alice')
        self.assertEqual(stats['rank'], 1)
        self.assertEqual(stats['best_score'], 95.0)
        self.assertEqual(stats['total_submissions'], 2)
        self.assertEqual(stats['successful_submissions'], 2)
        self.assertEqual(stats['failed_submissions'], 0)
    
    def test_get_user_stats_nonexistent_user(self):
        """Test getting statistics for non-existent user."""
        stats = self.lm.get_user_stats("nonexistent")
        self.assertIsNone(stats)
    
    def test_get_user_stats_with_failed_submission(self):
        """Test user stats including failed submissions."""
        # Add successful submission
        submission_id = self.db.add_submission(
            "testuser", "/path/test.ipynb", "completed", score=80.0
        )
        self.db.update_leaderboard("testuser", submission_id, 80.0)
        
        # Add failed submission
        self.db.add_submission(
            "testuser", "/path/test2.ipynb", "failed", error_message="Error"
        )
        
        stats = self.lm.get_user_stats("testuser")
        
        self.assertEqual(stats['total_submissions'], 2)
        self.assertEqual(stats['successful_submissions'], 1)
        self.assertEqual(stats['failed_submissions'], 1)
    
    def test_get_submission_history_df_empty(self):
        """Test getting empty submission history."""
        df = self.lm.get_submission_history_df("testuser")
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
    
    def test_get_submission_history_df_with_data(self):
        """Test getting submission history with data."""
        # Add multiple submissions
        self.db.add_submission("testuser", "/path/test1.ipynb", "completed", score=80.0)
        self.db.add_submission("testuser", "/path/test2.ipynb", "completed", score=85.0)
        self.db.add_submission("testuser", "/path/test3.ipynb", "failed", error_message="Error")
        
        df = self.lm.get_submission_history_df("testuser")
        
        self.assertEqual(len(df), 3)
        self.assertIn('ID', df.columns)
        self.assertIn('Timestamp', df.columns)
        self.assertIn('Score', df.columns)
        self.assertIn('Status', df.columns)
        self.assertIn('Error', df.columns)
    
    def test_get_recent_submissions_df_empty(self):
        """Test getting empty recent submissions."""
        df = self.lm.get_recent_submissions_df()
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)
    
    def test_get_recent_submissions_df_with_data(self):
        """Test getting recent submissions with data."""
        self.add_test_submissions()
        df = self.lm.get_recent_submissions_df(limit=10)
        
        self.assertEqual(len(df), 3)
        self.assertIn('Username', df.columns)
        self.assertIn('Timestamp', df.columns)
        self.assertIn('Score', df.columns)
        self.assertIn('Status', df.columns)
    
    def test_get_recent_submissions_df_with_limit(self):
        """Test recent submissions with limit."""
        # Add many submissions
        for i in range(15):
            self.db.add_submission(f"user{i}", f"/path/test{i}.ipynb", "completed", score=float(i))
        
        df = self.lm.get_recent_submissions_df(limit=5)
        self.assertEqual(len(df), 5)
    
    def test_get_statistics_empty(self):
        """Test getting statistics with no data."""
        stats = self.lm.get_statistics()
        
        self.assertEqual(stats['total_submissions'], 0)
        self.assertEqual(stats['total_users'], 0)
        self.assertEqual(stats['successful_submissions'], 0)
        self.assertEqual(stats['failed_submissions'], 0)
        self.assertEqual(stats['average_score'], 0)
        self.assertEqual(stats['highest_score'], 0)
        self.assertEqual(stats['lowest_score'], 0)
    
    def test_get_statistics_with_data(self):
        """Test getting statistics with data."""
        self.add_test_submissions()
        
        # Add a failed submission
        self.db.add_submission("dave", "/path/dave.ipynb", "failed")
        
        stats = self.lm.get_statistics()
        
        self.assertEqual(stats['total_submissions'], 4)
        self.assertEqual(stats['total_users'], 3)
        self.assertEqual(stats['successful_submissions'], 3)
        self.assertEqual(stats['failed_submissions'], 1)
        self.assertEqual(stats['average_score'], 90.0)  # (95 + 85 + 90) / 3
        self.assertEqual(stats['highest_score'], 95.0)
        self.assertEqual(stats['lowest_score'], 85.0)
    
    def test_format_leaderboard_for_display_empty(self):
        """Test formatting empty leaderboard."""
        df = pd.DataFrame(columns=['Rank', 'Username', 'Best Score'])
        formatted_df = self.lm.format_leaderboard_for_display(df)
        
        self.assertTrue(formatted_df.empty)
    
    def test_format_leaderboard_for_display_with_medals(self):
        """Test formatting leaderboard adds medals to top 3."""
        self.add_test_submissions()
        df = self.lm.get_leaderboard_df()
        formatted_df = self.lm.format_leaderboard_for_display(df)
        
        # Check for medal emojis
        self.assertIn('🥇', formatted_df.iloc[0]['Username'])  # Rank 1
        self.assertIn('🥈', formatted_df.iloc[1]['Username'])  # Rank 2
        self.assertIn('🥉', formatted_df.iloc[2]['Username'])  # Rank 3
    
    def test_format_leaderboard_for_display_no_medal_for_rank_4(self):
        """Test that rank 4 and beyond don't get medals."""
        # Add a 4th user
        submission_id = self.db.add_submission(
            "dave", "/path/dave.ipynb", "completed", score=80.0
        )
        self.db.update_leaderboard("dave", submission_id, 80.0)
        
        self.add_test_submissions()
        df = self.lm.get_leaderboard_df()
        formatted_df = self.lm.format_leaderboard_for_display(df)
        
        # Rank 4 should not have medal emojis
        rank_4_username = formatted_df.iloc[3]['Username']
        self.assertNotIn('🥇', rank_4_username)
        self.assertNotIn('🥈', rank_4_username)
        self.assertNotIn('🥉', rank_4_username)
    
    def test_clear_all_data(self):
        """Test clearing all leaderboard data."""
        self.add_test_submissions()
        
        # Verify data exists
        df = self.lm.get_leaderboard_df()
        self.assertFalse(df.empty)
        
        # Clear data
        self.lm.clear_all_data()
        
        # Verify data is gone
        df = self.lm.get_leaderboard_df()
        self.assertTrue(df.empty)
        
        stats = self.lm.get_statistics()
        self.assertEqual(stats['total_submissions'], 0)
    
    def test_average_score_calculation(self):
        """Test that average score is calculated correctly."""
        # Add submissions with known scores
        self.db.add_submission("user1", "/path/test1.ipynb", "completed", score=80.0)
        submission_id1 = self.db.add_submission("user1", "/path/test2.ipynb", "completed", score=90.0)
        self.db.update_leaderboard("user1", submission_id1, 90.0)
        
        submission_id2 = self.db.add_submission("user1", "/path/test3.ipynb", "completed", score=70.0)
        self.db.update_leaderboard("user1", submission_id2, 70.0)
        
        stats = self.lm.get_user_stats("user1")
        
        # Average should be (80 + 90 + 70) / 3 = 80.0
        self.assertEqual(stats['average_score'], 80.0)


if __name__ == '__main__':
    unittest.main()
