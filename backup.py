# -*- coding: utf-8 -*-
"""
PRTS 项目版本备份脚本
使用方法：在项目根目录执行 python backup.py [版本号]
示例：python backup.py 1.0.0
若不指定版本号，则自动使用当前日期时间作为版本标识
"""

import os
import sys
import shutil
import time
from pathlib import Path

# 需要备份的文件扩展名（源代码和资源）
INCLUDE_EXTENSIONS = {'.py', '.ui', '.qrc', '.png', '.ico', '.txt', '.ini', '.md', '.json'}

# 需要备份的完整文件名（即使扩展名不在上述列表中）
INCLUDE_FILES = {'requirements.txt', 'config.ini', 'prts.png', 'prts.ico', 'README.md'}

# 需要排除的目录名（不会被备份）
EXCLUDE_DIRS = {'__pycache__', '.venv', 'venv', '.git', '.idea', '.vscode', 'dist', 'build', 'backup'}

# 需要排除的文件名模式（支持通配符）
EXCLUDE_PATTERNS = {'*.log', '*.pyc', '*.pyo', '*.pyd', '*.spec', '*.exe'}

def should_include(file_path: Path, root_dir: Path) -> bool:
    """判断文件是否应该被备份"""
    # 检查文件名是否在明确包含列表中
    if file_path.name in INCLUDE_FILES:
        return True
    
    # 检查扩展名
    if file_path.suffix.lower() in INCLUDE_EXTENSIONS:
        return True
    
    return False

def should_exclude(file_path: Path, root_dir: Path) -> bool:
    """判断文件/目录是否应被排除"""
    # 检查是否在排除目录中
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # 检查是否匹配排除模式
    for pattern in EXCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True
    
    return False

def copy_project(src_dir: Path, dst_dir: Path):
    """复制项目文件到目标目录"""
    if dst_dir.exists():
        print(f"⚠️ 目标目录 {dst_dir} 已存在，将删除后重新备份")
        shutil.rmtree(dst_dir)
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    file_count = 0
    for root, dirs, files in os.walk(src_dir):
        root_path = Path(root)
        
        # 过滤排除的目录（原地修改dirs列表影响遍历）
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        # 计算相对路径
        rel_path = root_path.relative_to(src_dir)
        target_path = dst_dir / rel_path
        target_path.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            file_path = root_path / file
            rel_file_path = file_path.relative_to(src_dir)
            
            # 检查是否应排除
            if should_exclude(file_path, src_dir):
                continue
            
            # 检查是否应包含
            if should_include(file_path, src_dir):
                shutil.copy2(file_path, target_path / file)
                file_count += 1
                print(f"  ✓ 已备份: {rel_file_path}")
    
    return file_count

def main():
    # 确定版本号
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        version = time.strftime("%Y%m%d_%H%M%S")
    
    # 项目根目录（脚本所在目录）
    project_root = Path(__file__).parent.absolute()
    
    # 备份目标目录：上级目录/PRTS_backup_v版本号
    parent_dir = project_root.parent
    backup_dir = parent_dir / f"PRTS_backup_v{version}"
    
    print(f"📦 开始备份 PRTS 项目")
    print(f"   源目录: {project_root}")
    print(f"   目标目录: {backup_dir}")
    print()
    
    try:
        count = copy_project(project_root, backup_dir)
        print()
        print(f"✅ 备份完成！共备份 {count} 个文件。")
        print(f"   备份位置: {backup_dir}")
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()