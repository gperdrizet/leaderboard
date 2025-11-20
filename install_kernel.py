#!/usr/bin/env python3
"""Install and register the IPython kernel for Jupyter."""

import sys
import subprocess

def install_kernel():
    """Install and register the IPython kernel."""
    try:
        # Install ipykernel if not already installed
        print("Installing ipykernel...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ipykernel"])
        
        # Install the kernel spec
        print("Registering kernel...")
        subprocess.check_call([
            sys.executable, "-m", "ipykernel", "install", 
            "--user", "--name", "python3", "--display-name", "Python 3"
        ])
        
        print("✓ Kernel installed successfully!")
        
        # List available kernels
        print("\nAvailable kernels:")
        subprocess.check_call([sys.executable, "-m", "jupyter", "kernelspec", "list"])
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing kernel: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_kernel()
