# AI Integration & Documentation Maintenance Guide

*Created by: GitHub Copilot (Claude Sonnet 4) - 2025-07-28*

## 🤖 AI Discovery Mechanisms

### **Standard AI Context Files Created**

1. **`.aicodex`** - Standard AI context file (emerging convention)
2. **`.ai-context.yaml`** - YAML format for structured data
3. **`PROJECT_SUMMARY_AI.json`** - Comprehensive structured metadata
4. **`PROJECT_SUMMARY.md`** - Human-readable overview

### **Discovery Methods**

| AI Platform | Discovery Method | Files Found |
|-------------|------------------|-------------|
| **GitHub Copilot** | Workspace scanning | `.aicodex`, `README.md`, `*.json` |
| **Claude/ChatGPT** | Manual reference | All files when explicitly mentioned |
| **VS Code Copilot** | Active file context | Files in current workspace |
| **Custom AI Tools** | File pattern matching | `.ai-*`, `*_AI.*`, `PROJECT_*` |

## 🔄 Automated Maintenance System

### **1. Local Development**

**Pre-commit Hook**: Automatically updates docs before each commit
```bash
# Setup (run once)
cp scripts/git/pre_commit_doc_update.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Now documentation auto-updates on every commit!
```

**Manual Updates**:
```bash
# Update all documentation
python tools/documentation_maintainer.py

# Check current status
python tools/documentation_maintainer.py --check
```

### **2. GitHub Actions**

**Automated Workflow**: `.github/workflows/auto-update-docs.yml`
- **Triggers**: Push to main/develop, PRs, weekly schedule
- **Actions**: Updates timestamps, metadata, project structure
- **Result**: Auto-commits updated documentation

### **3. Smart Git Integration**

**Enhanced Quick Commit**: `scripts/git/quick_commit.py`
- Automatically runs documentation updates
- Includes updated docs in commits
- Security scanning for all changes

## 📋 What Gets Updated Automatically

### **Timestamps & Metadata**
- Last updated dates in all files
- Git commit information
- Branch status and recent changes

### **Project Structure**
- File listings and organization
- Code statistics (lines of code)
- New tools and scripts discovery

### **Development Context**
- Current automation tools
- Security requirements updates
- New development patterns

## 🎯 AI Assistant Integration

### **For Human Developers**

**Quick Reference Commands**:
```bash
# Get project context for AI
cat .aicodex

# Get comprehensive AI data
cat PROJECT_SUMMARY_AI.json

# Get contributor guidelines
cat CONTRIBUTOR_QUICK_REFERENCE.md
```

### **For AI Assistants**

**Context Loading**:
1. Primary: Load `.aicodex` for quick context
2. Detailed: Reference `PROJECT_SUMMARY_AI.json`
3. Human docs: Use `PROJECT_SUMMARY.md`
4. Guidelines: Check `CONTRIBUTOR_QUICK_REFERENCE.md`

**Example AI Prompt**:
```
Reference the project context in .aicodex and PROJECT_SUMMARY_AI.json 
when working on this codebase. Follow the security guidelines and 
development standards outlined in these files.
```

## 🔧 Customization & Extension

### **Adding New Context**

**For New Automation Tools**:
```python
# In tools/documentation_maintainer.py
def _discover_new_tools(self):
    # Add logic to discover new automation
    pass
```

**For New AI Platforms**:
```bash
# Create platform-specific context file
echo "platform_specific_data" > .ai-context-platform.yaml
```

### **Custom Update Triggers**

**On File Changes**:
```bash
# Add to .git/hooks/post-merge
python tools/documentation_maintainer.py --auto
```

**On Version Tags**:
```yaml
# In GitHub Actions
on:
  push:
    tags:
      - 'v*'
```

## 📊 Monitoring & Verification

### **Check Documentation Status**

```bash
# Quick status check
python tools/documentation_maintainer.py --check

# Verify AI context files exist
ls -la .ai* PROJECT_SUMMARY*

# Check last update timestamps
grep -r "last_updated\|Last Updated" .ai* PROJECT_*
```

### **GitHub Actions Monitoring**

- Check Actions tab for update workflow runs
- Review commit history for auto-update commits
- Monitor for any failed documentation updates

## 🚀 Best Practices

### **For Project Maintainers**

1. **Regular Reviews**: Check AI context accuracy monthly
2. **Update Triggers**: Run maintenance after major changes
3. **Version Control**: Tag documentation updates in releases
4. **Quality Checks**: Verify AI suggestions match project standards

### **For Contributors**

1. **Use Automation**: Always use smart git tools
2. **Check Context**: Reference AI files when using assistants
3. **Update Guidelines**: Suggest improvements to AI context
4. **Security First**: Never bypass security automation

### **For AI Assistants**

1. **Load Context**: Always check for `.aicodex` and AI summary files
2. **Follow Standards**: Adhere to project-specific guidelines
3. **Security Aware**: Respect sensitive data patterns
4. **Attribution**: Add timestamps to AI-generated code

## 🔮 Future Enhancements

### **Planned Improvements**

- **Smart Context Selection**: AI chooses relevant context sections
- **Cross-Project Learning**: Share patterns across repositories
- **Real-time Updates**: Live documentation synchronization
- **AI Training Data**: Generate training examples from code patterns

### **Integration Opportunities**

- **IDE Extensions**: Direct AI context loading in editors
- **CI/CD Integration**: Documentation quality gates
- **Team Collaboration**: Shared AI context across team members

---

## 📞 Support & Troubleshooting

### **Common Issues**

**Documentation Not Updating**:
```bash
# Check maintenance script
python tools/documentation_maintainer.py --check

# Verify git hooks
ls -la .git/hooks/

# Check GitHub Actions
# Visit: https://github.com/Wootehfook/letterboxd-friend-check/actions
```

**AI Not Finding Context**:
1. Verify `.aicodex` file exists
2. Check file permissions (should be readable)
3. Reference files explicitly in AI prompts
4. Use semantic search tool to find context

**Automation Failures**:
```bash
# Check script logs
python tools/documentation_maintainer.py 2>&1 | tee doc-update.log

# Verify file permissions
chmod +x scripts/git/*.py tools/*.py
```

---

*This system ensures AI assistants always have current, accurate context about the project while minimizing manual maintenance overhead.*
