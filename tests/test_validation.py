"""Unit tests for validation module."""

import unittest
import os
import tempfile
import json

from utils.validation import NotebookValidator, validate_submission


class TestNotebookValidator(unittest.TestCase):
    """Test cases for NotebookValidator class."""
    
    def setUp(self):
        """Set up test files before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = NotebookValidator(max_file_size_mb=1.0)
    
    def tearDown(self):
        """Clean up test files after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_valid_notebook(self, filename="test.ipynb"):
        """Helper to create a valid notebook file."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('Hello World')"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        return filepath
    
    def test_validate_valid_notebook(self):
        """Test validation of a valid notebook."""
        filepath = self.create_valid_notebook()
        is_valid, error = self.validator.validate_file(filepath)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        is_valid, error = self.validator.validate_file("/nonexistent/file.ipynb")
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)
    
    def test_validate_wrong_extension(self):
        """Test validation of file with wrong extension."""
        filepath = os.path.join(self.temp_dir, "test.txt")
        with open(filepath, 'w') as f:
            f.write("test")
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn(".ipynb", error)
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        filepath = os.path.join(self.temp_dir, "empty.ipynb")
        open(filepath, 'w').close()
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("empty", error.lower())
    
    def test_validate_file_too_large(self):
        """Test validation of file exceeding size limit."""
        filepath = os.path.join(self.temp_dir, "large.ipynb")
        
        # Create file larger than 1MB limit
        with open(filepath, 'w') as f:
            # Write more than 1MB of data
            f.write('x' * (2 * 1024 * 1024))
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("too large", error.lower())
    
    def test_validate_invalid_json(self):
        """Test validation of file with invalid JSON."""
        filepath = os.path.join(self.temp_dir, "invalid.ipynb")
        with open(filepath, 'w') as f:
            f.write("not valid json {")
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("JSON", error)
    
    def test_validate_missing_cells(self):
        """Test validation of notebook missing cells."""
        filepath = os.path.join(self.temp_dir, "nocells.ipynb")
        notebook_content = {
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("cells", error)
    
    def test_validate_missing_metadata(self):
        """Test validation of notebook missing metadata."""
        filepath = os.path.join(self.temp_dir, "nometa.ipynb")
        notebook_content = {
            "cells": [],
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("metadata", error)
    
    def test_validate_missing_nbformat(self):
        """Test validation of notebook missing nbformat."""
        filepath = os.path.join(self.temp_dir, "noformat.ipynb")
        notebook_content = {
            "cells": [],
            "metadata": {}
        }
        
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("nbformat", error)
    
    def test_validate_empty_cells(self):
        """Test validation of notebook with no cells."""
        filepath = os.path.join(self.temp_dir, "emptycells.ipynb")
        notebook_content = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("at least one cell", error)
    
    def test_validate_no_code_cells(self):
        """Test validation of notebook with no code cells."""
        filepath = os.path.join(self.temp_dir, "nocode.ipynb")
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Title"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        is_valid, error = self.validator.validate_file(filepath)
        self.assertFalse(is_valid)
        self.assertIn("code cell", error)
    
    def test_validate_username_valid(self):
        """Test validation of valid username."""
        is_valid, error = self.validator.validate_username("valid_user123")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_username_empty(self):
        """Test validation of empty username."""
        is_valid, error = self.validator.validate_username("")
        self.assertFalse(is_valid)
        self.assertIn("empty", error.lower())
    
    def test_validate_username_too_short(self):
        """Test validation of username too short."""
        is_valid, error = self.validator.validate_username("ab")
        self.assertFalse(is_valid)
        self.assertIn("at least 3", error)
    
    def test_validate_username_too_long(self):
        """Test validation of username too long."""
        is_valid, error = self.validator.validate_username("a" * 51)
        self.assertFalse(is_valid)
        self.assertIn("less than 50", error)
    
    def test_validate_username_invalid_chars(self):
        """Test validation of username with invalid characters."""
        is_valid, error = self.validator.validate_username("user@name")
        self.assertFalse(is_valid)
        self.assertIn("letters, numbers", error.lower())
    
    def test_validate_username_with_underscore(self):
        """Test validation of username with underscore."""
        is_valid, error = self.validator.validate_username("user_name")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_username_with_hyphen(self):
        """Test validation of username with hyphen."""
        is_valid, error = self.validator.validate_username("user-name")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_username_with_period(self):
        """Test validation of username with period."""
        is_valid, error = self.validator.validate_username("user.name")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_submission_success(self):
        """Test validate_submission convenience function with valid inputs."""
        filepath = self.create_valid_notebook()
        is_valid, error = validate_submission(filepath, "testuser", max_file_size_mb=1.0)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_submission_invalid_username(self):
        """Test validate_submission with invalid username."""
        filepath = self.create_valid_notebook()
        is_valid, error = validate_submission(filepath, "ab", max_file_size_mb=1.0)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_submission_invalid_file(self):
        """Test validate_submission with invalid file."""
        is_valid, error = validate_submission("/nonexistent.ipynb", "testuser")
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_notebook_structure_with_patterns(self):
        """Test validation of notebook structure with required patterns."""
        filepath = self.create_valid_notebook()
        
        # Should pass - contains "print"
        is_valid, error = self.validator.validate_notebook_structure(
            filepath,
            required_cell_patterns=["print"]
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_notebook_structure_missing_pattern(self):
        """Test validation fails when required pattern is missing."""
        filepath = self.create_valid_notebook()
        
        # Should fail - doesn't contain "import pandas"
        is_valid, error = self.validator.validate_notebook_structure(
            filepath,
            required_cell_patterns=["import pandas"]
        )
        self.assertFalse(is_valid)
        self.assertIn("not found", error)


if __name__ == '__main__':
    unittest.main()
