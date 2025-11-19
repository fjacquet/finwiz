#!/bin/bash
# Switch from MkDocs (gh-pages branch) to Jekyll (main branch)

set -e

echo "🔄 Switching GitHub Pages from MkDocs to Jekyll..."
echo ""

# Check if we're on main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "❌ Please run this script from the main branch"
    echo "   Current branch: $current_branch"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

echo "✅ On main branch with clean working directory"
echo ""

# Delete local gh-pages branch if it exists
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "🗑️  Deleting local gh-pages branch..."
    git branch -D gh-pages
    echo "✅ Local gh-pages branch deleted"
else
    echo "ℹ️  No local gh-pages branch to delete"
fi

# Delete remote gh-pages branch
if git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
    echo "🗑️  Deleting remote gh-pages branch..."
    git push origin --delete gh-pages
    echo "✅ Remote gh-pages branch deleted"
else
    echo "ℹ️  No remote gh-pages branch to delete"
fi

echo ""
echo "✅ MkDocs artifacts removed!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Go to GitHub repository settings:"
echo "   https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/settings/pages"
echo ""
echo "2. Under 'Build and deployment':"
echo "   - Source: Deploy from a branch"
echo "   - Branch: main"
echo "   - Folder: /docs"
echo ""
echo "3. Click 'Save'"
echo ""
echo "4. Wait 1-2 minutes for GitHub Pages to rebuild"
echo ""
echo "5. Your site will be available at:"
echo "   https://$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | cut -d'/' -f1).github.io/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/' | cut -d'/' -f2)/"
echo ""
echo "🌙 Dark mode will work automatically based on system preferences!"
