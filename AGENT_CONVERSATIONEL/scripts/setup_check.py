#!/usr/bin/env python3
"""
Quick Setup Validation Script - Test World Bank chatbot installation
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version >= 3.11"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """Check required packages"""
    required = [
        "fastapi",
        "uvicorn",
        "langchain",
        "openai",
        "faiss-cpu",
        "pydantic"
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"✅ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"❌ {pkg} missing")
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing)}")
        return False
    
    return True

def check_files():
    """Check critical files"""
    required_files = [
        "config.json",
        "app.py",
        "core/config_loader.py",
        "core/embeddings_loader.py",
        "core/llm_handler.py",
        "core/agent_orchestrator.py",
        "templates/base.html",
        "static/app.js"
    ]
    
    base_dir = Path(__file__).parent
    missing = []
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            missing.append(file_path)
            print(f"❌ {file_path} missing")
    
    if missing:
        return False
    
    return True

def check_env():
    """Check environment variables"""
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY set ({api_key[:10]}...)")
    else:
        print("⚠️  OPENAI_API_KEY not set (required to run)")
        print("   Set it: export OPENAI_API_KEY=sk-your-key")
        return False
    
    return True

def check_data():
    """Check data files"""
    base_dir = Path(__file__).parent
    data_file = base_dir / "data" / "world_bank_data.json"
    
    if data_file.exists():
        size = data_file.stat().st_size / (1024 * 1024)  # MB
        print(f"✅ world_bank_data.json exists ({size:.2f} MB)")
    else:
        print("⚠️  data/world_bank_data.json not found")
        print("   Run extraction: cd EXTRACTION_WB && python collector.py")
        return False
    
    return True

def main():
    """Run all checks"""
    print("=" * 50)
    print("🔍 World Bank Chatbot - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Files", check_files),
        ("Environment Variables", check_env),
        ("Data Files", check_data)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\n🚀 Start the chatbot:")
        print("   python app.py")
        print("   Then open: http://localhost:8000")
    else:
        print("❌ SOME CHECKS FAILED")
        print("   Fix issues above before running")
    print("=" * 50)

if __name__ == "__main__":
    main()
