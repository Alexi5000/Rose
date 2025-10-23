# Branch Protection Rules Setup Guide

This guide provides step-by-step instructions for configuring branch protection rules for the Rose AI Companion repository.

## Prerequisites

- Repository admin access
- GitHub repository with `main` and `develop` branches
- CI/CD workflows configured (see `.github/workflows/`)

## Branch Protection Rules Overview

We use a two-branch strategy:
- **`main`**: Production branch with strict protection
- **`develop`**: Development integration branch with moderate protection

## Setup Instructions

### 1. Access Branch Protection Settings

1. Navigate to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Branches** under "Code and automation"
4. Click **Add branch protection rule**

### 2. Configure `main` Branch Protection

Create a new branch protection rule with the following settings:

#### Branch Name Pattern
```
main
```

#### Protection Settings

**Require a pull request before merging**
- ✅ Enable this option
- **Required approvals**: 1
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ⬜ Require review from Code Owners (optional, enable if using CODEOWNERS)
- ⬜ Restrict who can dismiss pull request reviews (optional)
- ⬜ Allow specified actors to bypass required pull requests (leave unchecked)
- ⬜ Require approval of the most recent reviewable push

**Require status checks to pass before merging**
- ✅ Enable this option
- ✅ Require branches to be up to date before merging
- **Required status checks** (add these as they become available from workflows):
  - `code-quality` (from ci-cd.yml)
  - `unit-tests` (from ci-cd.yml)
  - `smoke-tests` (from ci-cd.yml)

**Require conversation resolution before merging**
- ✅ Enable this option (recommended)

**Require signed commits**
- ⬜ Optional - enable if your team uses commit signing

**Require linear history**
- ✅ Enable this option (prevents merge commits, enforces rebase or squash)

**Require deployments to succeed before merging**
- ⬜ Leave unchecked (we handle deployment after merge)

**Lock branch**
- ⬜ Leave unchecked

**Do not allow bypassing the above settings**
- ✅ Enable this option (enforces rules for admins too)

**Restrict who can push to matching branches**
- ⬜ Leave unchecked (or configure specific users/teams if needed)

**Allow force pushes**
- ⬜ Leave unchecked (prevent force pushes)

**Allow deletions**
- ⬜ Leave unchecked (prevent branch deletion)

### 3. Configure `develop` Branch Protection

Create another branch protection rule with the following settings:

#### Branch Name Pattern
```
develop
```

#### Protection Settings

**Require a pull request before merging**
- ✅ Enable this option
- **Required approvals**: 1
- ⬜ Dismiss stale pull request approvals when new commits are pushed (more flexible for develop)
- ⬜ Require review from Code Owners (optional)

**Require status checks to pass before merging**
- ✅ Enable this option
- ⬜ Require branches to be up to date before merging (more flexible for develop)
- **Required status checks**:
  - `code-quality` (from ci-cd.yml)
  - `unit-tests` (from ci-cd.yml)

**Require conversation resolution before merging**
- ✅ Enable this option (recommended)

**Require signed commits**
- ⬜ Optional

**Require linear history**
- ⬜ Leave unchecked (allow merge commits in develop)

**Do not allow bypassing the above settings**
- ⬜ Leave unchecked (allow admins to bypass for develop)

**Allow force pushes**
- ⬜ Leave unchecked

**Allow deletions**
- ⬜ Leave unchecked

### 4. Verify Configuration

After setting up both rules:

1. Navigate to **Settings** → **Branches**
2. Verify both `main` and `develop` rules are listed
3. Click on each rule to review settings
4. Make any necessary adjustments

### 5. Test Branch Protection

Test the configuration by:

1. Creating a test feature branch from `develop`
2. Making a small change
3. Opening a pull request to `develop`
4. Verify that:
   - CI checks run automatically
   - Merge is blocked until checks pass
   - At least one approval is required
5. Repeat test for PR from `develop` to `main`

## Status Check Names Reference

The following status checks will be available once CI/CD workflows are implemented:

### From `ci-cd.yml` workflow:
- `code-quality` - Linting and formatting checks
- `unit-tests` - Unit test execution with coverage
- `integration-tests` - Integration test execution (optional)
- `smoke-tests` - Pre-deployment smoke tests

### From `pr-validation.yml` workflow:
- `pr-checks` - PR title and format validation

## Updating Status Checks

As you add or modify workflows, you may need to update the required status checks:

1. Go to **Settings** → **Branches**
2. Click **Edit** on the branch protection rule
3. Scroll to **Require status checks to pass before merging**
4. Search for and add new status check names
5. Click **Save changes**

## Troubleshooting

### Status checks not appearing
- Ensure the workflow has run at least once
- Check that the job names in your workflow files match the status check names
- Wait a few minutes for GitHub to register the new checks

### Unable to merge despite passing checks
- Verify all required status checks are passing
- Check if branch is up to date (if required)
- Ensure you have the required number of approvals

### Accidentally locked out of branch
- If you enabled "Do not allow bypassing" and need to make emergency changes
- Temporarily disable the branch protection rule
- Make your changes
- Re-enable the protection rule

## CODEOWNERS Configuration

The `.github/CODEOWNERS` file has been created with default ownership patterns. To customize:

1. Edit `.github/CODEOWNERS`
2. Replace `@OWNER_USERNAME` with actual GitHub usernames or team names
3. Add or modify path patterns as needed
4. Commit and push changes

Example CODEOWNERS patterns:
```
# Single owner
/src/ai_companion/ @username

# Multiple owners
/docs/ @username1 @username2

# Team ownership
/frontend/ @org/frontend-team

# Wildcard patterns
*.md @org/docs-team
```

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Status Checks Documentation](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

## Notes

- Branch protection rules are configured through the GitHub web interface and cannot be automated via git commands
- These settings require repository admin permissions
- Changes to branch protection rules take effect immediately
- Consider your team's workflow when deciding on strictness levels
