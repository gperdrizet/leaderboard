"""Unit tests for scorer module."""

import unittest
import os
import tempfile
import json
import shutil

from src.scorer import Scorer, simple_accuracy_scorer, mse_scorer


class TestScorer(unittest.TestCase):
    """Test cases for Scorer class."""
    
    def setUp(self):
        """Set up test files before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.scorer = Scorer()
    
    def tearDown(self):
        """Clean up test files after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_executed_notebook(self, filename="executed.ipynb", execution_count=1):
        """Helper to create an executed notebook file."""
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": execution_count,
                    "metadata": {},
                    "outputs": [
                        {
                            "output_type": "stream",
                            "name": "stdout",
                            "text": ["Hello World\n"]
                        }
                    ],
                    "source": ["print('Hello World')"]
                },
                {
                    "cell_type": "code",
                    "execution_count": execution_count + 1,
                    "metadata": {},
                    "outputs": [],
                    "source": ["x = 42"]
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
    
    def create_ground_truth_file(self, filename="ground_truth.json"):
        """Helper to create a ground truth file."""
        ground_truth = {
            "expected_result": 42,
            "expected_accuracy": 0.95
        }
        
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(ground_truth, f)
        
        return filepath
    
    def test_scorer_initialization(self):
        """Test scorer initialization."""
        scorer = Scorer()
        self.assertIsNone(scorer.ground_truth)
    
    def test_scorer_initialization_with_ground_truth(self):
        """Test scorer initialization with ground truth file."""
        gt_path = self.create_ground_truth_file()
        scorer = Scorer(ground_truth_path=gt_path)
        self.assertIsNotNone(scorer.ground_truth)
        self.assertEqual(scorer.ground_truth['expected_result'], 42)
    
    def test_scorer_load_ground_truth_invalid_path(self):
        """Test scorer with invalid ground truth path."""
        scorer = Scorer(ground_truth_path="/nonexistent/path.json")
        self.assertIsNone(scorer.ground_truth)
    
    def test_score_notebook_basic(self):
        """Test basic notebook scoring."""
        filepath = self.create_executed_notebook()
        score, feedback = self.scorer.score_notebook(filepath)
        
        # Should return numeric score and string feedback
        self.assertIsInstance(score, float)
        self.assertIsInstance(feedback, str)
        self.assertGreaterEqual(score, 0.0)
    
    def test_score_notebook_all_cells_executed(self):
        """Test scoring when all cells are executed."""
        filepath = self.create_executed_notebook()
        score, feedback = self.scorer.score_notebook(filepath)
        
        # Should get points for completion
        self.assertGreater(score, 0.0)
    
    def test_score_notebook_partial_execution(self):
        """Test scoring with partially executed notebook."""
        # Create notebook with mixed execution counts
        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": ["x = 1"]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,  # Not executed
                    "metadata": {},
                    "outputs": [],
                    "source": ["y = 2"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        filepath = os.path.join(self.temp_dir, "partial.ipynb")
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        score, feedback = self.scorer.score_notebook(filepath)
        
        # Score should reflect partial execution (50% of 10 points = 5.0)
        self.assertAlmostEqual(score, 5.0, places=1)
    
    def test_score_notebook_no_code_cells(self):
        """Test scoring notebook with no code cells."""
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
        
        filepath = os.path.join(self.temp_dir, "nocode.ipynb")
        with open(filepath, 'w') as f:
            json.dump(notebook_content, f)
        
        score, feedback = self.scorer.score_notebook(filepath)
        self.assertEqual(score, 0.0)
    
    def test_score_notebook_invalid_file(self):
        """Test scoring with invalid notebook file."""
        score, feedback = self.scorer.score_notebook("/nonexistent/notebook.ipynb")
        
        # Should return 0 score and error message
        self.assertEqual(score, 0.0)
        self.assertIn("Error", feedback)
    
    def test_score_from_variables_empty(self):
        """Test scoring from empty variables dict."""
        score, feedback = self.scorer.score_from_variables({})
        self.assertEqual(score, 0.0)
        self.assertIn("No variables", feedback)
    
    def test_score_from_variables_with_data(self):
        """Test scoring from variables dict with data."""
        variables = {"accuracy": 0.95, "result": 42}
        score, feedback = self.scorer.score_from_variables(variables)
        
        # Should return valid score and feedback
        self.assertIsInstance(score, float)
        self.assertIsInstance(feedback, str)
    
    def test_score_custom(self):
        """Test custom scoring function."""
        submission_data = {"predictions": [1, 2, 3]}
        scoring_criteria = {"threshold": 0.9}
        
        score, feedback = self.scorer.score_custom(submission_data, scoring_criteria)
        
        # Should return valid score and feedback
        self.assertIsInstance(score, float)
        self.assertIsInstance(feedback, str)


class TestScorerHelperFunctions(unittest.TestCase):
    """Test cases for scorer helper functions."""
    
    def test_simple_accuracy_scorer_perfect(self):
        """Test accuracy scorer with perfect predictions."""
        predictions = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        
        accuracy = simple_accuracy_scorer(predictions, ground_truth)
        self.assertEqual(accuracy, 100.0)
    
    def test_simple_accuracy_scorer_partial(self):
        """Test accuracy scorer with partial accuracy."""
        predictions = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 0, 0, 5]  # 3 out of 5 correct
        
        accuracy = simple_accuracy_scorer(predictions, ground_truth)
        self.assertEqual(accuracy, 60.0)
    
    def test_simple_accuracy_scorer_zero(self):
        """Test accuracy scorer with zero accuracy."""
        predictions = [1, 2, 3]
        ground_truth = [4, 5, 6]
        
        accuracy = simple_accuracy_scorer(predictions, ground_truth)
        self.assertEqual(accuracy, 0.0)
    
    def test_simple_accuracy_scorer_length_mismatch(self):
        """Test accuracy scorer with mismatched lengths."""
        predictions = [1, 2, 3]
        ground_truth = [1, 2]
        
        accuracy = simple_accuracy_scorer(predictions, ground_truth)
        self.assertEqual(accuracy, 0.0)
    
    def test_mse_scorer_perfect(self):
        """Test MSE scorer with perfect predictions."""
        import numpy as np
        predictions = [1.0, 2.0, 3.0]
        ground_truth = [1.0, 2.0, 3.0]
        
        mse = mse_scorer(predictions, ground_truth)
        self.assertEqual(mse, 0.0)
    
    def test_mse_scorer_with_error(self):
        """Test MSE scorer with some error."""
        import numpy as np
        predictions = [1.0, 2.0, 3.0]
        ground_truth = [1.5, 2.5, 3.5]
        
        mse = mse_scorer(predictions, ground_truth)
        # MSE = ((0.5)^2 + (0.5)^2 + (0.5)^2) / 3 = 0.25
        # Returned value is -MSE (negative)
        self.assertAlmostEqual(mse, -0.25, places=5)
    
    def test_mse_scorer_length_mismatch(self):
        """Test MSE scorer with mismatched lengths."""
        predictions = [1.0, 2.0, 3.0]
        ground_truth = [1.0, 2.0]
        
        mse = mse_scorer(predictions, ground_truth)
        self.assertEqual(mse, -float('inf'))


if __name__ == '__main__':
    unittest.main()
