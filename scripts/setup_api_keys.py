#!/usr/bin/env python3
"""
API Key Setup Script for SAFEPATH
Guides you through getting all required API keys
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with API key placeholders"""
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    
    print("🔧 Creating .env file for API keys...")
    
    env_content = """# SAFEPATH Environment Variables
# Database
DATABASE_URL=postgresql://username:password@localhost/safepath

# REQUIRED API Keys
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
LETTA_API_KEY=your_letta_token_here

# OPTIONAL API Keys (uncomment if you want to use them)
# GOOGLE_MAPS_API_KEY=your_google_maps_token_here
# CRIMEOMETER_API_KEY=your_crimeometer_token_here
# OPENWEATHER_API_KEY=your_openweather_token_here
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at {env_file}")
    return env_file

def show_api_key_instructions():
    """Display instructions for getting each API key"""
    
    print("\n" + "="*60)
    print("🔑 SAFEPATH API KEY SETUP GUIDE")
    print("="*60)
    
    # Required API Keys
    print("\n📋 REQUIRED API KEYS:")
    print("-" * 30)
    
    print("\n1. 🗺️  MAPBOX API KEY (REQUIRED)")
    print("   Purpose: Interactive maps, routing, geocoding")
    print("   Cost: FREE (50,000 requests/month)")
    print("   Steps:")
    print("   1. Go to: https://account.mapbox.com")
    print("   2. Sign up for free account")
    print("   3. Go to 'Access Tokens' section")
    print("   4. Copy your 'Default public token'")
    print("   5. Paste it in .env file as MAPBOX_ACCESS_TOKEN")
    
    print("\n2. 🧠 LETTA API KEY (REQUIRED)")
    print("   Purpose: User memory for saved locations")
    print("   Cost: FREE tier available")
    print("   Steps:")
    print("   1. Go to: https://letta.ai")
    print("   2. Sign up for free account")
    print("   3. Go to API section")
    print("   4. Generate API key")
    print("   5. Paste it in .env file as LETTA_API_KEY")
    
    # Optional API Keys
    print("\n📋 OPTIONAL API KEYS (For Enhanced Features):")
    print("-" * 50)
    
    print("\n3. 🗺️  GOOGLE MAPS API KEY (OPTIONAL)")
    print("   Purpose: Alternative to Mapbox")
    print("   Cost: $200/month free credit")
    print("   Steps:")
    print("   1. Go to: https://console.cloud.google.com")
    print("   2. Create new project")
    print("   3. Enable Maps JavaScript API")
    print("   4. Create credentials")
    print("   5. Copy API key")
    
    print("\n4. 🚨 CRIMEOMETER API KEY (OPTIONAL)")
    print("   Purpose: Premium crime data from 700+ cities")
    print("   Cost: $50-200/month")
    print("   Steps:")
    print("   1. Go to: https://www.crimeometer.com")
    print("   2. Sign up for account")
    print("   3. Choose subscription plan")
    print("   4. Get API key from dashboard")
    
    print("\n5. 🌤️  OPENWEATHER API KEY (OPTIONAL)")
    print("   Purpose: Weather conditions for route planning")
    print("   Cost: FREE (1,000 calls/day)")
    print("   Steps:")
    print("   1. Go to: https://openweathermap.org")
    print("   2. Sign up for free account")
    print("   3. Go to API keys section")
    print("   4. Copy your API key")

def test_api_keys():
    """Test if API keys are working"""
    print("\n🧪 Testing API Keys...")
    
    # Check if .env file exists
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Run setup first.")
        return
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    # Test Mapbox
    mapbox_key = os.getenv('MAPBOX_ACCESS_TOKEN')
    if mapbox_key and mapbox_key != 'your_mapbox_token_here':
        print("✅ Mapbox API key configured")
    else:
        print("❌ Mapbox API key not configured")
    
    # Test Letta
    letta_key = os.getenv('LETTA_API_KEY')
    if letta_key and letta_key != 'your_letta_token_here':
        print("✅ Letta API key configured")
    else:
        print("❌ Letta API key not configured")
    
    # Test optional keys
    google_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if google_key and google_key != 'your_google_maps_token_here':
        print("✅ Google Maps API key configured")
    
    crimeometer_key = os.getenv('CRIMEOMETER_API_KEY')
    if crimeometer_key and crimeometer_key != 'your_crimeometer_token_here':
        print("✅ CrimeoMeter API key configured")
    
    openweather_key = os.getenv('OPENWEATHER_API_KEY')
    if openweather_key and openweather_key != 'your_openweather_token_here':
        print("✅ OpenWeather API key configured")

def show_minimum_setup():
    """Show minimum setup for MVP"""
    print("\n🚀 MINIMUM SETUP FOR MVP:")
    print("-" * 30)
    print("To get started quickly, you only need:")
    print("1. Mapbox API key (FREE)")
    print("2. Letta API key (FREE)")
    print("3. San Francisco Police API (NO KEY NEEDED)")
    print("4. Berkeley PD API (NO KEY NEEDED)")
    print("\nTotal cost: $0/month")

def show_production_setup():
    """Show production setup with all features"""
    print("\n🏭 PRODUCTION SETUP:")
    print("-" * 25)
    print("For full production features:")
    print("1. Mapbox API key (FREE tier)")
    print("2. Letta API key (FREE tier)")
    print("3. CrimeoMeter API key ($50-200/month)")
    print("4. OpenWeather API key (FREE)")
    print("\nTotal cost: $50-200/month")

def main():
    """Main setup function"""
    print("🚀 SAFEPATH API Key Setup")
    print("=" * 40)
    
    # Create .env file
    env_file = create_env_file()
    
    # Show instructions
    show_api_key_instructions()
    
    # Show setup options
    show_minimum_setup()
    show_production_setup()
    
    # Test keys if available
    try:
        test_api_keys()
    except ImportError:
        print("\n⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Get your API keys from the links above")
    print("2. Edit backend/.env file with your keys")
    print("3. Run: python backend/main.py")
    print("4. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
