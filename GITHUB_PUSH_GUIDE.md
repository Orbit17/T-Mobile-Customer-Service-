# 🚀 How to Push to GitHub

## Step-by-Step Guide

### 1. Check if Git is Initialized

```bash
cd "/Users/rafay/Downloads/T-Mobile-Customer-Service--main 2"
git status
```

If you see "not a git repository", initialize it:
```bash
git init
```

### 2. Create a .gitignore File (if it doesn't exist)

Make sure sensitive files are NOT pushed to GitHub:

```bash
cat > .gitignore << 'EOF'
# Environment variables (IMPORTANT - contains API keys!)
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.bak
*.cache
EOF
```

### 3. Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `T-Mobile-Customer-Service` (or your preferred name)
3. Description: "T-Mobile Customer Happiness Index Dashboard with AI-powered insights"
4. Choose **Private** (recommended since it contains API keys in code)
5. **DO NOT** initialize with README, .gitignore, or license (we already have files)
6. Click "Create repository"

### 4. Add All Files (except .env)

```bash
# Add all files
git add .

# Verify .env is NOT being added
git status | grep .env
# Should show nothing (or show .env as untracked, which is good)
```

### 5. Create Initial Commit

```bash
git commit -m "Initial commit: T-Mobile CHI Dashboard with AI chatbot and GROQ integration"
```

### 6. Add GitHub Remote

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/T-Mobile-Customer-Service.git
```

Or if you prefer SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/T-Mobile-Customer-Service.git
```

### 7. Push to GitHub

```bash
# Push to main branch
git branch -M main
git push -u origin main
```

If you get authentication errors, you may need to:
- Use a Personal Access Token (GitHub Settings → Developer settings → Personal access tokens)
- Or set up SSH keys

---

## ⚠️ IMPORTANT: Security Checklist

Before pushing, make sure:

1. ✅ `.env` file is in `.gitignore` (contains API keys!)
2. ✅ No API keys are hardcoded in source files
3. ✅ Database files are ignored
4. ✅ Consider making the repository **Private**

---

## 🔄 Future Updates

After making changes:

```bash
# Check what changed
git status

# Add changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

---

## 📝 Quick Commands Reference

```bash
# Check status
git status

# See what files changed
git diff

# Add all changes
git add .

# Commit
git commit -m "Your commit message"

# Push
git push

# Pull latest changes
git pull
```

---

## 🆘 Troubleshooting

### "Permission denied" error
- Use Personal Access Token instead of password
- Or set up SSH keys

### "Repository not found" error
- Check repository name and username
- Make sure repository exists on GitHub

### "Large files" error
- Check `.gitignore` includes large files
- Remove large files from git: `git rm --cached large_file.txt`

