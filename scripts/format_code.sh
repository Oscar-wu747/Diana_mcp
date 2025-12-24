#!/bin/bash

# 代码格式化脚本
# 使用 Black 和 isort 格式化 Python 代码

set -e

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "=========================================="
echo "代码格式化工具"
echo "=========================================="
echo ""

# 检查 Black 是否安装
if ! command -v black &> /dev/null; then
    echo "❌ Black 未安装，正在安装..."
    pip install black>=23.12.0 isort>=5.13.0
fi

echo "📝 使用 Black 格式化代码..."
black .

echo ""
echo "📦 使用 isort 整理导入..."
isort .

echo ""
echo "✅ 代码格式化完成！"
echo ""
echo "提示："
echo "  - 检查更改: git diff"
echo "  - 只检查不修改: black --check ."
echo "  - 格式化单个文件: black path/to/file.py"

