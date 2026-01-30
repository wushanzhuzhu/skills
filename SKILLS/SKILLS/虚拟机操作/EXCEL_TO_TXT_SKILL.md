# Excel转TXT文本技能

## 功能描述
此技能用于将Excel电子表格(XLSX、XLS)转换为文本文件(TXT)格式。支持多种分隔符导出、单sheet或多sheet处理，可灵活设置列分隔符和行尾方式。

## 实现方法

### 基础转换 - 使用openpyxl和csv库

```python
import openpyxl
import csv

def excel_to_txt(excel_file, txt_file, delimiter='\t', sheet_name=0):
    """
    将Excel文件转换为TXT文本文件
    
    参数:
        excel_file: Excel文件路径
        txt_file: 输出的TXT文件路径
        delimiter: 列分隔符，默认为制表符(\t)
        sheet_name: sheet名称或索引，默认为第一个sheet
    """
    # 打开Excel文件
    workbook = openpyxl.load_workbook(excel_file)
    
    # 获取指定sheet
    if isinstance(sheet_name, int):
        worksheet = workbook.worksheets[sheet_name]
    else:
        worksheet = workbook[sheet_name]
    
    # 写入TXT文件
    with open(txt_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        for row in worksheet.iter_rows(values_only=True):
            writer.writerow(row)
    
    workbook.close()
    print(f"转换完成: {excel_file} -> {txt_file}")
```

### 高级转换 - 自定义处理

```python
def excel_to_txt_advanced(excel_file, txt_file, delimiter=',', 
                          skip_empty_rows=False, encoding='utf-8'):
    """
    高级Excel转TXT转换，支持更多选项
    
    参数:
        excel_file: Excel文件路径
        txt_file: 输出的TXT文件路径
        delimiter: 列分隔符，可选 ',' '\t' '|' 等
        skip_empty_rows: 是否跳过空行
        encoding: 输出文件编码，默认utf-8
    """
    workbook = openpyxl.load_workbook(excel_file)
    worksheet = workbook.active
    
    with open(txt_file, 'w', encoding=encoding, newline='') as f:
        for row in worksheet.iter_rows(values_only=True):
            # 跳过空行
            if skip_empty_rows and all(cell is None for cell in row):
                continue
            
            # 处理None值为空字符串
            row_data = [str(cell) if cell is not None else '' for cell in row]
            
            # 写入行
            f.write(delimiter.join(row_data) + '\n')
    
    workbook.close()
    print(f"高级转换完成: {excel_file} -> {txt_file}")
```

### 多Sheet转换 - 分别导出

```python
def excel_to_multi_txt(excel_file, output_dir, delimiter=','):
    """
    将Excel的所有sheet分别转换为独立的TXT文件
    
    参数:
        excel_file: Excel文件路径
        output_dir: 输出目录
        delimiter: 列分隔符
    """
    import os
    
    workbook = openpyxl.load_workbook(excel_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
        
        # 生成输出文件名
        output_file = os.path.join(output_dir, f"{sheet_name}.txt")
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            for row in worksheet.iter_rows(values_only=True):
                row_data = [str(cell) if cell is not None else '' for cell in row]
                f.write(delimiter.join(row_data) + '\n')
        
        print(f"已导出: {sheet_name} -> {output_file}")
    
    workbook.close()
```

### 使用Pandas库 - 更简洁

```python
import pandas as pd

def excel_to_txt_pandas(excel_file, txt_file, delimiter='\t', 
                       sheet_name=0, index=False):
    """
    使用pandas将Excel转换为TXT
    
    参数:
        excel_file: Excel文件路径
        txt_file: 输出的TXT文件路径
        delimiter: 列分隔符
        sheet_name: sheet名称或索引
        index: 是否输出索引列
    """
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    df.to_csv(txt_file, sep=delimiter, index=index, encoding='utf-8')
    print(f"转换完成: {excel_file} -> {txt_file}")

# 使用示例
excel_to_txt_pandas('data.xlsx', 'output.txt', delimiter=',')
```

## 使用示例

### 示例1: 基础转换
```python
# 将Excel转换为以制表符分隔的TXT文件
excel_to_txt('input.xlsx', 'output.txt', delimiter='\t')
```

### 示例2: 使用逗号分隔
```python
# 将Excel转换为以逗号分隔的CSV格式TXT
excel_to_txt('data.xlsx', 'data.txt', delimiter=',')
```

### 示例3: 指定Sheet转换
```python
# 只转换特定sheet
excel_to_txt('input.xlsx', 'output.txt', sheet_name='Sheet2')
```

### 示例4: 多Sheet分别导出
```python
# 将所有sheet分别导出为TXT文件
excel_to_multi_txt('input.xlsx', './output_folder', delimiter=',')
```

## 依赖库

```bash
pip install openpyxl pandas
```

## 分隔符选项表

| 分隔符 | 说明 | 使用场景 |
|--------|------|---------|
| `,` | 逗号 | CSV标准格式 |
| `\t` | 制表符 | 制表符分隔值 |
| ` ` | 空格 | 固定宽度文本 |
| `\|` | 竖线 | 数据库导出 |
| `;` | 分号 | 某些地区的CSV标准 |

## 注意事项

1. **编码问题**: 确保输出文件编码正确，建议使用UTF-8
2. **空值处理**: 空单元格会被转换为空字符串
3. **数据类型**: 所有数据会被转换为字符串格式
4. **大文件**: 处理大文件时建议使用流式处理
5. **公式**: Excel中的公式会被转换为其计算结果

## 常见问题解决

### 问题1: 中文乱码
```python
# 明确指定编码为UTF-8
df.to_csv(txt_file, encoding='utf-8-sig')
```

### 问题2: 日期格式错误
```python
# 指定日期格式
df['date_column'] = pd.to_datetime(df['date_column']).dt.strftime('%Y-%m-%d')
```

### 问题3: 处理大文件
```python
# 使用分块处理
chunk_size = 10000
for chunk in pd.read_excel(excel_file, chunksize=chunk_size):
    chunk.to_csv(txt_file, mode='a', index=False)
```

## 完整脚本示例

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import openpyxl
import pandas as pd
from pathlib import Path

class ExcelToTxtConverter:
    """Excel转TXT转换器类"""
    
    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.workbook = openpyxl.load_workbook(excel_file)
    
    def convert_single(self, output_file, delimiter=',', sheet_index=0):
        """转换单个sheet"""
        worksheet = self.workbook.worksheets[sheet_index]
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in worksheet.iter_rows(values_only=True):
                row_str = [str(cell) if cell is not None else '' for cell in row]
                f.write(delimiter.join(row_str) + '\n')
        print(f"✓ 已转换: {output_file}")
    
    def convert_all(self, output_dir, delimiter=','):
        """转换所有sheet"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for i, sheet_name in enumerate(self.workbook.sheetnames):
            output_file = os.path.join(output_dir, f"{sheet_name}.txt")
            self.convert_single(output_file, delimiter, i)
    
    def close(self):
        self.workbook.close()

# 使用示例
if __name__ == '__main__':
    converter = ExcelToTxtConverter('input.xlsx')
    converter.convert_all('./output', delimiter=',')
    converter.close()
```

