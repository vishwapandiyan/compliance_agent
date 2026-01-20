# 🔗 GitHub Integration Guide

## Overview

DevGuard now supports scanning files directly from GitHub repositories! You can analyze any public repository or private repository (with authentication) without manually downloading files.

---

## ✨ Features

- 🌐 **Public Repository Support**: Scan any public GitHub repository
- 🔐 **Private Repository Support**: Use Personal Access Token for private repos
- 📥 **Automatic Cloning**: Shallow clone (depth=1) for fast download
- 🗂️ **Recursive File Collection**: Scans all files in all subdirectories
- 🧹 **Auto Cleanup**: Temporary files removed after scan
- ⚡ **File Type Support**: All supported extensions (.py, .js, .ts, .json, .yml, etc.)

---

## 🚀 How to Use

### Method 1: Public Repository

1. **Open DevGuard** in your browser
2. **Select Input Method**: Choose **"GitHub Repository"**
3. **Enter Repository URL**:
   ```
   https://github.com/username/repository-name
   ```
4. **Start Scan**: Click "🔍 Start LLM-Powered Scan"

**Example URLs:**
```
https://github.com/torvalds/linux
https://github.com/django/django
https://github.com/nodejs/node
```

---

### Method 2: Private Repository

1. **Generate GitHub Personal Access Token**:
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: **`repo`** (Full control of private repositories)
   - Generate and copy the token (starts with `ghp_...`)

2. **In DevGuard**:
   - Select **"GitHub Repository"**
   - Enter your repository URL
   - Expand **"🔐 Advanced: Private Repository Access"**
   - Paste your token in the **"GitHub Personal Access Token"** field
   - Click "🔍 Start LLM-Powered Scan"

**Token Format:**
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📋 Supported File Types

The scanner automatically collects these file types:

| Language/Type | Extensions |
|--------------|-----------|
| Python | `.py` |
| JavaScript | `.js` |
| TypeScript | `.ts` |
| Configuration | `.json`, `.yml`, `.yaml`, `.env`, `.txt` |
| Documentation | `.md` |
| Java | `.java` |
| Go | `.go` |
| Rust | `.rs` |
| PHP | `.php` |
| Ruby | `.rb` |

---

## 🔍 How It Works

1. **Clone Repository**:
   ```python
   git.Repo.clone_from(github_url, temp_dir, depth=1)
   ```
   - Uses shallow clone (depth=1) for faster download
   - Only downloads latest commit

2. **Collect Files**:
   - Recursively walks through directory tree
   - Filters by supported extensions
   - Skips `.git` directory

3. **Create File Objects**:
   - Reads file content
   - Creates BytesIO objects compatible with Streamlit
   - Preserves relative paths

4. **Scan Files**:
   - Passes files to scanning agent
   - Runs LLM-powered analysis
   - Generates security findings

5. **Cleanup**:
   - Removes temporary clone directory
   - Frees up disk space

---

## 🛡️ Security Considerations

### Personal Access Tokens

- **Never commit tokens** to version control
- **Use minimal scopes** (only `repo` scope needed)
- **Revoke tokens** after use if no longer needed
- **Tokens are stored** only in session memory, not saved to disk

### Repository Access

- **Public repos**: No authentication required
- **Private repos**: Requires valid Personal Access Token
- **Organization repos**: Ensure token has access to the organization

---

## ⚠️ Limitations

1. **Repository Size**: Large repositories may take longer to clone
   - Consider using file upload for very large repos
   - Shallow clone helps reduce download time

2. **File Count**: Scanning many files uses more LLM API calls
   - Monitor your NVIDIA API quota
   - Rate limiting: 2 seconds between batches

3. **Binary Files**: Only text-based files are scanned
   - Images, executables, etc. are skipped automatically

4. **Network Required**: Internet connection needed to clone repository

---

## 💡 Tips & Best Practices

### For Faster Scans

1. **Test with small repos first**: Verify setup with small repositories
2. **Use specific branches**: Clone specific branch if needed (modify URL)
3. **Monitor progress**: Watch execution logs for status updates

### Error Handling

**Authentication Failed:**
```
❌ GitHub authentication failed. Please provide a valid Personal Access Token.
```
**Solution**: Generate new token with `repo` scope

**No Files Found:**
```
⚠️ No supported files found in repository
```
**Solution**: Check if repository contains supported file types

**Clone Failed:**
```
❌ Failed to clone repository: ...
```
**Solution**: 
- Verify URL is correct
- Check internet connection
- Ensure repository exists and is accessible

---

## 📊 Example Workflow

### Scanning a Public Python Project

```
1. Open DevGuard
2. Select "GitHub Repository"
3. Enter: https://github.com/pallets/flask
4. Click "Start LLM-Powered Scan"

Result:
✅ Repository cloned successfully
✅ Collected 247 file(s) from repository
🔍 Starting file scan... 247 file(s) to analyze
📊 Analysis complete with findings
```

### Scanning Your Private Repository

```
1. Generate token at https://github.com/settings/tokens
2. Open DevGuard
3. Select "GitHub Repository"
4. Enter: https://github.com/yourusername/private-repo
5. Expand "Advanced: Private Repository Access"
6. Paste token: ghp_xxxxx...
7. Click "Start LLM-Powered Scan"

Result:
✅ Repository cloned successfully (using authentication)
✅ Collected 42 file(s) from repository
🔍 Starting file scan... 42 file(s) to analyze
📊 Analysis complete with findings
```

---

## 🔧 Troubleshooting

### GitPython Not Installed

**Error:**
```
❌ GitPython not installed. Please run: pip install GitPython
```

**Fix:**
```bash
pip install GitPython
```

### Rate Limit Exceeded

**Symptom:** Many files cause API quota issues

**Solution:**
- Reduce batch size in configuration
- Wait between scans
- Consider uploading specific files instead

### Clone Timeout

**Symptom:** Large repository takes too long

**Solution:**
- Use file upload for very large repos
- Clone manually and upload specific files
- Use smaller test repositories first

---

## 🆚 Comparison: GitHub vs File Upload

| Feature | GitHub Repository | File Upload |
|---------|------------------|-------------|
| **Setup** | Enter URL | Select files manually |
| **Speed** | Depends on repo size | Instant |
| **File Selection** | Automatic (all files) | Manual selection |
| **Private Repos** | Requires token | Direct access |
| **Large Projects** | May be slow | Faster (selected files) |
| **Best For** | Full repo scans | Specific files |

---

## 🎯 Use Cases

### 1. **Pre-Purchase Code Review**
- Scan open-source project before adopting
- Verify security practices
- Identify potential vulnerabilities

### 2. **Compliance Auditing**
- Audit entire codebase for compliance
- Track security posture over time
- Generate comprehensive reports

### 3. **Third-Party Code Assessment**
- Evaluate vendor code security
- Review dependencies
- Risk assessment

### 4. **CI/CD Integration** (Future)
- Automated security checks
- Pull request analysis
- Continuous monitoring

---

## 📚 API Reference

### GitHub URL Format

```
https://github.com/{owner}/{repository}
```

**Valid Examples:**
```
✅ https://github.com/microsoft/vscode
✅ https://github.com/facebook/react
✅ https://github.com/username/my-project
```

**Invalid Examples:**
```
❌ github.com/microsoft/vscode        (missing https://)
❌ http://github.com/microsoft/vscode (must be https)
❌ https://gitlab.com/project/repo    (only GitHub supported)
```

---

## 🔄 Updates & Roadmap

### Current Features ✅
- [x] Public repository support
- [x] Private repository support
- [x] Automatic file collection
- [x] All file types supported
- [x] Error handling

### Planned Features 🚧
- [ ] Branch/tag selection
- [ ] Specific path filtering
- [ ] GitLab support
- [ ] Bitbucket support
- [ ] Incremental scanning (only changed files)
- [ ] Repository comparison (before/after)

---

## 📞 Support

**Issues?**
- Check execution logs in the UI
- Verify GitHub token permissions
- Ensure repository is accessible
- Test with smaller repositories first

**Still need help?**
- Open an issue on GitHub
- Check documentation
- Review error messages carefully

---

**Last Updated:** January 20, 2026  
**Version:** 2.0  
**Feature Status:** ✅ Stable

