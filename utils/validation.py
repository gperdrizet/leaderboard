"""Validation utilities for notebook submissions."""

import os
import json
from typing import Tuple, Optional


class NotebookValidator:
    """Validates Jupyter notebook submissions."""
    
    def __init__(self, max_file_size_mb: float = 10.0):
        """Initialize validator.
        
        Args:
            max_file_size_mb: Maximum file size in megabytes
        """
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate a notebook file.
        
        Args:
            file_path: Path to the notebook file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file extension
        if not file_path.endswith('.ipynb'):
            return False, "File must be a Jupyter notebook (.ipynb)"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File too large: {actual_mb:.2f}MB (max: {max_mb:.2f}MB)"
        
        # Check if file is empty
        if file_size == 0:
            return False, "File is empty"
        
        # Validate notebook format
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_content = json.load(f)
            
            # Check required notebook fields
            if 'cells' not in notebook_content:
                return False, "Invalid notebook format: missing 'cells'"
            
            if 'metadata' not in notebook_content:
                return False, "Invalid notebook format: missing 'metadata'"
            
            if 'nbformat' not in notebook_content:
                return False, "Invalid notebook format: missing 'nbformat'"
            
            # Check if notebook has at least one cell
            if len(notebook_content['cells']) == 0:
                return False, "Notebook must contain at least one cell"
            
            # Check if notebook has at least one code cell
            code_cells = [cell for cell in notebook_content['cells'] if cell.get('cell_type') == 'code']
            if len(code_cells) == 0:
                return False, "Notebook must contain at least one code cell"
            
            return True, None
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {str(e)}"
        except UnicodeDecodeError:
            return False, "File encoding error: file must be UTF-8"
        except Exception as e:
            return False, f"Error validating notebook: {str(e)}"
    
    def validate_username(self, username: str) -> Tuple[bool, Optional[str]]:
        """Validate username.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not all(c.isalnum() or c in ['_', '-', '.'] for c in username):
            return False, "Username can only contain letters, numbers, underscores, hyphens, and periods"
        
        return True, None
    
    def validate_notebook_structure(
        self,
        file_path: str,
        required_cell_patterns: Optional[list] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate notebook structure against specific requirements.
        
        Args:
            file_path: Path to the notebook file
            required_cell_patterns: Optional list of patterns that cells must contain
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_content = json.load(f)
            
            cells = notebook_content.get('cells', [])
            
            # If specific patterns are required, check for them
            if required_cell_patterns:
                for pattern in required_cell_patterns:
                    found = False
                    for cell in cells:
                        if cell.get('cell_type') == 'code':
                            source = ''.join(cell.get('source', []))
                            if pattern in source:
                                found = True
                                break
                    
                    if not found:
                        return False, f"Required code pattern not found: {pattern}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating structure: {str(e)}"


def validate_submission(
    file_path: str,
    username: str,
    max_file_size_mb: float = 10.0
) -> Tuple[bool, Optional[str]]:
    """Convenience function to validate a complete submission.
    
    Args:
        file_path: Path to the notebook file
        username: Username submitting
        max_file_size_mb: Maximum file size in megabytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = NotebookValidator(max_file_size_mb=max_file_size_mb)
    
    # Validate username
    is_valid, error = validator.validate_username(username)
    if not is_valid:
        return False, error
    
    # Validate file
    is_valid, error = validator.validate_file(file_path)
    if not is_valid:
        return False, error
    
    return True, None
