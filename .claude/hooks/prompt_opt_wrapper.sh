#!/bin/bash
# Wrapper to ensure OPENAI_API_KEY is passed to prompt_opt.py

# Try to get OPENAI_API_KEY from multiple sources
if [ -z "$OPENAI_API_KEY" ]; then
    # Try to source from .bashrc
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc
    fi
fi

if [ -z "$OPENAI_API_KEY" ]; then
    # Try to source from .profile
    if [ -f ~/.profile ]; then
        source ~/.profile
    fi
fi

if [ -z "$OPENAI_API_KEY" ]; then
    # Try to get from .env file if it exists
    if [ -f /home/opsvi/master_root/.env ]; then
        export $(grep OPENAI_API_KEY /home/opsvi/master_root/.env | xargs)
    fi
fi

# If still not found, try the parent shell environment
if [ -z "$OPENAI_API_KEY" ]; then
    export OPENAI_API_KEY=$(printenv OPENAI_API_KEY 2>/dev/null || echo "")
fi

# Now run the Python script with the environment variable
exec /home/opsvi/miniconda/bin/python /home/opsvi/master_root/.claude/hooks/prompt_opt.py
