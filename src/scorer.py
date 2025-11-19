"""Scoring module for evaluating notebook outputs.

This module provides a customizable scoring function that evaluates
the outputs from executed notebooks. Modify this to match your specific
assignment requirements.
"""

import os
from typing import Dict, Optional, Tuple, Any
import pickle
import json


class Scorer:
    """Handles scoring of notebook outputs."""
    
    def __init__(self, ground_truth_path: Optional[str] = None):
        """Initialize scorer.
        
        Args:
            ground_truth_path: Optional path to ground truth data/answers
        """
        self.ground_truth_path = ground_truth_path
        self.ground_truth = None
        
        if ground_truth_path and os.path.exists(ground_truth_path):
            self._load_ground_truth()
    
    def _load_ground_truth(self):
        """Load ground truth data from file."""
        try:
            # Try loading as JSON first
            with open(self.ground_truth_path, 'r') as f:
                self.ground_truth = json.load(f)
        except json.JSONDecodeError:
            # Try loading as pickle
            try:
                with open(self.ground_truth_path, 'rb') as f:
                    self.ground_truth = pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load ground truth: {e}")
                self.ground_truth = None
    
    def score_notebook(
        self,
        executed_notebook_path: str,
        output_data: Optional[Dict] = None
    ) -> Tuple[float, str]:
        """Score an executed notebook.
        
        This is a template scoring function. Customize it based on your
        specific assignment requirements.
        
        Args:
            executed_notebook_path: Path to the executed notebook
            output_data: Optional dictionary of extracted outputs
            
        Returns:
            Tuple of (score, feedback_message)
        """
        try:
            # Import here to avoid circular dependencies
            import nbformat
            
            # Read the executed notebook
            with open(executed_notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Example scoring logic - customize this!
            score = 0.0
            feedback_parts = []
            
            # Example 1: Check if specific variables are defined
            # This is a placeholder - you'll need to customize based on your needs
            score += self._check_notebook_completion(nb)
            feedback_parts.append("Notebook completion checked")
            
            # Example 2: If you have ground truth data
            if self.ground_truth:
                accuracy_score = self._compare_with_ground_truth(nb, self.ground_truth)
                score += accuracy_score
                feedback_parts.append(f"Accuracy score: {accuracy_score}")
            
            # Example 3: Check for specific output patterns
            # Add your custom scoring logic here
            
            feedback = " | ".join(feedback_parts)
            
            return score, feedback
            
        except Exception as e:
            return 0.0, f"Error scoring notebook: {str(e)}"
    
    def _check_notebook_completion(self, nb) -> float:
        """Check if notebook executed successfully.
        
        Args:
            nb: Notebook object from nbformat
            
        Returns:
            Score based on completion
        """
        # Count executed cells
        executed_cells = 0
        total_code_cells = 0
        
        for cell in nb.cells:
            if cell.cell_type == 'code':
                total_code_cells += 1
                # Check if cell has execution count (was executed)
                if cell.execution_count is not None:
                    executed_cells += 1
        
        if total_code_cells == 0:
            return 0.0
        
        # Return score based on percentage of cells executed
        completion_rate = executed_cells / total_code_cells
        return completion_rate * 10.0  # Max 10 points for completion
    
    def _compare_with_ground_truth(self, nb, ground_truth: Dict) -> float:
        """Compare notebook outputs with ground truth.
        
        This is a template function. Customize based on your assignment.
        
        Args:
            nb: Notebook object
            ground_truth: Ground truth data dictionary
            
        Returns:
            Score based on accuracy
        """
        # This is a placeholder implementation
        # You should customize this based on your specific requirements
        
        # Example: Extract variables from notebook using scrapbook
        # or parse output cells for specific values
        
        score = 0.0
        
        # TODO: Implement your custom comparison logic here
        # For example:
        # - Compare computed values with expected values
        # - Check if plots were generated
        # - Verify model accuracy metrics
        # - Check data processing steps
        
        return score
    
    def score_from_variables(self, variables: Dict[str, Any]) -> Tuple[float, str]:
        """Score based on extracted variables from notebook.
        
        This method is useful when using scrapbook or similar tools
        to extract specific variables from notebooks.
        
        Args:
            variables: Dictionary of variable names and values
            
        Returns:
            Tuple of (score, feedback_message)
        """
        score = 0.0
        feedback_parts = []
        
        # Example scoring based on specific variables
        # Customize this based on your assignment
        
        if not variables:
            return 0.0, "No variables found for scoring"
        
        # TODO: Add your custom variable-based scoring logic
        # Example:
        # if 'accuracy' in variables:
        #     score += min(variables['accuracy'] * 100, 50)
        #     feedback_parts.append(f"Accuracy: {variables['accuracy']:.2%}")
        
        feedback = " | ".join(feedback_parts) if feedback_parts else "Scored successfully"
        return score, feedback
    
    def score_custom(
        self,
        submission_data: Dict[str, Any],
        scoring_criteria: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Custom scoring function with flexible criteria.
        
        Args:
            submission_data: Data extracted from submission
            scoring_criteria: Criteria to use for scoring
            
        Returns:
            Tuple of (score, feedback_message)
        """
        # Implement your custom scoring logic here
        # This is a flexible template for various scoring needs
        
        score = 0.0
        feedback = "Custom scoring completed"
        
        return score, feedback


# Example scoring function for specific use cases
def simple_accuracy_scorer(predictions, ground_truth) -> float:
    """Simple accuracy scorer for classification tasks.
    
    Args:
        predictions: List or array of predictions
        ground_truth: List or array of ground truth labels
        
    Returns:
        Accuracy score (0-100)
    """
    if len(predictions) != len(ground_truth):
        return 0.0
    
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    accuracy = (correct / len(predictions)) * 100
    return accuracy


def mse_scorer(predictions, ground_truth) -> float:
    """Mean squared error scorer for regression tasks.
    
    Args:
        predictions: List or array of predictions
        ground_truth: List or array of ground truth values
        
    Returns:
        Negative MSE (higher is better)
    """
    import numpy as np
    
    if len(predictions) != len(ground_truth):
        return -float('inf')
    
    mse = np.mean((np.array(predictions) - np.array(ground_truth)) ** 2)
    # Return negative MSE so higher is better
    return -mse
