# Git Safe - Automated Pre-Commit Safety System

🛡️ **Prevent accidental commits** of unwanted files and ensure code quality before pushing to repositories.

## 🚀 Quick Start

1. **Setup the system:**
   ```bash
   python setup_git_safe.py
   ```

2. **Use safe git operations:**
   ```bash
   # Instead of: git add .
   python git_safe.py add .
   
   # Instead of: git commit -m "message"  
   python git_safe.py commit -m "message"
   
   # Instead of: git push
   python git_safe.py push
   ```

3. **Run checks manually:**
   ```bash
   python pre_commit_check.py --fix --verbose
   ```

## 📋 What It Checks

### 🚫 **Forbidden Files** (Auto-blocked)
- Temporary files: `*.tmp`, `*.log`, `*.cache`, `*.swp`
- Security reports: `bandit-*.json`, `safety-*.json`, `trufflehog-*.json`
- Cache directories: `__pycache__/`, `.pytest_cache/`
- Large files (>10MB) with warnings

### 🎨 **Code Quality Analysis**
- Detects cosmetic-only changes (formatting, quotes, whitespace)
- Identifies functional vs. style-only modifications
- Suggests appropriate commit categorization

### 📊 **Git Status Validation**
- Checks for staged vs. unstaged changes
- Warns about mixed states in same files
- Validates commit readiness

## 🔧 Usage Options

### 1. **Direct Scripts** (Recommended)
```bash
# Run pre-commit checks only
python pre_commit_check.py
python pre_commit_check.py --fix          # Auto-fix issues
python pre_commit_check.py --verbose      # Detailed output

# Safe git operations
python git_safe.py add .
python git_safe.py commit -m "fix: security issues"
python git_safe.py push
```

### 2. **PowerShell Wrapper** (Windows)
```powershell
.\\git-safe.ps1 add .
.\\git-safe.ps1 commit -m "feat: new feature"
.\\git-safe.ps1 push
```

### 3. **Git Aliases** (Global)
```bash
# Setup once
python setup_git_safe.py

# Then use
git safe-add .
git safe-commit -m "message"
git safe-push
git safe-check
```

### 4. **Shell Functions** 
Add to your `~/.bashrc`, `~/.zshrc`, or PowerShell `$PROFILE`:

**Bash/Zsh:**
```bash
source git_safe_functions.sh
gadd .        # Safe git add
gcommit -m "" # Safe git commit  
gpush         # Safe git push
gcheck        # Run checks only
```

**PowerShell:**
```powershell
. .\\git_safe_functions.ps1
gadd .
gcommit -m "message"
gpush
gcheck
```

## 🎯 Exit Codes

| Code | Status | Action |
|------|--------|--------|
| `0` | ✅ Clean | Safe to commit |
| `1` | ⚠️ Warnings | Review before committing |
| `2` | ❌ Critical | Do not commit |

## 🔍 Example Output

```
🚀 Running pre-commit checks...
==================================================
ℹ️  Found 3 modified files
ℹ️  Checking for forbidden files...
✅ No forbidden files found
ℹ️  Analyzing change types...
⚠️  Cosmetic-only changes detected in: ['tests/test_letterboxd.py']
⚠️  Consider reviewing if these should be committed
ℹ️  Functional changes detected in: ['letterboxd_friend_check/data/database.py']
ℹ️  Checking commit readiness...
ℹ️  Suggested commit prefix: 🔒 Security fixes, 🎨 Code formatting

==================================================
📊 PRE-COMMIT CHECK SUMMARY
==================================================
⚠️  Warnings: 1
   • Cosmetic-only changes detected in: ['tests/test_letterboxd.py']

⚠️  CAUTION: Review warnings before committing
```

## 🛠️ Configuration

### Adding Custom Forbidden Patterns
Edit `pre_commit_check.py` and modify the `forbidden_patterns` list:

```python
self.forbidden_patterns = [
    "*.tmp", "*.log", "*.cache",
    "bandit-*.json",
    "my-custom-*.temp",  # Add your patterns
]
```

### Customizing Cosmetic Indicators
Modify the `cosmetic_indicators` list to detect style-only changes:

```python
self.cosmetic_indicators = [
    "single quotes to double quotes",
    "trailing whitespace", 
    "your-custom-indicator",  # Add custom patterns
]
```

## 🎨 Integration Examples

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
python pre_commit_check.py
exit $?
```

### CI/CD Pipeline
```yaml
# GitHub Actions
- name: Pre-commit Safety Check
  run: python pre_commit_check.py --verbose
```

### Makefile Integration
```makefile
# Include generated targets
include Makefile.git-safe

deploy: git-check
	@echo "Safe to deploy!"
```

## 📝 Files Created

After running `setup_git_safe.py`:

- `pre_commit_check.py` - Main checker script ⭐
- `git_safe.py` - Safe git wrapper ⭐  
- `git-safe.ps1` - PowerShell wrapper
- `git_safe_functions.sh` - Bash/Zsh functions
- `git_safe_functions.ps1` - PowerShell functions
- `Makefile.git-safe` - Make targets

## 🔒 Security Benefits

1. **Prevents Credential Leaks**: Blocks security report files
2. **Avoids Bloat**: Stops large files and temporary files
3. **Code Quality**: Separates functional from cosmetic changes
4. **Audit Trail**: Clear commit categorization
5. **Team Safety**: Consistent checks across team members

## 🆘 Troubleshooting

**Issue**: `pre_commit_check.py not found`  
**Solution**: Run from repository root directory

**Issue**: Permission denied on PowerShell script  
**Solution**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Issue**: Git aliases not working  
**Solution**: Re-run `python setup_git_safe.py`

## 🎯 Best Practices

1. **Always use safe commands** for `add .`, `commit`, and `push`
2. **Review warnings** before proceeding with commits
3. **Use `--fix` mode** for automatic issue resolution
4. **Separate commits** for functional vs. cosmetic changes
5. **Run checks early** during development, not just before pushing

---

**Next time you want to commit**, simply run:
```bash
python git_safe.py add .
```

The system will automatically check for issues and guide you to a clean commit! 🎉
