"""Notebook execution module using papermill."""

import os
import papermill as pm
from datetime import datetime
from typing import Optional, Tuple, Dict
import tempfile
import traceback
import signal
from contextlib import contextmanager


class TimeoutException(Exception):
    """Exception raised when notebook execution times out."""
    pass


@contextmanager
def timeout(seconds: int):
    """Context manager for timing out operations.
    
    Args:
        seconds: Number of seconds before timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Execution timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)


class NotebookRunner:
    """Handles execution of Jupyter notebooks."""
    
    def __init__(self, output_dir: str = "data/outputs", timeout_seconds: int = 300):
        """Initialize notebook runner.
        
        Args:
            output_dir: Directory to store executed notebooks
            timeout_seconds: Maximum execution time in seconds (default: 5 minutes)
        """
        self.output_dir = output_dir
        self.timeout_seconds = timeout_seconds
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def execute_notebook(
        self,
        notebook_path: str,
        parameters: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Execute a Jupyter notebook.
        
        Args:
            notebook_path: Path to the notebook file
            parameters: Optional parameters to inject into notebook
            
        Returns:
            Tuple of (success, output_path, error_message)
        """
        # Generate output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        notebook_name = os.path.splitext(os.path.basename(notebook_path))[0]
        output_path = os.path.join(
            self.output_dir,
            f"{notebook_name}_{timestamp}_executed.ipynb"
        )
        
        try:
            # Execute notebook with timeout
            with timeout(self.timeout_seconds):
                pm.execute_notebook(
                    notebook_path,
                    output_path,
                    parameters=parameters or {},
                    kernel_name='python3',
                    progress_bar=False
                )
            
            return True, output_path, None
            
        except TimeoutException as e:
            error_msg = str(e)
            return False, None, error_msg
            
        except pm.PapermillExecutionError as e:
            # Notebook executed but raised an error
            error_msg = f"Notebook execution error: {str(e)}"
            # Still save the output notebook to see where it failed
            return False, output_path if os.path.exists(output_path) else None, error_msg
            
        except Exception as e:
            # Other errors (file not found, invalid notebook format, etc.)
            error_msg = f"Error executing notebook: {str(e)}\n{traceback.format_exc()}"
            return False, None, error_msg
    
    def execute_notebook_safe(
        self,
        notebook_path: str,
        parameters: Optional[Dict] = None
    ) -> Dict[str, any]:
        """Execute notebook with comprehensive error handling and return status.
        
        Args:
            notebook_path: Path to the notebook file
            parameters: Optional parameters to inject into notebook
            
        Returns:
            Dictionary with execution results:
            {
                'success': bool,
                'output_path': str or None,
                'error_message': str or None,
                'execution_time': float (seconds)
            }
        """
        start_time = datetime.now()
        
        success, output_path, error_message = self.execute_notebook(
            notebook_path,
            parameters
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': success,
            'output_path': output_path,
            'error_message': error_message,
            'execution_time': execution_time
        }
    
    def get_notebook_outputs(self, executed_notebook_path: str) -> Optional[Dict]:
        """Extract outputs from an executed notebook.
        
        Args:
            executed_notebook_path: Path to the executed notebook
            
        Returns:
            Dictionary of outputs or None if extraction fails
        """
        try:
            import nbformat
            
            with open(executed_notebook_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            outputs = {}
            for i, cell in enumerate(nb.cells):
                if cell.cell_type == 'code' and cell.outputs:
                    outputs[f'cell_{i}'] = cell.outputs
            
            return outputs
            
        except Exception as e:
            print(f"Error extracting outputs: {e}")
            return None
    
    def get_notebook_namespace(self, executed_notebook_path: str) -> Optional[Dict]:
        """Extract the final namespace/variables from an executed notebook.
        
        Note: This is a simplified version. For production use, consider
        using papermill's scrapbook library for better variable extraction.
        
        Args:
            executed_notebook_path: Path to the executed notebook
            
        Returns:
            Dictionary of variables or None if extraction fails
        """
        try:
            # This would require scrapbook for proper implementation
            # For now, return None and recommend using scrapbook
            # in the notebooks to explicitly record outputs
            return None
            
        except Exception as e:
            print(f"Error extracting namespace: {e}")
            return None
