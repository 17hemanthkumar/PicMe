"""
Unit tests for Dockerfile validation.

These tests verify that the Dockerfile contains all required components
for containerizing the PicMe application.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

import os
import pytest


def read_dockerfile():
    """Helper function to read the Dockerfile content."""
    dockerfile_path = os.path.join(os.path.dirname(__file__), '..', 'Dockerfile')
    with open(dockerfile_path, 'r') as f:
        return f.read()


def test_dockerfile_contains_correct_base_image():
    """
    Test that Dockerfile contains correct base image.
    
    Validates: Requirements 1.1
    """
    content = read_dockerfile()
    assert 'FROM python:3.10-slim' in content, \
        "Dockerfile must use python:3.10-slim as base image"


def test_dockerfile_contains_all_required_system_packages():
    """
    Test that Dockerfile contains all required system packages for dlib and OpenCV.
    
    Validates: Requirements 1.2
    """
    content = read_dockerfile()
    
    required_packages = [
        'build-essential',
        'cmake',
        'libgl1',
        'libglib2.0-0'
    ]
    
    for package in required_packages:
        assert package in content, \
            f"Dockerfile must install {package} for dlib/OpenCV compatibility"


def test_dockerfile_cleans_apt_cache():
    """
    Test that Dockerfile cleans up apt cache to reduce image size.
    
    Validates: Requirements 6.1, 6.2
    """
    content = read_dockerfile()
    assert 'rm -rf /var/lib/apt/lists/*' in content, \
        "Dockerfile must clean up apt cache to minimize image size"


def test_dockerfile_contains_correct_copy_commands():
    """
    Test that Dockerfile contains correct COPY commands.
    
    Validates: Requirements 1.3
    """
    content = read_dockerfile()
    
    # Check for WORKDIR
    assert 'WORKDIR /app' in content, \
        "Dockerfile must set WORKDIR to /app"
    
    # Check for COPY backend command
    assert 'COPY backend /app' in content, \
        "Dockerfile must copy backend directory to /app"


def test_dockerfile_upgrades_pip():
    """
    Test that Dockerfile upgrades pip before installing packages.
    
    Validates: Requirements 1.4
    """
    content = read_dockerfile()
    assert 'pip install --upgrade pip' in content, \
        "Dockerfile must upgrade pip before installing packages"


def test_dockerfile_installs_requirements():
    """
    Test that Dockerfile installs Python packages from requirements.txt.
    
    Validates: Requirements 1.4
    """
    content = read_dockerfile()
    assert 'pip install' in content and '-r requirements.txt' in content, \
        "Dockerfile must install packages from requirements.txt"


def test_dockerfile_exposes_correct_port():
    """
    Test that Dockerfile exposes port 8080.
    
    Validates: Requirements 1.5
    """
    content = read_dockerfile()
    assert 'EXPOSE 8080' in content, \
        "Dockerfile must expose port 8080"


def test_dockerfile_contains_correct_cmd():
    """
    Test that Dockerfile contains correct CMD for running gunicorn.
    
    Validates: Requirements 1.5, 5.1, 5.2, 5.3
    """
    content = read_dockerfile()
    
    # Check for gunicorn command
    assert 'gunicorn' in content, \
        "Dockerfile CMD must use gunicorn"
    
    # Check for either inline config or config file
    has_inline_config = '0.0.0.0:8080' in content
    has_config_file = 'gunicorn_config.py' in content
    
    assert has_inline_config or has_config_file, \
        "Dockerfile CMD must configure gunicorn binding (inline or via config file)"
    
    # Check for app:app
    assert 'app:app' in content, \
        "Dockerfile CMD must specify app:app as the application"


def test_dockerfile_configures_gunicorn_workers():
    """
    Test that Dockerfile configures gunicorn with appropriate workers.
    
    Validates: Requirements 5.3
    """
    content = read_dockerfile()
    
    # Check for worker configuration (either inline or via config file)
    has_inline_workers = '-w' in content or '--workers' in content
    has_config_file = 'gunicorn_config.py' in content
    
    assert has_inline_workers or has_config_file, \
        "Dockerfile CMD must configure gunicorn workers (inline or via config file)"


def test_dockerfile_configures_gunicorn_timeout():
    """
    Test that Dockerfile configures gunicorn with appropriate timeout.
    
    Validates: Requirements 5.3
    """
    content = read_dockerfile()
    
    # Check for timeout configuration
    assert '--timeout' in content or 'timeout' in content, \
        "Dockerfile CMD must configure gunicorn timeout for face recognition operations"


def test_dockerfile_structure_order():
    """
    Test that Dockerfile follows best practices for layer ordering.
    
    This ensures that frequently changing layers (like application code)
    come after stable layers (like system dependencies).
    """
    content = read_dockerfile()
    lines = content.split('\n')
    
    from_index = -1
    apt_index = -1
    workdir_index = -1
    copy_index = -1
    pip_index = -1
    cmd_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith('FROM'):
            from_index = i
        elif 'apt-get' in line:
            apt_index = i
        elif line.startswith('WORKDIR'):
            workdir_index = i
        elif line.startswith('COPY'):
            copy_index = i
        elif 'pip install' in line:
            pip_index = i
        elif line.startswith('CMD'):
            cmd_index = i
    
    # Verify order: FROM -> apt-get -> WORKDIR -> COPY -> pip -> CMD
    assert from_index < apt_index, "FROM must come before apt-get"
    assert apt_index < workdir_index, "System dependencies must be installed before setting WORKDIR"
    assert workdir_index < copy_index, "WORKDIR must be set before COPY"
    assert copy_index < pip_index, "Application code must be copied before pip install"
    assert pip_index < cmd_index, "Dependencies must be installed before CMD"
