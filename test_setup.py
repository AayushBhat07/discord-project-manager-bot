"""
Test script to verify API connectivity and configuration
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_configuration():
    """Test that all required configuration is present"""
    print("🔍 Testing Configuration...\n")
    
    required_vars = {
        'DISCORD_BOT_TOKEN': 'Discord bot token',
        'REPORT_CHANNEL_ID': 'Discord report channel ID',
        'WEBAPP_API_URL': 'Web app API URL'
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var:
                display_value = value[:10] + '...' + value[-5:] if len(value) > 15 else '***'
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: MISSING")
            missing.append(description)
    
    if missing:
        print(f"\n❌ Missing configuration:")
        for item in missing:
            print(f"  - {item}")
        return False
    
    print("\n✅ All required configuration present!")
    return True


def test_api_connectivity():
    """Test connectivity to the web app API"""
    print("\n🌐 Testing API Connectivity...\n")
    
    try:
        import requests
        api_url = os.getenv('WEBAPP_API_URL')
        
        # Try to connect to the API
        response = requests.get(f"{api_url}/discord/projects", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ API is reachable at {api_url}")
            data = response.json()
            print(f"📊 Found {len(data)} projects")
            return True
        else:
            print(f"⚠️  API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API at {api_url}")
        print("   Make sure the web app is running and the URL is correct")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_dependencies():
    """Test that all required dependencies are installed"""
    print("\n📦 Testing Dependencies...\n")
    
    dependencies = {
        'discord': 'discord.py',
        'requests': 'requests',
        'apscheduler': 'APScheduler',
        'pytz': 'pytz',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - MISSING")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing dependencies:")
        for item in missing:
            print(f"  - {item}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies installed!")
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("Discord Bot - Configuration Test")
    print("=" * 50 + "\n")
    
    results = []
    
    # Test dependencies first
    results.append(("Dependencies", test_dependencies()))
    
    # Test configuration
    results.append(("Configuration", test_configuration()))
    
    # Test API connectivity
    results.append(("API Connectivity", test_api_connectivity()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50 + "\n")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("\n✅ All tests passed! Bot is ready to run.")
        print("\nStart the bot with: python bot.py")
        print("Or use the start script: ./start.sh\n")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
