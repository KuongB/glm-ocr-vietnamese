"""
Check Backend Health and Configuration

Run this script to verify backend setup before starting the server.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("⚠️  Warning: Python 3.11+ recommended")
        return False
    print("✅ Python version OK")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "httpx",
        "Pillow"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_").lower())
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        print("❌ .env file not found")
        if env_example_path.exists():
            print("💡 Copy .env.example to .env:")
            print("   cp .env.example .env  # Linux/Mac")
            print("   copy .env.example .env  # Windows")
        return False
    
    print("✅ .env file exists")
    
    # Check for Modal API URL (required)
    with open(env_path, 'r') as f:
        content = f.read()
        
        if "MODAL_API_URL=" in content:
            url_line = content.split("MODAL_API_URL=")[1].split('\n')[0].strip()
            if url_line and len(url_line) > 10 and not url_line.startswith("https://your-"):
                print("✅ Modal API URL configured")
            else:
                print("⚠️  MODAL_API_URL not configured or using default template")
                print("💡 Set your actual Modal API URL in .env file")
                print("   Example: MODAL_API_URL=https://username--glm-ocr-api-ocr-endpoint.modal.run")
                print("   See MODAL_DEPLOYMENT.md for deployment instructions")
        else:
            print("❌ MODAL_API_URL not found in .env")
            print("💡 Add MODAL_API_URL to your .env file")
    
    return True

def check_project_structure():
    """Check if all required files exist"""
    required_files = [
        "main.py",
        "requirements.txt",
        "app/__init__.py",
        "app/config.py",
        "app/services/ocr_service.py",
        "app/routes/ocr.py",
        "app/routes/health.py"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} NOT FOUND")
            all_exist = False
    
    return all_exist

def main():
    """Run all health checks"""
    print("=" * 60)
    print("🏥 Backend Health Check")
    print("=" * 60)
    print()
    
    # Change to backend directory if needed
    if Path("backend").exists():
        os.chdir("backend")
        print("📁 Changed to backend directory\n")
    
    print("1️⃣  Checking Python version...")
    py_ok = check_python_version()
    print()
    
    print("2️⃣  Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("3️⃣  Checking environment configuration...")
    env_ok = check_env_file()
    print()
    
    print("4️⃣  Checking project structure...")
    struct_ok = check_project_structure()
    print()
    
    print("=" * 60)
    if py_ok and deps_ok and env_ok and struct_ok:
        print("✅ All checks passed! Backend is ready to run.")
        print("\n🚀 Start the server with:")
        print("   python main.py")
        print("\n📚 API Documentation will be at:")
        print("   http://localhost:8000/api/docs")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\n💡 Quick fixes:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Create .env file: copy .env.example .env")
        print("   3. Configure Modal URL in .env (see MODAL_DEPLOYMENT.md)")
    print("=" * 60)

if __name__ == "__main__":
    main()
