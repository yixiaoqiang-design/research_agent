import os
import glob

import sys
import io

# 方法1：修改标准输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def find_files_ignore_node_modules(directory, extension):
    """
    使用glob遍历目录，但忽略node_modules目录
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    print(f"在目录 '{directory}' 中查找扩展名为 '{extension}' 的文件...")
    print("忽略 node_modules 目录")
    print("=" * 60)
    
    file_count = 0
    
    # 构建搜索模式
    search_pattern = os.path.join(directory, '**', f'*{extension}')
    
    # 使用glob递归查找文件
    for file_path in glob.glob(search_pattern, recursive=True):
        # 检查文件路径是否包含node_modules
        if 'node_modules' in file_path.split(os.sep):
            continue  # 跳过node_modules目录中的文件
        if 'venv' in file_path.split(os.sep):
            continue  # 跳过node_modules目录中的文件
        
        if os.path.isfile(file_path):
            file_count += 1
            print(f"\n文件 {file_count}: {file_path}")
            print("-" * 40)
            
            try:
                # 尝试以UTF-8编码读取文件
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    print(content)
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='gbk') as file:
                        content = file.read()
                        print(content)
                except Exception as e:
                    print(f"无法读取文件: {e}")
            except Exception as e:
                print(f"读取文件时出错: {e}")
    
    print("=" * 60)
    print(f"共找到 {file_count} 个{extension}文件")

# 使用示例
if __name__ == "__main__":
    directory = input("请输入要搜索的目录路径（留空使用当前目录）: ") or "."
    extension = input("请输入文件扩展名（如: txt, py, md）: ") or "txt"
    
    find_files_ignore_node_modules(directory, extension)