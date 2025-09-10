#!/usr/bin/env python3
"""
Setup script to configure token pool for multi-agent system
This keeps tokens secure and never logs them
"""

import os
import sys
import json
from pathlib import Path
from getpass import getpass

sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')

from opsvi_mcp.servers.claude_code.token_pool import SecureTokenPool, token_pool_manager


def setup_tokens():
    """Setup tokens securely"""
    
    print("=" * 60)
    print("CLAUDE CODE TOKEN POOL SETUP")
    print("=" * 60)
    
    # Check existing tokens
    current_count = token_pool_manager.pool.get_token_count()
    print(f"\nCurrent tokens in pool: {current_count}")
    
    # Option to add tokens
    print("\nOptions:")
    print("1. Add tokens from environment variables")
    print("2. Add tokens interactively (secure input)")
    print("3. Load from encrypted file")
    print("4. Save current tokens (encrypted)")
    print("5. Test token rotation")
    print("6. Exit")
    
    choice = input("\nChoice (1-6): ").strip()
    
    if choice == "1":
        # Set environment variables for the 3 tokens
        # NOTE: In production, these would be set securely, not in code
        tokens_to_add = []
        
        # Check for CLAUDE_CODE_TOKEN1, CLAUDE_CODE_TOKEN2, CLAUDE_CODE_TOKEN3
        for i in range(1, 4):
            token_key = f"CLAUDE_CODE_TOKEN{i}"
            token = os.environ.get(token_key)
            if token:
                tokens_to_add.append(token)
                print(f"✓ Found {token_key}")
        
        if tokens_to_add:
            token_pool_manager.initialize_with_tokens(tokens_to_add)
            print(f"\n✅ Added {len(tokens_to_add)} tokens to pool")
        else:
            print("\n⚠️  No tokens found in environment")
            print("Set CLAUDE_CODE_TOKEN1, CLAUDE_CODE_TOKEN2, CLAUDE_CODE_TOKEN3")
    
    elif choice == "2":
        # Interactive secure input
        print("\nEnter tokens (press Enter with empty input to finish):")
        tokens_to_add = []
        i = 1
        while True:
            token = getpass(f"Token {i} (hidden): ").strip()
            if not token:
                break
            tokens_to_add.append(token)
            print(f"✓ Token {i} added (length: {len(token)})")
            i += 1
        
        if tokens_to_add:
            token_pool_manager.initialize_with_tokens(tokens_to_add)
            print(f"\n✅ Added {len(tokens_to_add)} tokens to pool")
    
    elif choice == "3":
        # Load from encrypted file
        filepath = Path.home() / ".claude" / "tokens.enc"
        if filepath.exists():
            token_pool_manager.pool.load_tokens_encrypted(filepath)
            print(f"✅ Loaded tokens from {filepath}")
        else:
            print(f"❌ File not found: {filepath}")
    
    elif choice == "4":
        # Save current tokens
        filepath = Path.home() / ".claude" / "tokens.enc"
        token_pool_manager.pool.save_tokens_encrypted(filepath)
        print(f"✅ Saved tokens to {filepath}")
    
    elif choice == "5":
        # Test rotation
        print("\nTesting token rotation:")
        if token_pool_manager.pool.get_token_count() > 0:
            for i in range(5):
                token, token_id = token_pool_manager.get_next_token()
                print(f"  Request {i+1}: Got {token_id}")
            
            print("\nUsage stats:")
            stats = token_pool_manager.get_pool_status()
            for token_id, usage in stats["usage_stats"].items():
                print(f"  {token_id}: {usage['usage_count']} uses")
        else:
            print("❌ No tokens in pool")
    
    print("\nToken pool ready for use!")
    print(f"Total tokens available: {token_pool_manager.pool.get_token_count()}")


def create_env_file():
    """Create environment file template"""
    
    env_file = Path.home() / ".claude" / "tokens.env"
    env_file.parent.mkdir(exist_ok=True)
    
    template = """# Claude Code Token Pool Configuration
# Add your tokens here (keep this file secure!)

# Primary token (optional)
#CLAUDE_CODE_TOKEN=sk-ant-...

# Additional tokens for parallel execution
#CLAUDE_CODE_TOKEN1=sk-ant-...
#CLAUDE_CODE_TOKEN2=sk-ant-...
#CLAUDE_CODE_TOKEN3=sk-ant-...

# Encryption key for token storage
#CLAUDE_ENCRYPTION_KEY=your-secure-key-here
"""
    
    if not env_file.exists():
        env_file.write_text(template)
        os.chmod(env_file, 0o600)
        print(f"Created template: {env_file}")
        print("Edit this file and add your tokens, then source it:")
        print(f"  source {env_file}")
    else:
        print(f"Environment file already exists: {env_file}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-env":
        create_env_file()
    else:
        setup_tokens()