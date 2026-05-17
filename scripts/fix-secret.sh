#!/bin/bash
# Script to remove secret from git history

git filter-branch --force --tree-filter '
  if [ -f .env.example ]; then
    sed -i "s/GROQ_API_KEY=gsk_[a-zA-Z0-9]*/GROQ_API_KEY=\"your_groq_api_key_here\"/g" .env.example
  fi
' --prune-empty --tag-name-filter cat -- --all
