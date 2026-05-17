# GitHub Push Protection Bypass Instructions

## Issue

GitHub's push protection has detected what it believes are secrets in the repository, specifically in the `.env.example` file. These are actually placeholder values, not real secrets.

## Detected "Secrets"

- **Groq API Key** in `.env.example` (line 6)
  - Commits: `b70eb18f2360201f51f4d8e14cb549a0e1259c80`, `0baef873652da7348cd432005fc8946b2d38e88c`
  - This is a placeholder value: `"your_groq_api_key_here"`

## Resolution Steps

### Option 1: Allow the Secret (Recommended for .env.example)

Since this is a placeholder in an example file and not a real secret:

1. Visit the bypass URL provided by GitHub:
   ```
   https://github.com/Alexi5000/Rose/security/secret-scanning/unblock-secret/34UI1XAgpfFKTc3MEnxTTDexCO8
   ```

2. Click "Allow secret" or "It's used in tests" (since it's an example file)

3. Retry the push:
   ```bash
   git push origin main
   git push origin main --tags
   git push origin develop
   ```

### Option 2: Modify the Placeholder Format

If you prefer not to bypass the protection, modify `.env.example` to use a different placeholder format:

```bash
# Change from:
GROQ_API_KEY="your_groq_api_key_here"

# To:
GROQ_API_KEY="gsk_YOUR_API_KEY_HERE"
# or
GROQ_API_KEY="<your-groq-api-key>"
```

Then commit and push again:
```bash
git add .env.example
git commit -m "chore: update API key placeholder format"
git push origin main
```

## Why This Happened

GitHub's secret scanning uses pattern matching to detect potential secrets. The placeholder text in `.env.example` matched the pattern for a Groq API key, triggering the push protection.

This is actually a good security feature - it prevents accidentally committing real secrets. In this case, it's a false positive since we're using placeholder text.

## Best Practices

For future `.env.example` files:

1. Use clearly fake placeholder formats:
   - `YOUR_API_KEY_HERE`
   - `<your-api-key>`
   - `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

2. Add comments indicating these are placeholders:
   ```bash
   # Replace with your actual API key
   GROQ_API_KEY="YOUR_KEY_HERE"
   ```

3. Never commit actual secrets to any file, including:
   - `.env` (should be in `.gitignore`)
   - Configuration files
   - Test files
   - Documentation

## After Resolution

Once you've bypassed the protection or modified the placeholders, complete the branch setup:

```bash
# Push main branch
git push origin main

# Push the v1.0.0 tag
git push origin v1.0.0

# Push develop branch
git push origin develop
```

Then proceed with configuring branch protection rules as described in `BRANCH_PROTECTION_SETUP.md`.
