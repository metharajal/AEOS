#!/usr/bin/env bash

set -e
set -o pipefail

echo "=========================================="
echo "🚀 AI Foundation Kit Bootstrap"
echo "=========================================="
echo ""

echo "🔍 Detecting operating system..."
OS=$(uname)
echo "Operating System: $OS"
echo ""

if [[ "$OS" != "Darwin" ]]; then
  echo "❌ This first bootstrap version currently supports macOS only."
  exit 1
fi

echo "✅ macOS detected."
echo ""

echo "🍺 Checking Homebrew..."

if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Homebrew is not installed."
  exit 1
fi

echo "✅ Homebrew installed."
echo ""

echo "🔧 Checking required tools..."

TOOLS=(
git
gh
node
pnpm
uv
docker
code
)

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        echo "✅ $tool"
    else
        echo "❌ Missing: $tool"
    fi
done

echo ""
echo "🎉 Bootstrap verification completed."