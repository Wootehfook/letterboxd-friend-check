# GitHub Actions Workflow Security Guidelines

*Last Updated: July 28, 2025*  
*Project: Letterboxd Friend Check*  
*Author: Woo T. Fook (AI-Enhanced Development)*

## 🛡️ Security Best Practices for GitHub Actions

### **1. Always Define Explicit Permissions**

**❌ Insecure (Default permissions):**
```yaml
name: My Workflow
# No permissions block = ALL permissions granted (DANGEROUS)
```

**✅ Secure (Minimal permissions):**
```yaml
name: My Workflow
permissions:
  contents: read  # Only read repository contents
  # Add only what you actually need
```

### **2. Principle of Least Privilege**

Grant only the minimum permissions required:

```yaml
# For reading code only
permissions:
  contents: read

# For updating documentation
permissions:
  contents: write
  pull-requests: read

# For creating issues/PRs
permissions:
  contents: read
  issues: write
  pull-requests: write

# For security scanning
permissions:
  contents: read
  security-events: write
  actions: read
```

### **3. Common Permission Requirements**

| Action | Required Permissions | Use Case |
|--------|---------------------|----------|
| Read code | `contents: read` | Linting, testing |
| Commit changes | `contents: write` | Auto-updates, fixes |
| Create issues | `issues: write` | Bug reporting |
| Security scanning | `security-events: write` | CodeQL, SARIF |
| Package publishing | `packages: write` | NPM, Docker |
| Status checks | `checks: write` | Test results |

### **4. Project-Specific Workflows**

#### **Documentation Workflows**
```yaml
permissions:
  contents: write  # To commit doc updates
  pull-requests: read  # To read PR context
```

#### **Security Scanning**
```yaml
permissions:
  contents: read
  security-events: write  # Upload SARIF results
  actions: read  # Read workflow info
  pull-requests: read  # PR context
```

#### **Testing Workflows**
```yaml
permissions:
  contents: read  # Read source code only
  pull-requests: read  # PR context
  checks: write  # Write test results
```

#### **Code Quality Workflows**
```yaml
permissions:
  contents: read  # Read source code
  pull-requests: read  # PR context
  checks: write  # Write quality results
```

### **5. Security Considerations**

#### **Token Scope Limitation**
- Use `${{ secrets.GITHUB_TOKEN }}` for most operations
- Create Personal Access Tokens only when necessary
- Store sensitive tokens in repository secrets
- Never hardcode tokens in workflow files

#### **Dependency Security**
- Pin action versions: `uses: actions/checkout@v4` (not `@main`)
- Review third-party actions before use
- Use official actions when possible
- Regularly update pinned versions

#### **Environment Protection**
```yaml
jobs:
  deploy:
    environment: production  # Requires approval
    permissions:
      contents: write
```

### **6. Audit Checklist**

Before merging any workflow:

- [ ] **Permissions defined explicitly**
- [ ] **Minimal permissions granted**
- [ ] **Actions pinned to specific versions**
- [ ] **No hardcoded secrets in workflow**
- [ ] **Appropriate environment protections**
- [ ] **Clear documentation of why permissions are needed**
- [ ] **Comments explaining security rationale**

### **7. Current Project Workflow Security Status**

#### **✅ Secure Workflows:**
- `tests.yml` - Minimal read permissions for testing
- `security.yml` - Appropriate permissions for security scanning
- `code-quality.yml` - Read permissions with check writing
- `auto-update-docs.yml` - Write permissions for documentation updates

#### **🔍 Security Features Implemented:**
- **Explicit permissions** on all workflows
- **Pinned action versions** (v4, not @main)
- **Scoped tokens** using GITHUB_TOKEN
- **Environment-specific protections**
- **Security scanning automation**

### **8. Example: Secure Documentation Workflow**

```yaml
name: 📚 Update Documentation
permissions:
  contents: write  # Required: commit doc updates
  pull-requests: read  # Required: read PR context
  
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    
jobs:
  update-docs:
    runs-on: ubuntu-latest
    # IMPORTANT: Only auto-update on pushes, not PRs
    if: github.event_name != 'pull_request'
    steps:
    - uses: actions/checkout@v4  # Pinned version
      with:
        token: ${{ secrets.GITHUB_TOKEN }}  # Scoped token
    
    - name: Update docs
      run: python scripts/update_docs.py
      
    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add .
        git commit -m "docs: auto-update" || exit 0
        # Use git push instead of action to avoid ref issues
        git push origin HEAD:${{ github.ref_name }}
        
  validate-docs:
    runs-on: ubuntu-latest
    # IMPORTANT: Only validate on PRs, don't push
    if: github.event_name == 'pull_request'
    steps:
    - uses: actions/checkout@v4
      with:
        ref: ${{ github.head_ref }}  # PR branch
    
    - name: Validate docs
      run: python scripts/validate_docs.py
```

### **9. Monitoring & Compliance**

#### **Regular Audits**
- Review workflow permissions quarterly
- Use GitHub's security tab to monitor
- Enable Dependabot for action updates
- Run CodeQL on workflow files

#### **Compliance Tools**
- **CodeQL**: Automatic security scanning
- **GitHub Advanced Security**: Repository insights
- **Dependabot**: Dependency updates
- **Branch protection**: Require status checks

### **10. Common GitHub Actions Issues & Fixes**

#### **❌ Problem: "deny updating a hidden ref" Error**
```
! [remote rejected] HEAD -> refs/pull/7/merge (deny updating a hidden ref)
```

**Root Cause**: Workflow trying to push to PR merge ref (read-only)

**✅ Solution**: Separate jobs for pushes vs PRs
```yaml
jobs:
  update-docs:
    if: github.event_name != 'pull_request'  # Only on pushes
    steps:
      - name: Push changes
        run: git push origin HEAD:${{ github.ref_name }}
  
  validate-docs:
    if: github.event_name == 'pull_request'  # Only on PRs
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}  # PR branch
```

#### **❌ Problem: Workflow Permissions Missing**
```
Error: Resource not accessible by integration
```

**Root Cause**: Missing or insufficient permissions

**✅ Solution**: Explicit minimal permissions
```yaml
permissions:
  contents: write  # For commits
  pull-requests: read  # For PR context
```

#### **❌ Problem: Action Version Vulnerabilities**
```
Warning: Using unpinned action version
```

**Root Cause**: Using floating tags like `@main`

**✅ Solution**: Pin to specific versions
```yaml
- uses: actions/checkout@v4  # Not @main
- uses: actions/setup-python@v4  # Not @latest
```

### **11. Security Incident Response**

If you discover a security issue in workflows:

1. **Immediate**: Disable the workflow
2. **Assessment**: Determine scope of exposure
3. **Fix**: Update permissions and security
4. **Audit**: Review all similar workflows
5. **Document**: Update this guide as needed
6. **Test**: Verify fix works correctly

### **11. Best Practices Summary**

#### **DO:**
- ✅ Always define explicit permissions
- ✅ Use minimal required permissions
- ✅ Pin action versions to specific releases
- ✅ Use scoped GITHUB_TOKEN
- ✅ Add security comments explaining choices
- ✅ Regular security audits

#### **DON'T:**
- ❌ Rely on default permissions
- ❌ Grant broad permissions unnecessarily
- ❌ Use unpinned action versions (@main)
- ❌ Hardcode secrets in workflows
- ❌ Skip security reviews
- ❌ Ignore security warnings

---

## 🚨 Security Contact

For security issues in workflows:
- Create issue with `security` label
- Review with project maintainers
- Document in security audit log

---

*These guidelines ensure our GitHub Actions follow security best practices and maintain the principle of least privilege.*
