#!/usr/bin/env python3
import sys
import os
import platform
import subprocess

def check_python_version():
    print("Checking Python version...")
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"  Current version: {sys.version} (Python {major}.{minor})")
    if major == 3 and minor >= 11:
        print("  [PASS] Python version is 3.11+.")
        return True
    else:
        print("  [FAIL] Python version should be 3.11+ (recommended 3.11).")
        return False

def check_architecture():
    print("Checking system architecture...")
    machine = platform.machine()
    system = platform.system()
    print(f"  OS: {system}, Machine: {machine}")
    
    if system == "Darwin" and machine != "arm64":
        # Check if we are on Apple Silicon running via Rosetta translation
        # (sysctl -n hw.optional.arm64 would return 1 on M1 Mac even if running x86_64 process)
        try:
            is_translation = subprocess.check_output(["sysctl", "-n", "sysctl.proc_translated"]).decode().strip()
            if is_translation == "1":
                print("  [WARNING] You are running Python under Rosetta 2 translation (x86_64).")
                print("            For native M1 GPU acceleration, run Python natively (arm64).")
                return True
        except Exception:
            pass
        print("  [INFO] Running on non-arm64 architecture.")
    elif system == "Darwin" and machine == "arm64":
        print("  [PASS] Running natively on Apple Silicon (arm64) macOS.")
    else:
        print("  [INFO] Running on non-macOS system.")
    return True

def check_dependencies():
    print("Checking Python packages...")
    packages = ["arcade", "pygame-ce"]
    missing = []
    
    for package in packages:
        try:
            # We import under try block
            if package == "pygame-ce":
                # pygame-ce is imported as pygame
                import pygame
                print(f"  [PASS] pygame-ce is installed (version: {pygame.__version__}).")
            else:
                import arcade
                print(f"  [PASS] arcade is installed (version: {arcade.__version__}).")
        except ImportError:
            print(f"  [FAIL] {package} is NOT installed.")
            missing.append(package)
            
    if missing:
        print("\nMissing packages detected! To install them, run:")
        print(f"  pip install {' '.join(missing)}")
        return False
    return True

def check_venv():
    print("Checking Virtual Environment...")
    # Check if VIRTUAL_ENV environment variable is set or if we are running from a sub-directory venv
    venv_active = "VIRTUAL_ENV" in os.environ
    if venv_active:
        print(f"  [PASS] Virtual environment active at: {os.environ['VIRTUAL_ENV']}")
    else:
        print("  [WARNING] No virtual environment active in the current shell.")
        print("            Please activate the virtual environment by running:")
        print("            source venv/bin/activate  (or source .venv/bin/activate)")
    return venv_active

def main():
    print("=" * 60)
    print("Halando - Project Environment Diagnostics")
    print("=" * 60)
    
    py_ok = check_python_version()
    print("-" * 40)
    arch_ok = check_architecture()
    print("-" * 40)
    venv_ok = check_venv()
    print("-" * 40)
    deps_ok = check_dependencies()
    
    print("=" * 60)
    if py_ok and deps_ok:
        print("SUCCESS: Your environment is ready to run Halando!")
        print("Run the game using: python src/main.py")
    else:
        print("ALERT: Some checks failed. Please see diagnostic output above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
