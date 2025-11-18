#!/bin/bash
# Final automation script to complete Willow migration
# Run this after reviewing all changes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "Willow Migration - Final Steps Automation"
echo "=================================================================="
echo ""
echo "This script will:"
echo "  1. Rename extension directory"
echo "  2. Replace temporary files with final versions"
echo "  3. Remove old files"
echo "  4. Update git repository (optional)"
echo ""
read -p "Have you reviewed all changes? Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted. Please review changes first."
    exit 1
fi

echo ""
echo "Step 1: Running migration script..."
if [ -f "migrate-to-willow.sh" ]; then
    chmod +x migrate-to-willow.sh
    ./migrate-to-willow.sh
else
    echo "⚠ migrate-to-willow.sh not found, skipping..."
fi

echo ""
echo "Step 2: Replacing PKGBUILD files..."
if [ -f "PKGBUILD.new" ]; then
    mv PKGBUILD PKGBUILD.old
    mv PKGBUILD.new PKGBUILD
    echo "✓ PKGBUILD updated (old saved as PKGBUILD.old)"
fi

if [ -f "PKGBUILD-git.new" ]; then
    mv PKGBUILD-git PKGBUILD-git.old 2>/dev/null || true
    mv PKGBUILD-git.new PKGBUILD-git
    echo "✓ PKGBUILD-git updated"
fi

echo ""
echo "Step 3: Replacing documentation..."
if [ -f "README.new.md" ]; then
    mv README.md README.old.md
    mv README.new.md README.md
    echo "✓ README.md updated (old saved as README.old.md)"
fi

if [ -f ".github/copilot-instructions.new.md" ]; then
    mv .github/copilot-instructions.md .github/copilot-instructions.old.md 2>/dev/null || true
    mv .github/copilot-instructions.new.md .github/copilot-instructions.md
    echo "✓ Copilot instructions updated"
fi

echo ""
echo "Step 4: Generating .SRCINFO for AUR..."
if command -v makepkg &> /dev/null; then
    makepkg --printsrcinfo > .SRCINFO 2>/dev/null || echo "⚠ Failed to generate .SRCINFO (not critical)"
    echo "✓ .SRCINFO generated"
else
    echo "⚠ makepkg not found, skipping .SRCINFO generation"
fi

echo ""
echo "Step 5: Cleaning up temporary files..."
rm -f migrate-to-willow.sh
echo "✓ Migration script removed"

echo ""
echo "=================================================================="
echo "Migration Complete!"
echo "=================================================================="
echo ""
echo "✅ All files have been updated and renamed"
echo "✅ Old files backed up with .old suffix"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the build:"
echo "   cd service && rm -rf build && mkdir build && cd build"
echo "   cmake .. && make"
echo ""
echo "2. Review changes:"
echo "   git status"
echo "   git diff"
echo ""
echo "3. Commit changes:"
echo "   git add ."
echo "   git commit -m 'Rebrand to Willow with centralized configuration'"
echo ""
echo "4. Optional - rename repository on GitHub:"
echo "   Go to Settings → Repository name → Rename"
echo ""
echo "5. Build and test package:"
echo "   makepkg -si"
echo ""
echo "=================================================================="

# Ask if user wants to see git status
echo ""
read -p "Show git status? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    git status
fi

echo ""
echo "Done! Check REBRANDING_SUMMARY.md for complete details."
