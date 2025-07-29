# Contributor Quick Reference Guide

## 🚀 Essential Commands

### Daily Development
```bash
# Start work
git checkout -b feature/your-feature-name

# Make changes and commit safely
python scripts/git/quick_commit.py

# Run security scan
python scripts/security/security_scan.py

# Check project status
python tools/project_status_checker.py

# Run tests
pytest
```

### Before Submitting PR
```bash
# Format code
black . --line-length 100

# Run linting
pylint *.py letterboxd_friend_check/ scripts/ tools/

# Security check
python scripts/security/security_scan.py

# Final commit
python scripts/git/quick_commit.py
```

## 📁 Where Things Go

| What | Where | Example |
|------|-------|---------|
| Core app changes | Root or `letterboxd_friend_check/` | `LBoxFriendCheck.py` |
| New features | `letterboxd_friend_check/` package | `letterboxd_friend_check/features/` |
| Build scripts | `scripts/build/` | `scripts/build/deploy.py` |
| Security tools | `scripts/security/` | `scripts/security/scan_deps.py` |
| Dev utilities | `tools/` | `tools/data_migration.py` |
| Tests | `tests/` | `tests/test_new_feature.py` |
| Documentation | Root or `docs/` | `FEATURE_GUIDE.md` |

## ⚠️ Never Commit These

- `Cookie.json` - User authentication
- `*.db` or `*.sqlite3` - User data
- `config.json` - Personal configuration
- `security_report*.txt` - Scan results
- `*_ENABLED.md` - Dev notes
- Personal test data files

## 🎯 Code Standards Checklist

- [ ] Max line length: 100 characters
- [ ] Docstrings: Google format
- [ ] Type hints: Added for all functions
- [ ] AI attribution: Added timestamp comment
- [ ] Security: No hardcoded secrets
- [ ] Tests: Added for new code
- [ ] Documentation: Updated if needed

## 🔒 Security Checklist

- [ ] No API keys in code
- [ ] No personal data in commits
- [ ] URL parsing uses `startswith()`
- [ ] Input validation added
- [ ] Error messages don't leak info
- [ ] Ran security scanner

## 📝 Commit Message Format

```
🏷️ Type: Brief description

Detailed explanation if needed.

Related: #issue-number
```

Types:
- 🐛 Fix: Bug fixes
- ✨ Feature: New features
- 📚 Docs: Documentation
- 🎨 Style: Formatting only
- ♻️ Refactor: Code restructuring
- 🧪 Test: Test additions
- 🔒 Security: Security fixes
- ⚡ Perf: Performance improvements

## 🆘 Getting Help

1. Check existing documentation
2. Use AI bridge: `python tools/github_issues_bridge.py --search "your question"`
3. Create an issue with "question" label
4. Reference this guide and PROJECT_SUMMARY.md

## 🤖 AI Development Tips

When using AI assistants:
1. Reference #codebase for context
2. Mention specific guidelines from this project
3. Ask for security review of generated code
4. Request tests with new features
5. Verify no sensitive data in examples

---
*Remember: Security and code quality are not optional - they're built into our workflow!*
