#!/usr/bin/env python3
"""
Convert ClueWeb22 Data
将ClueWeb22的txt文件转换为JSON格式
"""

import os
import json
import re
from typing import List, Dict
from pathlib import Path

def parse_clueweb22_file(file_path: str) -> List[Dict]:
    """解析单个ClueWeb22文件"""
    documents = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取文件名作为主题
        filename = os.path.basename(file_path)
        topic = filename.replace('.txt', '').replace('_', ' ')
        
        # 简单分割内容为段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 每个段落作为一个文档
        for i, paragraph in enumerate(paragraphs[:10]):  # 限制每个文件最多10个文档
            if len(paragraph) > 50:  # 过滤太短的段落
                doc = {
                    'title': f"{topic} - Part {i+1}",
                    'content': paragraph,
                    'source': 'clueweb22',
                    'file_origin': filename,
                    'language': detect_language(paragraph)
                }
                documents.append(doc)
    
    except Exception as e:
        print(f"解析文件失败 {file_path}: {e}")
    
    return documents

def detect_language(text: str) -> str:
    """简单的语言检测"""
    # 检测日文字符
    japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)
    # 检测英文字符
    english_chars = re.findall(r'[a-zA-Z]', text)
    
    if japanese_chars and english_chars:
        return 'en-ja'
    elif japanese_chars:
        return 'ja'
    else:
        return 'en'

def convert_clueweb22_to_json():
    """转换ClueWeb22数据为JSON格式"""
    
    input_dir = "task_file/clueweb22_query_results"
    output_dir = "task_file/clueweb22_json_results"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有txt文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    print(f"找到 {len(txt_files)} 个txt文件")
    
    # 按主题分组文件
    topic_groups = {}
    for filename in txt_files:
        # 提取主题名（去掉top数字部分）
        topic_match = re.match(r'(clueweb22-[^_]+)', filename)
        if topic_match:
            topic_base = topic_match.group(1)
            if topic_base not in topic_groups:
                topic_groups[topic_base] = []
            topic_groups[topic_base].append(filename)
    
    print(f"识别到 {len(topic_groups)} 个主题组")
    
    # 处理每个主题组
    for topic_base, files in topic_groups.items():
        print(f"处理主题: {topic_base} ({len(files)} 个文件)")
        
        all_documents = []
        
        # 处理该主题的所有文件
        for filename in files[:5]:  # 每个主题最多处理5个文件
            file_path = os.path.join(input_dir, filename)
            documents = parse_clueweb22_file(file_path)
            all_documents.extend(documents)
        
        if all_documents:
            # 保存为JSON
            output_data = {
                'topic': topic_base.replace('-', ' '),
                'source': 'clueweb22',
                'total_documents': len(all_documents),
                'results': all_documents
            }
            
            output_file = os.path.join(output_dir, f"{topic_base}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"  保存到: {output_file} ({len(all_documents)} 个文档)")
    
    # 生成统计信息
    stats = {
        'total_topics': len(topic_groups),
        'total_files_processed': sum(min(5, len(files)) for files in topic_groups.values()),
        'topics': list(topic_groups.keys())
    }
    
    stats_file = os.path.join(output_dir, "conversion_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n转换完成！")
    print(f"输出目录: {output_dir}")
    print(f"主题数量: {stats['total_topics']}")
    print(f"统计文件: {stats_file}")

def create_sample_topics():
    """创建一些示例主题用于测试"""
    
    output_dir = "task_file/clueweb22_json_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 示例主题数据
    sample_topics = [
        {
            'topic': 'artificial intelligence research',
            'documents': [
                {
                    'title': 'AI Research Trends in 2024',
                    'content': 'Recent advances in artificial intelligence have focused on large language models, computer vision, and reinforcement learning. These technologies are transforming various industries including healthcare, finance, and autonomous systems.',
                    'source': 'clueweb22',
                    'language': 'en'
                },
                {
                    'title': '人工知能研究の最新動向',
                    'content': '人工知能の研究分野では、深層学習、自然言語処理、コンピュータビジョンが主要な技術として注目されている。これらの技術は医療、金融、自動運転などの分野で実用化が進んでいる。',
                    'source': 'clueweb22',
                    'language': 'ja'
                }
            ]
        },
        {
            'topic': 'machine learning applications',
            'documents': [
                {
                    'title': 'Machine Learning in Healthcare',
                    'content': 'Machine learning algorithms are being applied to medical diagnosis, drug discovery, and personalized treatment plans. Deep learning models can analyze medical images with accuracy comparable to human experts.',
                    'source': 'clueweb22',
                    'language': 'en'
                },
                {
                    'title': '機械学習の医療応用',
                    'content': '機械学習技術は医療診断、創薬、個別化医療の分野で活用されている。特に画像診断においては、深層学習モデルが専門医と同等の精度を実現している。',
                    'source': 'clueweb22',
                    'language': 'ja'
                }
            ]
        },
        {
            'topic': 'computer vision technology',
            'documents': [
                {
                    'title': 'Computer Vision Advances',
                    'content': 'Computer vision technology has made significant progress in object detection, image segmentation, and facial recognition. These advances enable applications in autonomous vehicles, security systems, and augmented reality.',
                    'source': 'clueweb22',
                    'language': 'en'
                }
            ]
        },
        {
            'topic': 'natural language processing',
            'documents': [
                {
                    'title': 'NLP Breakthrough Technologies',
                    'content': 'Natural language processing has achieved remarkable progress with transformer architectures and large language models. These technologies enable better machine translation, text summarization, and conversational AI.',
                    'source': 'clueweb22',
                    'language': 'en'
                }
            ]
        },
        {
            'topic': 'robotics and automation',
            'documents': [
                {
                    'title': 'Robotics in Manufacturing',
                    'content': 'Industrial robotics and automation systems are revolutionizing manufacturing processes. Advanced robots can perform complex assembly tasks, quality control, and collaborative work with human operators.',
                    'source': 'clueweb22',
                    'language': 'en'
                }
            ]
        }
    ]
    
    # 保存示例主题
    for i, topic_data in enumerate(sample_topics):
        topic_name = topic_data['topic'].replace(' ', '_')
        
        output_data = {
            'topic': topic_data['topic'],
            'source': 'clueweb22',
            'total_documents': len(topic_data['documents']),
            'results': topic_data['documents']
        }
        
        output_file = os.path.join(output_dir, f"sample_topic_{i+1}_{topic_name}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"创建示例主题: {output_file}")
    
    print(f"\n创建了 {len(sample_topics)} 个示例主题")

def main():
    """主函数"""
    print("=== ClueWeb22数据转换 ===")
    
    # 检查是否有实际的ClueWeb22数据
    input_dir = "task_file/clueweb22_query_results"
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    if txt_files:
        print(f"发现 {len(txt_files)} 个ClueWeb22文件，开始转换...")
        convert_clueweb22_to_json()
    else:
        print("未发现ClueWeb22 txt文件，创建示例主题...")
        create_sample_topics()

if __name__ == "__main__":
    main() 