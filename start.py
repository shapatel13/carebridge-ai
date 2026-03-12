#!/usr/bin/env python3
"""
CareBridge AI - Startup Script

This script:
1. Installs backend dependencies
2. Builds the React frontend (npm install + npm run build)
3. Starts the FastAPI backend server
4. Serves everything on http://localhost:8000

Usage:
    python start.py

Requirements:
    - Node.js and npm installed
    - Python 3.11+
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(step: int, total: int, text: str):
    """Print a step indicator."""
    print(f"[{step}/{total}] {text}")


def run_command(command: list[str], cwd: Path, description: str) -> bool:
    """Run a command and return success status."""
    print(f"  Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: {description} failed!")
        if e.stdout:
            print(f"  stdout: {e.stdout}")
        if e.stderr:
            print(f"  stderr: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"  ERROR: Command not found - {e}")
        return False


def check_nodejs() -> bool:
    """Check if Node.js and npm are installed."""
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    """Main startup function."""
    print_header("CareBridge AI - ICU Communication Platform")
    print("Starting application...\n")

    # Get paths
    project_root = Path(__file__).parent.absolute()
    frontend_dir = project_root / "frontend"
    backend_dir = project_root / "backend"

    total_steps = 5
    current_step = 1

    # Step 1: Check prerequisites
    print_step(current_step, total_steps, "Checking prerequisites...")
    if not check_nodejs():
        print("  ERROR: Node.js and npm are required but not found!")
        print("  Please install Node.js from https://nodejs.org/")
        sys.exit(1)
    
    # Check node version
    result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    print(f"  Node.js version: {result.stdout.strip()}")
    current_step += 1
    
    # Step 2: Install backend dependencies
    print_step(current_step, total_steps, "Installing backend dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], backend_dir, "pip install"):
        print("\n  WARNING: pip install had issues, trying to continue...")
    current_step += 1

    # Step 3: Install frontend dependencies
    print_step(current_step, total_steps, "Installing frontend dependencies...")
    if not run_command(["npm", "install"], frontend_dir, "npm install"):
        print("\n  WARNING: npm install had issues, trying to continue...")
    current_step += 1
    
    # Step 4: Build frontend
    print_step(current_step, total_steps, "Building frontend...")
    if not run_command(["npm", "run", "build"], frontend_dir, "npm run build"):
        print("\n  ERROR: Frontend build failed!")
        sys.exit(1)
    
    # Verify build output
    dist_dir = frontend_dir / "dist"
    index_html = dist_dir / "index.html"
    if not index_html.exists():
        print(f"  ERROR: Build output not found at {index_html}")
        sys.exit(1)
    print(f"  Build successful: {dist_dir}")
    current_step += 1
    
    # Step 5: Start backend server
    print_step(current_step, total_steps, "Starting FastAPI server...")
    print_header("CareBridge AI is Ready!")
    print("  App:  http://localhost:8000")
    print("  API:  http://localhost:8000/docs")
    print("  Demo: Click 'Try Demo Mode' on the login page")
    print("\n  Press Ctrl+C to stop the server\n")
    
    # Give user a moment to see the message
    time.sleep(1)
    
    # Start uvicorn
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
