#!/usr/bin/env python3
"""
Script to help update the Mapbox API token in the frontend .env file
"""

import os
import sys

def update_mapbox_token():
    """Update the Mapbox token in the frontend .env file"""
    
    print("🗺️  Mapbox API Token Updater")
    print("=" * 40)
    
    # Get the new token from user
    print("\nTo get your Mapbox API token:")
    print("1. Go to: https://account.mapbox.com/access-tokens/")
    print("2. Sign up/login to Mapbox")
    print("3. Copy your 'Default public token'")
    print("4. It should look like: pk.eyJ1IjoieW91cnVzZXJuYW1lIiwiYSI6ImNqZXhhbXBsZSJ9.actual_token")
    
    print("\n" + "=" * 40)
    new_token = input("Enter your Mapbox API token: ").strip()
    
    if not new_token:
        print("❌ No token provided. Exiting.")
        return False
    
    if not new_token.startswith('pk.'):
        print("⚠️  Warning: Token doesn't start with 'pk.' - this might not be correct.")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            return False
    
    # Update the .env file
    env_file = os.path.join('frontend', '.env')
    
    if not os.path.exists(env_file):
        print(f"❌ .env file not found at {env_file}")
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update the Mapbox token line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('REACT_APP_MAPBOX_TOKEN='):
                lines[i] = f'REACT_APP_MAPBOX_TOKEN={new_token}\n'
                updated = True
                break
        
        if not updated:
            # Add the token if it doesn't exist
            lines.append(f'REACT_APP_MAPBOX_TOKEN={new_token}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Successfully updated Mapbox token in {env_file}")
        print(f"   New token: {new_token[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def verify_token():
    """Verify the current token in .env file"""
    env_file = os.path.join('frontend', '.env')
    
    if not os.path.exists(env_file):
        print(f"❌ .env file not found at {env_file}")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        if 'REACT_APP_MAPBOX_TOKEN=' in content:
            lines = content.split('\n')
            for line in lines:
                if line.startswith('REACT_APP_MAPBOX_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    print(f"Current Mapbox token: {token}")
                    
                    if token.startswith('pk.') and 'example' not in token:
                        print("✅ Token looks valid!")
                        return True
                    else:
                        print("❌ Token appears to be a placeholder or invalid")
                        return False
        else:
            print("❌ No Mapbox token found in .env file")
            return False
            
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_token()
    else:
        update_mapbox_token()
