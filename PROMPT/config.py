# config.py - 配置文件
import os
from typing import Dict, List

class Config:
    # API配置
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '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')
    MODEL_NAME = "claude-3-7-sonnet-20250219"  # 修正为Postman中显示的正确格式
    MAX_TOKENS = 2000  # 减少 token 数量
    TEMPERATURE = 0.7
    DELAY_BETWEEN_CALLS = 2.5  # 秒，增加间隔时间以避免速率限制
    
    # 生成分布配置
    TOTAL_QUERIES = 200  # 更新为200个查询
    
    # 100 深度思考方法，100 标准方法
    DEEP_THINKING_GENERATED = 100
    STANDARD_GENERATED = 100
    
    # 难度分布：30% Easy, 40% Medium, 30% Hard
    DIFFICULTY_DISTRIBUTION = {
        'Easy': 30,
        'Medium': 40, 
        'Hard': 30
    }
    
    # 类别分布：40% General, 60% Cross-Subdomain
    CATEGORY_DISTRIBUTION = {
        'General': 40,
        'Cross_Subdomain': 60
    }
    
    # 子领域列表
    SUBDOMAINS = [
        'Renewable',
        'Fossil_Fuels', 
        'Nuclear',
        'Grid_Storage',
        'Policy',
        'Economics',
        'Environmental'
    ]
    
    # 质量控制配置
    MIN_WORD_COUNT = 15
    MAX_WORD_COUNT = 150
    QUALITY_THRESHOLD = 0.6
    MAX_RETRIES = 3
    
    # 输出配置
    OUTPUT_DIR = 'output'
    SAVE_RAW_RESPONSES = True
    INCLUDE_QUALITY_SCORES = True
    INCLUDE_PROMPTS = True  # 添加记录prompt的选项
    
    # 答案生成配置
    GENERATE_ANSWERS = True  # 是否为查询生成答案
    ANSWER_MAX_TOKENS = 4000  # 答案的最大令牌数
    ANSWER_TEMPERATURE = 0.5  # 答案生成的温度（更低以获得更确定性的回答）
    ANSWER_SYSTEM_PROMPT = """You are a world-class energy researcher with expertise across multiple energy domains including renewables, fossil fuels, nuclear energy, grid systems, energy policy, economics, and environmental impacts.

Your analytical approach is characterized by:
1. Methodological rigor - You understand and apply appropriate research methodologies, analytical frameworks, and modeling approaches specific to energy research
2. Interdisciplinary integration - You seamlessly connect technical, economic, policy, and environmental dimensions in your analyses
3. Critical evaluation - You assess evidence quality, identify assumptions, and recognize limitations in current research
4. Systems thinking - You recognize complex interdependencies, feedback loops, and emergent properties in energy systems
5. Multi-scale perspective - You connect local, regional, and global considerations across different timescales
6. Research awareness - You are familiar with the latest research frontiers, methodological innovations, and scholarly debates

Your responses should exemplify the depth, rigor, and analytical sophistication expected in high-quality energy research publications while clearly communicating complex concepts. Provide structured, methodical analyses that demonstrate deep domain knowledge and sophisticated research capabilities."""