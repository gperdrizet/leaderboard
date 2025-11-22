"""Unit tests for logger module."""

import unittest
import os
import tempfile
import shutil
import warnings
import logging
from pathlib import Path

from src.logger import get_logger, configure_warnings_logging


class TestLogger(unittest.TestCase):
    """Test cases for logging configuration."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Clear any existing handlers from the warnings logger
        warnings_logger = logging.getLogger('py.warnings')
        warnings_logger.handlers.clear()
        
    def tearDown(self):
        """Clean up test environment after each test."""
        # Return to original directory
        os.chdir(self.original_cwd)
        
        # Remove temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_logger_creation(self):
        """Test logger is created with correct handlers."""
        logger = get_logger("test_module")
        
        # Check logger has correct handlers
        self.assertEqual(len(logger.handlers), 3)  # file, error, console
        
        # Check log files are created
        self.assertTrue(os.path.exists("logs/leaderboard.log"))
        self.assertTrue(os.path.exists("logs/errors.log"))
    
    def test_warnings_capture(self):
        """Test that warnings are captured in log files."""
        # Configure warnings logging
        configure_warnings_logging()
        
        # Trigger a warning
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.warn("Test warning", DeprecationWarning)
        
        # Check that log file exists and contains the warning
        log_path = Path("logs/leaderboard.log")
        self.assertTrue(log_path.exists())
        
        # Read log file
        with open(log_path, 'r') as f:
            log_contents = f.read()
        
        # Check warning is in the log
        self.assertIn("Test warning", log_contents)
        self.assertIn("py.warnings", log_contents)
    
    def test_logger_levels(self):
        """Test that different log levels are handled correctly."""
        logger = get_logger("test_levels")
        
        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Check that all messages are in the main log
        with open("logs/leaderboard.log", 'r') as f:
            log_contents = f.read()
        
        self.assertIn("Debug message", log_contents)
        self.assertIn("Info message", log_contents)
        self.assertIn("Warning message", log_contents)
        self.assertIn("Error message", log_contents)
        
        # Check that only error is in error log
        with open("logs/errors.log", 'r') as f:
            error_log = f.read()
        
        self.assertNotIn("Debug message", error_log)
        self.assertNotIn("Info message", error_log)
        self.assertNotIn("Warning message", error_log)
        self.assertIn("Error message", error_log)


if __name__ == '__main__':
    unittest.main()
