"""Notebook execution module using papermill."""

import os
import traceback
from datetime import datetime
from typing import Optional, Tuple, Dict

import nbformat
import papermill as pm
from jupyter_client.kernelspec import KernelSpecManager


class TimeoutException(Exception):
    """Exception raised when notebook execution times out."""

    pass


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
        self.kernel_name = self._detect_kernel()


    def _ensure_output_dir(self):
        """Ensure output directory exists."""

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _detect_kernel(self) -> Optional[str]:
        """Detect the best available Python kernel.
        
        Returns:
            Name of the kernel to use, or None to use notebook's default
        """
        try:
            ksm = KernelSpecManager()
            available_kernels = ksm.get_all_specs()
            
            # Preferred kernel names in order of preference
            preferred_kernels = ['python3', 'python', 'python2', 'ir']
            
            for kernel in preferred_kernels:
                if kernel in available_kernels:
                    return kernel
            
            # If none of the preferred kernels found, use the first available
            if available_kernels:
                first_kernel = list(available_kernels.keys())[0]
                print(f"Using kernel: {first_kernel}")
                return first_kernel
            
            # Return None to let papermill use the notebook's kernel metadata
            print("Warning: No kernels found, will use notebook's default kernel")
            return None
            
        except Exception as e:
            print(f"Warning: Could not detect kernel: {e}")
            # Return None to let papermill use the notebook's kernel metadata
            return None


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
            # Prepare execution parameters
            exec_params = {
                'input_path': notebook_path,
                'output_path': output_path,
                'parameters': parameters or {},
                'progress_bar': False,
                'execution_timeout': self.timeout_seconds,  # Timeout per cell
                'timeout': self.timeout_seconds * 10  # Overall timeout
            }
            
            # Only set kernel_name if one was detected
            if self.kernel_name is not None:
                exec_params['kernel_name'] = self.kernel_name
            
            # Execute notebook with timeout using papermill's built-in timeout
            pm.execute_notebook(**exec_params)

            return True, output_path, None

        except pm.PapermillExecutionError as e:
            # Notebook executed but raised an error
            error_msg = f"Notebook execution error: {str(e)}"
            # Still save the output notebook to see where it failed
            return False, output_path if os.path.exists(output_path) else None, error_msg

        except Exception as e:
            # Other errors (file not found, invalid notebook format, timeout, etc.)
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
