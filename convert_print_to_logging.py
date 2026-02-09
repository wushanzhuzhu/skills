#!/usr/bin/env python3
"""
批量替换print语句为logging的脚本
"""

import os
import re
import ast

def has_logging_import(file_path):
    """检查文件是否已经导入logging"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return 'import logging' in content
    except:
        return False

def has_print_statements(file_path):
    """检查文件是否有print语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return 'print(' in content
    except:
        return False

def add_logging_to_file(file_path):
    """为Python文件添加logging配置"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST找到所有导入语句
        try:
            tree = ast.parse(content)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
        except:
            imports = []
        
        # 如果已经导入logging，跳过
        if 'import logging' in content:
            return False
        
        # 在第一个import后添加logging导入
        lines = content.split('\n')
        new_lines = []
        added_logging = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if (line.startswith('import ') or line.startswith('from ')) and not added_logging:
                new_lines.extend([
                    'import logging',
                    '',
                    '# 配置日志',
                    'logging.basicConfig(',
                    '    level=logging.INFO,',
                    '    format="%(asctime)s - %(levelname)s - %(message)s",',
                    '    datefmt="%Y-%m-%d %H:%M:%S"',
                    ')',
                    'logger = logging.getLogger(__name__)',
                    ''
                ])
                added_logging = True
        
        new_content = '\n'.join(new_lines)
        
        # 替换print语句
        new_content = re.sub(r'print\(', 'logger.info(', new_content)
        new_content = new_content.replace('logger.info(f"❌', 'logger.error(f"❌')
        new_content = new_content.replace('logger.info("❌', 'logger.error("❌')
        new_content = new_content.replace('logger.info(f"⚠️', 'logger.warning(f"⚠️')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    root_dir = '/root/new002'
    processed_count = 0
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk(root_dir):
        # 跳过特定目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # 检查是否需要处理
                if has_print_statements(file_path) and not has_logging_import(file_path):
                    if add_logging_to_file(file_path):
                        processed_count += 1
                        print(f"Processed: {file_path}")
    
    print(f"Total processed files: {processed_count}")

if __name__ == '__main__':
    main()