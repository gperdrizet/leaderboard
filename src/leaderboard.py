"""Leaderboard management module."""

from typing import Dict, Optional #, List
# from datetime import datetime

import pandas as pd
from src.database import Database


class LeaderboardManager:
    """Manages leaderboard operations and rankings."""

    def __init__(self, db: Database):
        """Initialize leaderboard manager.
        
        Args:
            db: Database instance
        """

        self.db = db


    def get_leaderboard_df(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get leaderboard as a pandas DataFrame.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            DataFrame with leaderboard data
        """

        leaderboard_data = self.db.get_leaderboard(limit=limit)

        if not leaderboard_data:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'Rank', 'Username', 'Best Score', 'Submissions', 'Last Updated'
            ])

        # Convert to DataFrame
        df = pd.DataFrame(leaderboard_data)

        # Rename columns for display
        df = df.rename(columns={
            'rank': 'Rank',
            'username': 'Username',
            'best_score': 'Best Score',
            'submission_count': 'Submissions',
            'last_updated': 'Last Updated'
        })

        # Format the Last Updated column
        df['Last Updated'] = pd.to_datetime(df['Last Updated']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Round the score to 2 decimal places
        df['Best Score'] = df['Best Score'].round(2)

        # Select and order columns
        df = df[['Rank', 'Username', 'Best Score', 'Submissions', 'Last Updated']]

        return df


    def get_user_stats(self, username: str) -> Optional[Dict]:
        """Get statistics for a specific user.
        
        Args:
            username: Username to get stats for
            
        Returns:
            Dictionary with user statistics or None
        """

        result = self.db.get_user_rank(username)

        if not result:
            return None

        rank, user_data = result

        # Get submission history
        submissions = self.db.get_user_submissions(username)

        # Calculate stats
        total_submissions = len(submissions)
        successful_submissions = len([s for s in submissions if s['status'] == 'completed'])
        failed_submissions = len([s for s in submissions if s['status'] == 'failed'])

        scores = [s['score'] for s in submissions if s['score'] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            'username': username,
            'rank': rank,
            'best_score': user_data['best_score'],
            'total_submissions': total_submissions,
            'successful_submissions': successful_submissions,
            'failed_submissions': failed_submissions,
            'average_score': round(avg_score, 2),
            'last_updated': user_data['last_updated']
        }

    def get_submission_history_df(self, username: str) -> pd.DataFrame:
        """Get submission history for a user as DataFrame.
        
        Args:
            username: Username to get history for
            
        Returns:
            DataFrame with submission history
        """

        submissions = self.db.get_user_submissions(username)

        if not submissions:
            return pd.DataFrame(columns=[
                'ID', 'Timestamp', 'Score', 'Status', 'Error'
            ])

        df = pd.DataFrame(submissions)

        # Select and rename columns
        df = df[['id', 'timestamp', 'score', 'status', 'error_message']]
        df = df.rename(columns={
            'id': 'ID',
            'timestamp': 'Timestamp',
            'score': 'Score',
            'status': 'Status',
            'error_message': 'Error'
        })

        # Format timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Round score
        df['Score'] = df['Score'].round(2)

        # Truncate error messages
        df['Error'] = df['Error'].apply(
            lambda x: (x[:100] + '...') if x and len(str(x)) > 100 else x
        )

        return df


    def get_recent_submissions_df(self, limit: int = 10) -> pd.DataFrame:
        """Get recent submissions across all users.
        
        Args:
            limit: Maximum number of submissions to return
            
        Returns:
            DataFrame with recent submissions
        """

        submissions = self.db.get_all_submissions(limit=limit)

        if not submissions:
            return pd.DataFrame(columns=[
                'Username', 'Timestamp', 'Score', 'Status'
            ])

        df = pd.DataFrame(submissions)

        # Select and rename columns
        df = df[['username', 'timestamp', 'score', 'status']]
        df = df.rename(columns={
            'username': 'Username',
            'timestamp': 'Timestamp',
            'score': 'Score',
            'status': 'Status'
        })

        # Format timestamp
        df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Round score
        df['Score'] = df['Score'].round(2)

        return df


    def get_statistics(self) -> Dict:
        """Get overall leaderboard statistics.
        
        Returns:
            Dictionary with overall statistics
        """

        all_submissions = self.db.get_all_submissions()
        leaderboard = self.db.get_leaderboard()

        total_submissions = len(all_submissions)
        total_users = len(leaderboard)

        successful = len([s for s in all_submissions if s['status'] == 'completed'])
        failed = len([s for s in all_submissions if s['status'] == 'failed'])

        scores = [s['score'] for s in all_submissions if s['score'] is not None]

        stats = {
            'total_submissions': total_submissions,
            'total_users': total_users,
            'successful_submissions': successful,
            'failed_submissions': failed,
            'average_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'highest_score': round(max(scores), 2) if scores else 0,
            'lowest_score': round(min(scores), 2) if scores else 0
        }

        return stats


    def format_leaderboard_for_display(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format leaderboard DataFrame for nice display.
        
        Args:
            df: Leaderboard DataFrame
            
        Returns:
            Formatted DataFrame
        """

        if df.empty:
            return df

        # Add medal emojis for top 3
        def add_medal(row):
            if row['Rank'] == 1:
                return f"🥇 {row['Username']}"
            elif row['Rank'] == 2:
                return f"🥈 {row['Username']}"
            elif row['Rank'] == 3:
                return f"🥉 {row['Username']}"
            else:
                return row['Username']

        df['Username'] = df.apply(add_medal, axis=1)

        return df

    def clear_all_data(self):
        """Clear all leaderboard data. Use with caution!"""

        self.db.clear_leaderboard()
