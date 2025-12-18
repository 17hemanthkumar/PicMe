"""
Property-based tests for Docker container build.

These tests validate the correctness properties defined in the design document
for the docker deployment feature.

**Feature: docker-deployment, Property 1: Container build completeness**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
"""

import pytest
import os
import subprocess
import sys
from hypothesis import given, settings, strategies as st


# ============================================================================
# Property 1: Container build completeness
# **Feature: docker-deployment, Property 1: Container build completeness**
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
# ============================================================================

def test_property_container_build_completeness():
    """
    Property 1: Container build completeness
    
    For any Docker build execution with the provided Dockerfile, the build
    process should complete successfully without errors and produce a runnable
    image with all required dependencies installed.
    
    **Feature: docker-deployment, Property 1: Container build completeness**
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    """
    # Get the project root directory (parent of backend)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if Docker is available
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("Docker is not available on this system")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("Docker is not available on this system")
    
    # Build the Docker image
    build_result = subprocess.run(
        ['docker', 'build', '-t', 'picme-test', '.'],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=600  # 10 minutes timeout for build
    )
    
    # Verify build completed successfully
    assert build_result.returncode == 0, \
        f"Docker build should complete without errors. Error: {build_result.stderr}"
    
    # Verify the image was created
    inspect_result = subprocess.run(
        ['docker', 'inspect', 'picme-test'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert inspect_result.returncode == 0, \
        "Docker image 'picme-test' should exist after build"
    
    # Verify image size is reasonable (< 2GB = 2147483648 bytes)
    size_result = subprocess.run(
        ['docker', 'images', 'picme-test', '--format', '{{.Size}}'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert size_result.returncode == 0, \
        "Should be able to query image size"
    
    # Parse size (format could be like "1.5GB" or "500MB")
    size_str = size_result.stdout.strip()
    
    # Extract numeric value and unit
    import re
    match = re.match(r'([\d.]+)([A-Z]+)', size_str)
    if match:
        size_value = float(match.group(1))
        size_unit = match.group(2)
        
        # Convert to GB for comparison
        if size_unit == 'MB':
            size_gb = size_value / 1024
        elif size_unit == 'GB':
            size_gb = size_value
        elif size_unit == 'KB':
            size_gb = size_value / (1024 * 1024)
        else:
            size_gb = 0
        
        assert size_gb < 2.0, \
            f"Image size should be less than 2GB, got {size_str}"
    
    # Verify required components are in the image
    # Check that Python is installed
    python_check = subprocess.run(
        ['docker', 'run', '--rm', 'picme-test', 'python', '--version'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert python_check.returncode == 0, \
        "Python should be installed in the image"
    assert 'Python 3.10' in python_check.stdout, \
        "Python 3.10 should be installed"
    
    # Check that gunicorn is installed
    gunicorn_check = subprocess.run(
        ['docker', 'run', '--rm', 'picme-test', 'gunicorn', '--version'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert gunicorn_check.returncode == 0, \
        "Gunicorn should be installed in the image"
    
    # Check that required Python packages are installed
    packages_to_check = ['flask', 'face-recognition', 'numpy', 'opencv-python', 'psycopg2']
    
    for package in packages_to_check:
        package_check = subprocess.run(
            ['docker', 'run', '--rm', 'picme-test', 'python', '-c', 
             f'import {package.replace("-", "_")}'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert package_check.returncode == 0, \
            f"Package {package} should be installed in the image"
    
    # Check that app.py exists in the image
    app_check = subprocess.run(
        ['docker', 'run', '--rm', 'picme-test', 'ls', '/app/app.py'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    assert app_check.returncode == 0, \
        "app.py should exist in /app directory"
    
    # Cleanup: remove the test image
    subprocess.run(
        ['docker', 'rmi', 'picme-test'],
        capture_output=True,
        timeout=30
    )


def test_dockerfile_exists():
    """
    Test that Dockerfile exists in the project root.
    
    This is a prerequisite for the container build property test.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile_path = os.path.join(project_root, 'Dockerfile')
    
    assert os.path.exists(dockerfile_path), \
        "Dockerfile should exist in project root"


def test_dockerignore_exists():
    """
    Test that .dockerignore exists in the project root.
    
    This ensures unnecessary files are excluded from the build context.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerignore_path = os.path.join(project_root, '.dockerignore')
    
    assert os.path.exists(dockerignore_path), \
        ".dockerignore should exist in project root"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
