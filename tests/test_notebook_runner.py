"""Unit tests for notebook_runner module."""

import unittest
import os
import tempfile
import json
import shutil
from unittest.mock import patch, MagicMock

from src.notebook_runner import NotebookRunner, TimeoutException


class TestNotebookRunner(unittest.TestCase):
    """Test cases for NotebookRunner class."""
    
    def setUp(self):
        """Set up test directories before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.test_dir, "outputs")
        self.runner = NotebookRunner(output_dir=self.output_dir, timeout_seconds=10)
    
    def tearDown(self):
        """Clean up test directories after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_simple_notebook(self, filename="test.ipynb"):
        """Helper to create a simple valid notebook."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('Hello World')"]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["x = 42\n", "print(x)"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        return filepath
    
    def test_runner_initialization(self):
        """Test notebook runner initialization."""
        self.assertEqual(self.runner.output_dir, self.output_dir)
        self.assertEqual(self.runner.timeout_seconds, 10)
        self.assertTrue(os.path.exists(self.output_dir))
    
    def test_output_dir_created(self):
        """Test that output directory is created if it doesn't exist."""
        new_output_dir = os.path.join(self.test_dir, "new_outputs")
        runner = NotebookRunner(output_dir=new_output_dir)
        self.assertTrue(os.path.exists(new_output_dir))
    
    @patch('src.notebook_runner.pm.execute_notebook')
    def test_execute_notebook_success(self, mock_execute):
        """Test successful notebook execution."""
        mock_execute.return_value = None
        
        notebook_path = self.create_simple_notebook()
        success, output_path, error = self.runner.execute_notebook(notebook_path)
        
        self.assertTrue(success)
        self.assertIsNotNone(output_path)
        self.assertIsNone(error)
        self.assertTrue(output_path.endswith("_executed.ipynb"))
        
        # Verify execute_notebook was called
        mock_execute.assert_called_once()
    
    @patch('src.notebook_runner.pm.execute_notebook')
    def test_execute_notebook_with_parameters(self, mock_execute):
        """Test notebook execution with parameters."""
        mock_execute.return_value = None
        
        notebook_path = self.create_simple_notebook()
        parameters = {"param1": "value1", "param2": 42}
        
        success, output_path, error = self.runner.execute_notebook(
            notebook_path,
            parameters=parameters
        )
        
        self.assertTrue(success)
        
        # Verify parameters were passed
        call_args = mock_execute.call_args
        self.assertEqual(call_args[1]['parameters'], parameters)
    
    @patch('src.notebook_runner.pm.execute_notebook')
    def test_execute_notebook_execution_error(self, mock_execute):
        """Test notebook execution with PapermillExecutionError."""
        import papermill as pm
        mock_execute.side_effect = pm.PapermillExecutionError("Cell error", None, None, None)
        
        notebook_path = self.create_simple_notebook()
        success, output_path, error = self.runner.execute_notebook(notebook_path)
        
        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn("execution error", error.lower())
    
    @patch('src.notebook_runner.pm.execute_notebook')
    def test_execute_notebook_general_error(self, mock_execute):
        """Test notebook execution with general error."""
        mock_execute.side_effect = Exception("Some error")
        
        notebook_path = self.create_simple_notebook()
        success, output_path, error = self.runner.execute_notebook(notebook_path)
        
        self.assertFalse(success)
        self.assertIsNone(output_path)
        self.assertIsNotNone(error)
        self.assertIn("Error executing", error)
    
    def test_execute_notebook_file_not_found(self):
        """Test executing non-existent notebook."""
        success, output_path, error = self.runner.execute_notebook("/nonexistent/notebook.ipynb")
        
        self.assertFalse(success)
        self.assertIsNone(output_path)
        self.assertIsNotNone(error)
    
    @patch('src.notebook_runner.pm.execute_notebook')
    def test_execute_notebook_safe(self, mock_execute):
        """Test execute_notebook_safe method."""
        mock_execute.return_value = None
        
        notebook_path = self.create_simple_notebook()
        result = self.runner.execute_notebook_safe(notebook_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('output_path', result)
        self.assertIn('error_message', result)
        self.assertIn('execution_time', result)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['output_path'])
        self.assertIsNone(result['error_message'])
        self.assertIsInstance(result['execution_time'], float)
        self.assertGreater(result['execution_time'], 0)
    
    def test_get_notebook_outputs_nonexistent(self):
        """Test getting outputs from non-existent notebook."""
        outputs = self.runner.get_notebook_outputs("/nonexistent/notebook.ipynb")
        self.assertIsNone(outputs)
    
    def test_get_notebook_outputs_valid(self):
        """Test getting outputs from valid executed notebook."""
        # Create an executed notebook with outputs
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [
                        {
                            "output_type": "stream",
                            "name": "stdout",
                            "text": ["Hello\n"]
                        }
                    ],
                    "source": ["print('Hello')"]
                },
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
        
        filepath = os.path.join(self.test_dir, "executed.ipynb")
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        outputs = self.runner.get_notebook_outputs(filepath)
        
        self.assertIsNotNone(outputs)
        self.assertIsInstance(outputs, dict)
        self.assertIn('cell_0', outputs)
        self.assertEqual(len(outputs['cell_0']), 1)
    
    def test_get_notebook_outputs_no_outputs(self):
        """Test getting outputs from notebook with no outputs."""
        notebook_path = self.create_simple_notebook()
        outputs = self.runner.get_notebook_outputs(notebook_path)
        
        # Should return empty dict since no cells have outputs
        self.assertIsInstance(outputs, dict)
        self.assertEqual(len(outputs), 0)
    
    def test_get_notebook_namespace(self):
        """Test getting notebook namespace (currently returns None)."""
        notebook_path = self.create_simple_notebook()
        namespace = self.runner.get_notebook_namespace(notebook_path)
        
        # Current implementation returns None
        self.assertIsNone(namespace)
    
    def test_timeout_context_manager(self):
        """Test timeout context manager."""
        from src.notebook_runner import timeout
        import time
        
        # Should not raise error within timeout
        with timeout(2):
            time.sleep(0.1)
        
        # Should raise TimeoutException
        with self.assertRaises(TimeoutException):
            with timeout(1):
                time.sleep(2)
    
    def test_output_path_naming(self):
        """Test that output path is named correctly."""
        notebook_path = self.create_simple_notebook("my_notebook.ipynb")
        
        with patch('src.notebook_runner.pm.execute_notebook'):
            success, output_path, error = self.runner.execute_notebook(notebook_path)
            
            self.assertIn("my_notebook", output_path)
            self.assertIn("_executed.ipynb", output_path)
            self.assertTrue(output_path.startswith(self.output_dir))


class TestTimeoutException(unittest.TestCase):
    """Test cases for TimeoutException."""
    
    def test_timeout_exception_creation(self):
        """Test creating TimeoutException."""
        exc = TimeoutException("Test timeout")
        self.assertIsInstance(exc, Exception)
        self.assertEqual(str(exc), "Test timeout")


if __name__ == '__main__':
    unittest.main()
