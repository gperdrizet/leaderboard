"""Database handler for leaderboard application using SQLite."""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from .logger import get_logger

logger = get_logger(__name__)


class Database:
    """Manages SQLite database operations for submissions and leaderboard."""
    
    def __init__(self, db_path: str = "data/leaderboard.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        logger.info(f"Initializing Database with path: {db_path}")
        self.db_path = db_path
        self.hf_token = os.environ.get("HF_TOKEN")
        self.hf_db_repo = os.environ.get("HF_DB_REPO")
        self._hub_enabled = bool(self.hf_token and self.hf_db_repo)
        if self._hub_enabled:
            logger.info(f"HuggingFace Hub persistence enabled: {self.hf_db_repo}")
        else:
            logger.info("HuggingFace Hub persistence disabled (HF_TOKEN/HF_DB_REPO not set)")
        self._ensure_db_directory()
        self._pull_from_hub()
        self._create_tables()
        logger.info("Database initialized successfully")
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

    def _pull_from_hub(self):
        """Download database from HuggingFace Hub dataset repo on startup.

        Requires HF_TOKEN and HF_DB_REPO environment variables to be set.
        Silently skips if Hub is not configured or the file doesn't exist yet.
        """
        if not self._hub_enabled:
            return
        try:
            from huggingface_hub import hf_hub_download
            logger.info(f"Pulling database from Hub: {self.hf_db_repo}")
            cached_path = hf_hub_download(
                repo_id=self.hf_db_repo,
                filename="leaderboard.db",
                repo_type="dataset",
                token=self.hf_token,
                force_download=True,
            )
            shutil.copy2(cached_path, self.db_path)
            logger.info("Database pulled from Hub successfully")
        except Exception as e:
            # File may not exist yet on the Hub (fresh deployment) — that's fine.
            logger.info(f"Could not pull database from Hub (may be a fresh deployment): {e}")

    def _push_to_hub(self):
        """Upload the local database file to HuggingFace Hub dataset repo.

        Called automatically after every write operation when Hub is configured.
        Errors are logged but never raised so that writes always succeed locally.
        """
        if not self._hub_enabled:
            return
        try:
            from huggingface_hub import upload_file
            logger.info(f"Pushing database to Hub: {self.hf_db_repo}")
            upload_file(
                path_or_fileobj=self.db_path,
                path_in_repo="leaderboard.db",
                repo_id=self.hf_db_repo,
                repo_type="dataset",
                token=self.hf_token,
                commit_message="Update leaderboard database",
            )
            logger.info("Database pushed to Hub successfully")
        except Exception as e:
            logger.error(f"Failed to push database to Hub: {e}", exc_info=True)
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed, rolling back: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Submissions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS submissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        notebook_path TEXT NOT NULL,
                        score REAL,
                        status TEXT NOT NULL,
                        error_message TEXT
                    )
                """)
                
                # Leaderboard table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        username TEXT PRIMARY KEY,
                        best_score REAL NOT NULL,
                        best_submission_id INTEGER NOT NULL,
                        last_updated DATETIME NOT NULL,
                        submission_count INTEGER NOT NULL,
                        FOREIGN KEY (best_submission_id) REFERENCES submissions(id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_submissions_username 
                    ON submissions(username)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_submissions_timestamp 
                    ON submissions(timestamp)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_leaderboard_score 
                    ON leaderboard(best_score DESC)
                """)
                
                logger.debug("Database tables and indexes created/verified")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            raise
    
    def add_submission(
        self,
        username: str,
        notebook_path: str,
        status: str = "pending",
        score: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> int:
        """Add a new submission to the database.
        
        Args:
            username: Name of the user submitting
            notebook_path: Path to the submitted notebook
            status: Submission status (pending, running, completed, failed)
            score: Score if available
            error_message: Error message if failed
            
        Returns:
            Submission ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (username, timestamp, notebook_path, score, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), notebook_path, score, status, error_message))
            submission_id = cursor.lastrowid
            logger.info(f"Added submission ID {submission_id} for user '{username}' with status '{status}'")
        self._push_to_hub()
        return submission_id
    
    def update_submission(
        self,
        submission_id: int,
        status: str,
        score: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Update an existing submission.
        
        Args:
            submission_id: ID of submission to update
            status: New status
            score: New score if available
            error_message: Error message if failed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions
                SET status = ?, score = ?, error_message = ?
                WHERE id = ?
            """, (status, score, error_message, submission_id))
            logger.info(f"Updated submission ID {submission_id}: status='{status}', score={score}")
            if error_message:
                logger.warning(f"Submission ID {submission_id} error: {error_message}")
        self._push_to_hub()
    
    def get_submission(self, submission_id: int) -> Optional[Dict]:
        """Get a submission by ID.
        
        Args:
            submission_id: ID of submission to retrieve
            
        Returns:
            Submission data as dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_submissions(self, username: str) -> List[Dict]:
        """Get all submissions for a user.
        
        Args:
            username: Username to get submissions for
            
        Returns:
            List of submission dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE username = ? 
                ORDER BY timestamp DESC
            """, (username,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_leaderboard(self, username: str, submission_id: int, score: float):
        """Update leaderboard with new submission.
        
        Args:
            username: Username to update
            submission_id: ID of the submission
            score: Score achieved
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists in leaderboard
            cursor.execute("SELECT best_score, submission_count FROM leaderboard WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                best_score, submission_count = row['best_score'], row['submission_count']
                
                # Update if new score is better (higher is better - adjust if lower is better)
                if score > best_score:
                    cursor.execute("""
                        UPDATE leaderboard
                        SET best_score = ?, best_submission_id = ?, last_updated = ?, submission_count = ?
                        WHERE username = ?
                    """, (score, submission_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), submission_count + 1, username))
                    logger.info(f"Updated leaderboard for '{username}': new best score {score} (was {best_score})")
                else:
                    # Just increment submission count
                    cursor.execute("""
                        UPDATE leaderboard
                        SET last_updated = ?, submission_count = ?
                        WHERE username = ?
                    """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), submission_count + 1, username))
                    logger.info(f"Updated submission count for '{username}': {submission_count + 1} submissions")
            else:
                # New user - insert into leaderboard
                cursor.execute("""
                    INSERT INTO leaderboard (username, best_score, best_submission_id, last_updated, submission_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, score, submission_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 1))
                logger.info(f"Added '{username}' to leaderboard with score {score}")
        self._push_to_hub()
    
    def get_leaderboard(self, limit: Optional[int] = None) -> List[Dict]:
        """Get leaderboard rankings.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of leaderboard entries sorted by score
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY best_score DESC) as rank,
                    username,
                    best_score,
                    submission_count,
                    last_updated
                FROM leaderboard
                ORDER BY best_score DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_rank(self, username: str) -> Optional[Tuple[int, Dict]]:
        """Get rank and details for a specific user.
        
        Args:
            username: Username to get rank for
            
        Returns:
            Tuple of (rank, user_data) or None if user not found
        """
        leaderboard = self.get_leaderboard()
        for entry in leaderboard:
            if entry['username'] == username:
                return entry['rank'], entry
        return None
    
    def clear_leaderboard(self):
        """Clear all leaderboard and submission data. Use with caution!"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leaderboard")
            cursor.execute("DELETE FROM submissions")
            logger.warning("Cleared all leaderboard and submission data")
        self._push_to_hub()
    
    def remove_submission(self, submission_id: int) -> bool:
        """Remove a submission and recalculate the affected user's leaderboard entry.

        Args:
            submission_id: ID of the submission to remove

        Returns:
            True if the submission was found and removed, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Fetch the submission so we know the owner
            cursor.execute("SELECT username FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"remove_submission: submission ID {submission_id} not found")
                return False

            username = row["username"]
            cursor.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))

            # Recalculate the leaderboard entry for this user
            cursor.execute("""
                SELECT MAX(score) AS best_score, COUNT(*) AS count
                FROM submissions
                WHERE username = ? AND status = 'completed'
            """, (username,))
            result = cursor.fetchone()

            if result["best_score"] is not None:
                cursor.execute("""
                    SELECT id FROM submissions
                    WHERE username = ? AND score = ? AND status = 'completed'
                    LIMIT 1
                """, (username, result["best_score"]))
                best_id = cursor.fetchone()["id"]
                cursor.execute("""
                    UPDATE leaderboard
                    SET best_score = ?, submission_count = ?, best_submission_id = ?, last_updated = ?
                    WHERE username = ?
                """, (result["best_score"], result["count"], best_id,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), username))
                logger.info(
                    f"Removed submission ID {submission_id}; updated leaderboard for '{username}'"
                )
            else:
                cursor.execute("DELETE FROM leaderboard WHERE username = ?", (username,))
                logger.info(
                    f"Removed submission ID {submission_id}; removed '{username}' from leaderboard"
                )

        self._push_to_hub()
        return True

    def get_all_submissions(self, limit: Optional[int] = None) -> List[Dict]:
        """Get all submissions across all users.
        
        Args:
            limit: Maximum number of submissions to return
            
        Returns:
            List of submission dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM submissions ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
