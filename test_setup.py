"""
Test Setup Script for Gemini-based Text-to-SQL
Run this before starting the Streamlit app to verify everything is configured correctly.

Usage: python test_setup.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'networkx': 'networkx',
        'google.generativeai': 'google-generativeai'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"❌ {package_name} is NOT installed")
            missing.append(package_name)
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing)}")
        return False
    return True

def check_api_key():
    """Check if Google API key is configured"""
    api_key = GOOGLE_API_KEY
    
    if api_key:
        print(f"✓ GOOGLE_API_KEY is set (length: {len(api_key)})")
        
        # Try to validate the key format
        if api_key.startswith('AIza'):
            print("  ✓ API key format looks valid")
        else:
            print("  ⚠️  API key format looks unusual (Google keys usually start with 'AIza')")
        
        return True
    else:
        print("⚠️  GOOGLE_API_KEY not found in environment")
        print("   You can:")
        print("   1. Set it as environment variable: export GOOGLE_API_KEY='your-key'")
        print("   2. Create a .env file with: GOOGLE_API_KEY=your-key")
        print("   3. Enter it in the Streamlit UI sidebar")
        print("\n   Get your key from: https://makersuite.google.com/app/apikey")
        return False

def check_gemini_connection():
    """Try to connect to Gemini API"""
    api_key = GOOGLE_API_KEY

    if not api_key:
        print("⚠️  Cannot test Gemini connection without API key")
        return False

    try:
        from google import genai

        # Use the new Client API (REST-based, no gRPC issues)
        client = genai.Client(api_key=api_key)

        # Try a simple generation to verify connection
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Respond with exactly: 'Connected'"
        )

        if response and response.text:
            print("✓ Successfully connected to Gemini API")
            print(f"  Model: gemini-2.0-flash-exp")
            print(f"  Test response: {response.text.strip()}")
            return True
        else:
            print("⚠️  Connected but received empty response")
            return False

    except Exception as e:
        print(f"❌ Failed to connect to Gemini API: {str(e)}")
        error_msg = str(e).lower()
        if 'timeout' in error_msg or 'deadline' in error_msg:
            print("   The request timed out. This might be a network or firewall issue.")
        elif 'api key' in error_msg or 'invalid' in error_msg or '400' in error_msg:
            print("   The API key appears to be invalid or has insufficient permissions.")
        elif '429' in error_msg:
            print("   Rate limit exceeded. Wait a moment and try again.")
        elif '503' in error_msg or '502' in error_msg:
            print("   Gemini service is temporarily unavailable.")
        else:
            print("   Check your API key and internet connection")
        return False

def check_excel_file():
    """Check if Excel file exists"""
    excel_path = "AI_SampleDataStruture.xlsx"
    
    if Path(excel_path).exists():
        print(f"✓ Excel file found: {excel_path}")
        
        # Try to read it
        try:
            import pandas as pd
            
            # Check for required sheets
            required_sheets = [
                "Counterparty New",
                "Trade New", 
                "Concentration New",
                "Joins"
            ]
            
            xls = pd.ExcelFile(excel_path)
            found_sheets = xls.sheet_names
            
            print(f"  Available sheets: {', '.join(found_sheets)}")
            
            missing_sheets = [s for s in required_sheets if s not in found_sheets]
            if missing_sheets:
                print(f"  ❌ Missing sheets: {', '.join(missing_sheets)}")
                return False
            else:
                print(f"  ✓ All required sheets present")
                
                # Check if sheets have data
                for sheet in required_sheets:
                    df = pd.read_excel(excel_path, sheet_name=sheet)
                    print(f"    - {sheet}: {len(df)} rows")
                
                return True
                
        except Exception as e:
            print(f"  ❌ Error reading Excel file: {e}")
            return False
    else:
        print(f"❌ Excel file not found: {excel_path}")
        print("   Make sure the file is in the same directory as app.py")
        return False

def check_app_file():
    """Check if main app file exists"""
    if Path("app.py").exists():
        print("✓ app.py found")
        
        # Check if it imports the right modules
        try:
            with open("app.py", 'r') as f:
                content = f.read()
                
            if 'from google import genai' in content or 'google.generativeai' in content:
                print("  ✓ Gemini imports found")
            else:
                print("  ⚠️  Gemini imports not found - check if app.py is updated")
            
            if 'GeminiClient' in content:
                print("  ✓ GeminiClient class found")
            else:
                print("  ⚠️  GeminiClient class not found")
            
            return True
        except Exception as e:
            print(f"  ⚠️  Could not read app.py: {e}")
            return True  # File exists, just couldn't read it
    else:
        print("❌ app.py not found!")
        return False

def main():
    print("=" * 60)
    print("Text-to-SQL with Gemini - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("API Key", check_api_key),
        ("Excel File", check_excel_file),
        ("App File", check_app_file),
    ]
    
    # Only check Gemini connection if API key is set
    if GOOGLE_API_KEY:
        checks.append(("Gemini Connection", check_gemini_connection))
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        print("-" * 40)
        result = check_func()
        results.append(result)
        print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\n🚀 You're ready to run: streamlit run app.py")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nPlease fix the issues above before running the app.")
        
        if not GOOGLE_API_KEY:
            print("\n💡 Quick tip: Get your Google API key from:")
            print("   https://makersuite.google.com/app/apikey")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)