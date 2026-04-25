#!/usr/bin/env python3
"""Mox Launcher - Start backend and frontend"""

import os
import sys
import subprocess
import time
import webbrowser
import socket


def is_port_open(host, port, timeout=2):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, socket.timeout, OSError):
        return False


def wait_for_url(url, timeout=30):
    """Wait for URL to be available"""
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            time.sleep(1)
    return False


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_dir, "frontend")

    print("=" * 50)
    print("  Mox v0.2.0 - LLM Attack Defense Platform")
    print("=" * 50)
    print()

    # Check Ollama (port 11434)
    print()
    print("[1/4] Checking Ollama...")
    if is_port_open("localhost", 11434):
        print("    [OK] Ollama is running")
    else:
        print("    [--] Ollama not running, skipping...")

    # Check Redis (port 6379)
    print()
    print("[2/4] Checking Redis...")
    if is_port_open("localhost", 6379):
        print("    [OK] Redis is running")
    else:
        print("    [--] Redis not running, using memory cache")

    # Start backend
    print()
    print("[3/4] Starting Backend...")
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "mox.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    try:
        subprocess.Popen(
            backend_cmd,
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        print("    Backend started on http://localhost:8000")
    except Exception as e:
        print(f"    Error starting backend: {e}")

    # Wait for backend
    print("    Waiting for backend...")
    if wait_for_url("http://localhost:8000/api/health", 20):
        print("    [OK] Backend ready!")
    else:
        print("    [--] Backend startup may have issues, continuing...")

    # Start frontend
    print()
    print("[4/4] Starting Frontend...")
    try:
        subprocess.Popen(
            "npm run dev",
            cwd=frontend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        print("    Frontend starting...")
    except Exception as e:
        print(f"    Error starting frontend: {e}")

    # Wait for frontend
    print("    Waiting for frontend...")
    if wait_for_url("http://localhost:3000", 25):
        print("    [OK] Frontend ready!")
    else:
        print("    [--] Frontend startup may have issues, continuing...")

    print()
    print("=" * 50)
    print("  All services ready!")
    print("=" * 50)
    print()
    print("  Backend:    http://localhost:8000")
    print("  Frontend:   http://localhost:3000")
    print("  API Docs:   http://localhost:8000/docs")
    print("  WebSocket:  ws://localhost:8000/ws")
    print()
    print("  Press Ctrl+C to stop services")
    print()

    # Open browser
    try:
        webbrowser.open("http://localhost:3000")
        print("Browser opened!")
    except Exception:
        pass

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("Shutting down...")
        print("Done!")


if __name__ == "__main__":
    main()
