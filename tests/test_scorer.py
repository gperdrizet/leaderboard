"""Unit tests for scorer module."""

import unittest
import os
import tempfile
import shutil
import pandas as pd

from src.scorer import Scorer


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
    
    def create_csv_file(self, filename="output.csv", data=None):
        """Helper to create a CSV file."""
        if data is None:
            data = pd.DataFrame({
                'A': [1, 2, 3],
                'B': [4, 5, 6],
                'C': [7, 8, 9]
            })
        
        filepath = os.path.join(self.temp_dir, filename)
        data.to_csv(filepath, index=False)
        return filepath
    
    def create_ground_truth_csv(self, filename="ground_truth.csv"):
        """Helper to create a ground truth CSV file."""
        data = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })
        
        filepath = os.path.join(self.temp_dir, filename)
        data.to_csv(filepath, index=False)
        return filepath
    
    def test_scorer_initialization(self):
        """Test scorer initialization."""
        scorer = Scorer()
        self.assertIsNone(scorer.ground_truth)
    
    def test_scorer_initialization_with_ground_truth(self):
        """Test scorer initialization with ground truth CSV file."""
        gt_path = self.create_ground_truth_csv()
        scorer = Scorer(ground_truth_path=gt_path)
        self.assertIsNotNone(scorer.ground_truth)
        self.assertEqual(len(scorer.ground_truth), 3)
    
    def test_scorer_load_ground_truth_invalid_path(self):
        """Test scorer with invalid ground truth path."""
        scorer = Scorer(ground_truth_path="/nonexistent/path.csv")
        self.assertIsNone(scorer.ground_truth)
    
    def test_score_notebook_no_csv(self):
        """Test scoring when no CSV file exists."""
        # Create empty directory with a dummy notebook
        notebook_path = os.path.join(self.temp_dir, "test.ipynb")
        with open(notebook_path, 'w') as f:
            f.write("{}")
        
        score, feedback = self.scorer.score_notebook(notebook_path)
        
        self.assertEqual(score, 0.0)
        self.assertIn("No CSV file found", feedback)
    
    def test_score_notebook_with_csv(self):
        """Test scoring when CSV file exists."""
        # Create CSV in temp directory
        self.create_csv_file()
        
        # Create notebook path in same directory
        notebook_path = os.path.join(self.temp_dir, "test.ipynb")
        
        score, feedback = self.scorer.score_notebook(notebook_path)
        
        # Should get points for having CSV
        self.assertGreater(score, 0.0)
        self.assertIsInstance(feedback, str)
    
    def test_score_notebook_invalid_file(self):
        """Test scoring with invalid notebook file."""
        score, feedback = self.scorer.score_notebook("/nonexistent/notebook.ipynb")
        
        # Should return 0 score and error message
        self.assertEqual(score, 0.0)
        self.assertIn("Error", feedback)
    
    def test_score_against_ground_truth_perfect(self):
        """Test scoring against ground truth with perfect match."""
        gt_path = self.create_ground_truth_csv()
        scorer = Scorer(ground_truth_path=gt_path)
        
        # Create matching CSV
        csv_path = self.create_csv_file()
        
        score, feedback = scorer.score_from_csv_path(csv_path)
        
        # Should get 100% accuracy
        self.assertEqual(score, 100.0)
        self.assertIn("100.00%", feedback)
    
    def test_score_against_ground_truth_partial(self):
        """Test scoring against ground truth with partial match."""
        gt_path = self.create_ground_truth_csv()
        scorer = Scorer(ground_truth_path=gt_path)
        
        # Create CSV with some differences
        data = pd.DataFrame({
            'A': [1, 2, 99],  # Third value differs
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })
        csv_path = self.create_csv_file(data=data)
        
        score, feedback = scorer.score_from_csv_path(csv_path)
        
        # Should get 8/9 = 88.89% accuracy
        self.assertAlmostEqual(score, 88.89, places=1)
    
    def test_score_against_ground_truth_shape_mismatch(self):
        """Test scoring with shape mismatch."""
        gt_path = self.create_ground_truth_csv()
        scorer = Scorer(ground_truth_path=gt_path)
        
        # Create CSV with different shape
        data = pd.DataFrame({
            'A': [1, 2],  # Only 2 rows instead of 3
            'B': [4, 5]
        })
        csv_path = self.create_csv_file(data=data)
        
        score, feedback = scorer.score_from_csv_path(csv_path)
        
        # Should get 0 for shape mismatch
        self.assertEqual(score, 0.0)
        self.assertIn("shape mismatch", feedback)
    
    def test_score_against_ground_truth_column_mismatch(self):
        """Test scoring with column mismatch."""
        gt_path = self.create_ground_truth_csv()
        scorer = Scorer(ground_truth_path=gt_path)
        
        # Create CSV with different columns
        data = pd.DataFrame({
            'X': [1, 2, 3],
            'Y': [4, 5, 6],
            'Z': [7, 8, 9]
        })
        csv_path = self.create_csv_file(data=data)
        
        score, feedback = scorer.score_from_csv_path(csv_path)
        
        # Should get 0 for column mismatch
        self.assertEqual(score, 0.0)
        self.assertIn("Error comparing with ground truth", feedback)
    
    def test_basic_csv_validation(self):
        """Test basic CSV validation when no ground truth exists."""
        # Create CSV
        csv_path = self.create_csv_file()
        
        score, feedback = self.scorer.score_from_csv_path(csv_path)
        
        # Should get points for valid CSV
        self.assertGreater(score, 0.0)
        self.assertIn("rows and", feedback)
    
    def test_csv_with_null_values(self):
        """Test CSV with null values."""
        data = pd.DataFrame({
            'A': [1, None, 3],
            'B': [4, 5, 6]
        })
        csv_path = self.create_csv_file(data=data)
        
        score, feedback = self.scorer.score_from_csv_path(csv_path)
        
        # Should still process but may note null values
        self.assertIsInstance(score, float)
        self.assertIsInstance(feedback, str)


if __name__ == '__main__':
    unittest.main()
