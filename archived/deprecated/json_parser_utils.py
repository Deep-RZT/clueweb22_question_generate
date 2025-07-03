#!/usr/bin/env python3
"""
JSON Parser Utils
JSON解析工具函数
"""

import json
import re
from typing import Any, Optional

def parse_json_response(content: str) -> Optional[Any]:
    """
    解析可能包含markdown代码块的JSON响应
    
    Args:
        content: 原始响应内容
        
    Returns:
        解析后的JSON数据，如果失败返回None
    """
    
    if not content:
        return None
    
    # 清理内容
    content = content.strip()
    
    # 方法1: 直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 方法2: 移除markdown代码块标记
    if content.startswith('```json'):
        content = content[7:]
    elif content.startswith('```'):
        content = content[3:]
    
    if content.endswith('```'):
        content = content[:-3]
    
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 方法3: 使用正则表达式提取JSON部分
    # 查找数组格式 [...]
    array_match = re.search(r'\[.*\]', content, re.DOTALL)
    if array_match:
        json_part = array_match.group(0)
        try:
            return json.loads(json_part)
        except json.JSONDecodeError:
            pass
    
    # 查找对象格式 {...}
    object_match = re.search(r'\{.*\}', content, re.DOTALL)
    if object_match:
        json_part = object_match.group(0)
        try:
            return json.loads(json_part)
        except json.JSONDecodeError:
            pass
    
    # 方法4: 尝试修复常见的JSON格式问题
    # 移除可能的前后文本
    lines = content.split('\n')
    json_lines = []
    in_json = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('[') or line.startswith('{'):
            in_json = True
        
        if in_json:
            json_lines.append(line)
        
        if line.endswith(']') or line.endswith('}'):
            break
    
    if json_lines:
        json_content = '\n'.join(json_lines)
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            pass
    
    return None

def extract_questions_from_response(response_content: str) -> list:
    """
    从响应中提取问题列表
    
    Args:
        response_content: API响应内容
        
    Returns:
        问题列表
    """
    
    parsed_data = parse_json_response(response_content)
    
    if parsed_data is None:
        return []
    
    # 如果是列表，直接返回
    if isinstance(parsed_data, list):
        return parsed_data
    
    # 如果是字典，查找questions键
    if isinstance(parsed_data, dict):
        if 'questions' in parsed_data:
            return parsed_data['questions']
        elif 'data' in parsed_data:
            return parsed_data['data']
        elif 'items' in parsed_data:
            return parsed_data['items']
        else:
            # 如果字典只有一个键，可能是包装的数据
            keys = list(parsed_data.keys())
            if len(keys) == 1:
                value = parsed_data[keys[0]]
                if isinstance(value, list):
                    return value
    
    return []

def test_json_parser():
    """测试JSON解析器"""
    
    # 测试用例
    test_cases = [
        # 正常JSON
        '[{"question": "test", "difficulty": "Easy"}]',
        
        # Markdown包装的JSON
        '```json\n[{"question": "test", "difficulty": "Easy"}]\n```',
        
        # 带前后文本的JSON
        'Here is the JSON:\n[{"question": "test", "difficulty": "Easy"}]\nEnd of response.',
        
        # 字典包装的JSON
        '{"questions": [{"question": "test", "difficulty": "Easy"}]}',
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"输入: {test_case}")
        
        result = parse_json_response(test_case)
        questions = extract_questions_from_response(test_case)
        
        print(f"解析结果: {result}")
        print(f"提取问题: {questions}")
        print("-" * 50)

if __name__ == "__main__":
    test_json_parser() 