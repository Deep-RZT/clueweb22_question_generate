#!/usr/bin/env python3
"""
Tree Level Query 整合系统
实现 WorkFlow 第7步: "Combine q11, q12, ..., q1n and q0 to derive a final, deeply expanded question → q1"
生成最终的深度整合问题，糅合所有层次的问题信息
"""

import logging
import json
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuestionNode:
    """问题节点"""
    question: str
    answer: str
    level: int
    parent_id: Optional[str] = None
    node_id: str = ""
    keywords: List[str] = None
    question_type: str = ""

@dataclass
class TreeLevelQuery:
    """树级整合问题"""
    integrated_question: str
    root_answer: str
    integration_depth: int
    component_questions: List[str]
    reasoning_path: List[str]
    confidence: float
    complexity_score: float
    metadata: Dict[str, Any]

class TreeLevelQueryIntegrator:
    """树级问题整合器"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        self.integration_strategies = {
            'keyword_replacement': self._integrate_with_keyword_replacement,
            'contextual_chaining': self._integrate_with_contextual_chaining,
            'hierarchical_fusion': self._integrate_with_hierarchical_fusion
        }
        
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
    
    def generate_tree_level_query(self, question_tree: Dict[str, Any], integration_strategy: str = 'hierarchical_fusion') -> Optional[TreeLevelQuery]:
        """
        生成树级整合问题
        
        Args:
            question_tree: 完整的问题树结构
            integration_strategy: 整合策略 ('keyword_replacement', 'contextual_chaining', 'hierarchical_fusion')
        
        Returns:
            TreeLevelQuery: 整合后的深度问题
        """
        logger.info(f"生成树级整合问题，策略: {integration_strategy}")
        
        if not self.api_client:
            logger.error("需要API客户端来生成整合问题")
            return None
        
        try:
            # 1. 解析问题树结构
            question_nodes = self._parse_question_tree(question_tree)
            
            if not question_nodes:
                logger.warning("无法解析问题树结构")
                return None
            
            # 2. 分析层次关系
            hierarchy_analysis = self._analyze_hierarchy(question_nodes)
            
            # 3. 选择并执行整合策略
            if integration_strategy not in self.integration_strategies:
                logger.warning(f"未知整合策略: {integration_strategy}，使用默认策略")
                integration_strategy = 'hierarchical_fusion'
            
            integration_func = self.integration_strategies[integration_strategy]
            tree_level_query = integration_func(question_nodes, hierarchy_analysis)
            
            if tree_level_query:
                logger.info(f"成功生成树级整合问题: {tree_level_query.integrated_question[:60]}...")
                return tree_level_query
            else:
                logger.warning("整合问题生成失败")
                return None
                
        except Exception as e:
            logger.error(f"生成树级整合问题时出错: {e}")
            return None
    
    def _parse_question_tree(self, question_tree: Dict[str, Any]) -> List[QuestionNode]:
        """解析问题树结构"""
        question_nodes = []
        
        try:
            # 解析根问题
            root_question_data = question_tree.get('root_question', {})
            if isinstance(root_question_data, dict):
                root_node = QuestionNode(
                    question=root_question_data.get('question', ''),
                    answer=root_question_data.get('answer', ''),
                    level=0,
                    node_id='root',
                    keywords=root_question_data.get('keywords', []),
                    question_type=self._determine_question_type(root_question_data.get('question', ''))
                )
                question_nodes.append(root_node)
            
            # 解析扩展节点
            nodes = question_tree.get('nodes', {})
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict):
                    child_node = QuestionNode(
                        question=node_data.get('question', ''),
                        answer=node_data.get('answer', ''),
                        level=node_data.get('depth_level', 1),
                        parent_id=node_data.get('parent_node_id', 'root'),
                        node_id=node_id,
                        keywords=node_data.get('keywords', []),
                        question_type=self._determine_question_type(node_data.get('question', ''))
                    )
                    question_nodes.append(child_node)
            
            logger.info(f"解析得到 {len(question_nodes)} 个问题节点")
            return question_nodes
            
        except Exception as e:
            logger.error(f"解析问题树时出错: {e}")
            return []
    
    def _determine_question_type(self, question: str) -> str:
        """确定问题类型"""
        question_lower = question.lower().strip()
        if question_lower.startswith('what'):
            return 'what'
        elif question_lower.startswith('when'):
            return 'when'
        elif question_lower.startswith('where'):
            return 'where'
        elif question_lower.startswith('who'):
            return 'who'
        elif question_lower.startswith('which'):
            return 'which'
        elif question_lower.startswith('how'):
            return 'how'
        elif question_lower.startswith('why'):
            return 'why'
        else:
            return 'other'
    
    def _analyze_hierarchy(self, question_nodes: List[QuestionNode]) -> Dict[str, Any]:
        """分析层次关系"""
        hierarchy = {'levels': {}, 'depth': 0, 'breadth': 0}
        
        # 按层级分组
        for node in question_nodes:
            level = node.level
            if level not in hierarchy['levels']:
                hierarchy['levels'][level] = []
            hierarchy['levels'][level].append(node)
        
        # 计算深度和广度
        hierarchy['depth'] = max(hierarchy['levels'].keys()) if hierarchy['levels'] else 0
        hierarchy['breadth'] = max(len(nodes) for nodes in hierarchy['levels'].values()) if hierarchy['levels'] else 0
        
        # 分析关键词流
        hierarchy['keyword_flow'] = self._analyze_keyword_flow(question_nodes)
        
        # 分析问题类型分布
        hierarchy['question_types'] = {}
        for node in question_nodes:
            qt = node.question_type
            hierarchy['question_types'][qt] = hierarchy['question_types'].get(qt, 0) + 1
        
        return hierarchy
    
    def _analyze_keyword_flow(self, question_nodes: List[QuestionNode]) -> Dict[str, List[str]]:
        """分析关键词在层次间的流动"""
        keyword_flow = {}
        
        for node in question_nodes:
            level_key = f"level_{node.level}"
            if level_key not in keyword_flow:
                keyword_flow[level_key] = []
            
            if node.keywords:
                keyword_flow[level_key].extend(node.keywords)
        
        # 去重
        for level, keywords in keyword_flow.items():
            keyword_flow[level] = list(set(keywords))
        
        return keyword_flow
    
    def _integrate_with_keyword_replacement(self, question_nodes: List[QuestionNode], hierarchy: Dict[str, Any]) -> Optional[TreeLevelQuery]:
        """使用关键词替换策略整合"""
        try:
            # 获取根问题
            root_node = next((node for node in question_nodes if node.level == 0), None)
            if not root_node:
                return None
            
            # 收集所有子问题的关键词
            child_keywords = []
            child_questions = []
            
            for node in question_nodes:
                if node.level > 0:
                    child_questions.append(node.question)
                    if node.keywords:
                        child_keywords.extend(node.keywords)
            
            if not child_questions:
                return None
            
            # Prompt说明: 使用关键词替换策略进行Tree Level Query整合
            integration_prompt = f"""You are performing keyword replacement strategy question integration. Deeply integrate root question with child question keywords.

Root Question: {root_node.question}
Root Answer: {root_node.answer}

Child Questions List:
{chr(10).join([f"- {q}" for q in child_questions])}

Child Question Keywords: {', '.join(set(child_keywords))}

Integration Requirements:
1. Based on root question structure, organically integrate child question keywords
2. Increase question depth and complexity
3. Maintain root answer as the final answer
4. Avoid overly complex questions that are hard to understand
5. Ensure the question has a clear reasoning path

Generate a deeply integrated question in JSON format:
{{
    "integrated_question": "Integrated deep question",
    "reasoning_path": ["Reasoning step 1", "Reasoning step 2", "Reasoning step 3"],
    "confidence": 0.0-1.0,
    "complexity_score": 0.0-1.0,
    "integration_method": "keyword_replacement"
}}"""

            response = self.api_client.generate_response(
                prompt=integration_prompt,
                temperature=0.3,
                max_tokens=600
            )
            
            # 解析响应
            integration_data = self._parse_integration_response(response)
            
            if integration_data:
                return TreeLevelQuery(
                    integrated_question=integration_data['integrated_question'],
                    root_answer=root_node.answer,
                    integration_depth=hierarchy['depth'],
                    component_questions=[root_node.question] + child_questions,
                    reasoning_path=integration_data.get('reasoning_path', []),
                    confidence=integration_data.get('confidence', 0.7),
                    complexity_score=integration_data.get('complexity_score', 0.8),
                    metadata={
                        'integration_method': 'keyword_replacement',
                        'total_keywords': len(set(child_keywords)),
                        'total_nodes': len(question_nodes)
                    }
                )
            
        except Exception as e:
            logger.error(f"关键词替换整合失败: {e}")
        
        return None
    
    def _integrate_with_contextual_chaining(self, question_nodes: List[QuestionNode], hierarchy: Dict[str, Any]) -> Optional[TreeLevelQuery]:
        """使用上下文链接策略整合"""
        try:
            # 按层级排序问题
            sorted_nodes = sorted(question_nodes, key=lambda x: (x.level, x.node_id))
            
            if len(sorted_nodes) < 2:
                return None
            
            # 构建推理链
            reasoning_chain = []
            all_questions = []
            
            for node in sorted_nodes:
                all_questions.append(node.question)
                reasoning_chain.append(f"Level {node.level}: {node.question} → {node.answer}")
            
            root_node = sorted_nodes[0]
            
            # Prompt说明: 使用上下文链接策略进行问题整合
            integration_prompt = f"""You are performing contextual chaining strategy question integration. Connect multi-level questions in logical order into a compound question.

Question Hierarchy Chain:
{chr(10).join(reasoning_chain)}

Integration Requirements:
1. Build a compound question that requires multi-step reasoning
2. The question should guide readers to think in hierarchical order
3. The final answer should be the root answer: {root_node.answer}
4. Ensure logical coherence of the reasoning chain
5. Avoid directly exposing the answer

Generate a contextually chained integration question in JSON format:
{{
    "integrated_question": "Integrated compound question",
    "reasoning_path": ["Reasoning step 1", "Reasoning step 2", "Reasoning step 3"],
    "confidence": 0.0-1.0,
    "complexity_score": 0.0-1.0,
    "integration_method": "contextual_chaining"
}}"""

            response = self.api_client.generate_response(
                prompt=integration_prompt,
                temperature=0.4,
                max_tokens=600
            )
            
            # 解析响应
            integration_data = self._parse_integration_response(response)
            
            if integration_data:
                return TreeLevelQuery(
                    integrated_question=integration_data['integrated_question'],
                    root_answer=root_node.answer,
                    integration_depth=hierarchy['depth'],
                    component_questions=all_questions,
                    reasoning_path=integration_data.get('reasoning_path', []),
                    confidence=integration_data.get('confidence', 0.7),
                    complexity_score=integration_data.get('complexity_score', 0.8),
                    metadata={
                        'integration_method': 'contextual_chaining',
                        'reasoning_chain_length': len(reasoning_chain),
                        'total_nodes': len(question_nodes)
                    }
                )
            
        except Exception as e:
            logger.error(f"上下文链接整合失败: {e}")
        
        return None
    
    def _integrate_with_hierarchical_fusion(self, question_nodes: List[QuestionNode], hierarchy: Dict[str, Any]) -> Optional[TreeLevelQuery]:
        """使用层次融合策略整合 (推荐策略)"""
        try:
            # 获取各层级信息
            levels = hierarchy['levels']
            root_node = next((node for node in question_nodes if node.level == 0), None)
            
            if not root_node:
                return None
            
            # 构建层次信息
            level_info = {}
            all_questions = [root_node.question]
            
            for level, nodes in levels.items():
                if level > 0:  # 跳过根级别
                    level_questions = [node.question for node in nodes]
                    level_answers = [node.answer for node in nodes]
                    level_keywords = []
                    for node in nodes:
                        if node.keywords:
                            level_keywords.extend(node.keywords)
                    
                    level_info[f"level_{level}"] = {
                        'questions': level_questions,
                        'answers': level_answers,
                        'keywords': list(set(level_keywords))
                    }
                    all_questions.extend(level_questions)
            
            if not level_info:
                return None
            
            # Prompt说明: 使用层次融合策略进行问题整合
            integration_prompt = f"""You are performing hierarchical fusion strategy question integration. Integrate multi-level question information into a comprehensive deep question.

Root Question: {root_node.question}
Root Answer: {root_node.answer}

Level Information:
{self._format_level_info(level_info)}

Question Type Distribution: {hierarchy.get('question_types', {})}
Tree Depth: {hierarchy['depth']}
Tree Breadth: {hierarchy['breadth']}

Hierarchical Fusion Requirements:
1. Create a deep question that integrates multiple levels of information
2. The question should reflect hierarchical structure from abstract to specific
3. Integrate keywords and concepts from different levels
4. Maintain final answer as root answer
5. Ensure the question has research value and challenge
6. Avoid overly lengthy or complex questions

Generate a hierarchically fused integration question in JSON format:
{{
    "integrated_question": "Hierarchically fused deep question",
    "reasoning_path": ["Reasoning step 1", "Reasoning step 2", "Reasoning step 3", "Reasoning step 4"],
    "confidence": 0.0-1.0,
    "complexity_score": 0.0-1.0,
    "integration_method": "hierarchical_fusion",
    "fusion_elements": ["融合的关键元素1", "融合的关键元素2"]
}}"""

            response = self.api_client.generate_response(
                prompt=integration_prompt,
                temperature=0.3,
                max_tokens=700
            )
            
            # 解析响应
            integration_data = self._parse_integration_response(response)
            
            if integration_data:
                return TreeLevelQuery(
                    integrated_question=integration_data['integrated_question'],
                    root_answer=root_node.answer,
                    integration_depth=hierarchy['depth'],
                    component_questions=all_questions,
                    reasoning_path=integration_data.get('reasoning_path', []),
                    confidence=integration_data.get('confidence', 0.8),
                    complexity_score=integration_data.get('complexity_score', 0.9),
                    metadata={
                        'integration_method': 'hierarchical_fusion',
                        'fusion_elements': integration_data.get('fusion_elements', []),
                        'total_levels': len(levels),
                        'total_nodes': len(question_nodes),
                        'level_distribution': {str(k): len(v) for k, v in levels.items()}
                    }
                )
            
        except Exception as e:
            logger.error(f"层次融合整合失败: {e}")
        
        return None
    
    def _format_level_info(self, level_info: Dict[str, Any]) -> str:
        """格式化层次信息"""
        formatted = []
        for level, info in level_info.items():
            formatted.append(f"{level}:")
            formatted.append(f"  问题: {', '.join(info['questions'])}")
            formatted.append(f"  答案: {', '.join(info['answers'])}")
            formatted.append(f"  关键词: {', '.join(info['keywords'])}")
        return '\n'.join(formatted)
    
    def _parse_integration_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析整合响应"""
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                return data
            
        except Exception as e:
            logger.warning(f"解析整合响应失败: {e}")
        
        return None
    
    def validate_integration_quality(self, tree_level_query: TreeLevelQuery) -> Dict[str, Any]:
        """验证整合质量"""
        validation_result = {
            'overall_score': 0.0,
            'criteria_scores': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # 1. 问题长度和复杂性
            question_length = len(tree_level_query.integrated_question.split())
            if question_length < 10:
                validation_result['issues'].append("整合问题过于简单")
                validation_result['criteria_scores']['complexity'] = 0.3
            elif question_length > 50:
                validation_result['issues'].append("整合问题过于复杂")
                validation_result['criteria_scores']['complexity'] = 0.6
            else:
                validation_result['criteria_scores']['complexity'] = 0.8
            
            # 2. 推理路径完整性
            reasoning_steps = len(tree_level_query.reasoning_path)
            if reasoning_steps < 2:
                validation_result['issues'].append("推理路径过于简单")
                validation_result['criteria_scores']['reasoning'] = 0.4
            elif reasoning_steps > 6:
                validation_result['issues'].append("推理路径过于复杂")
                validation_result['criteria_scores']['reasoning'] = 0.7
            else:
                validation_result['criteria_scores']['reasoning'] = 0.9
            
            # 3. 组件问题整合度
            component_count = len(tree_level_query.component_questions)
            if component_count < 2:
                validation_result['issues'].append("组件问题数量不足")
                validation_result['criteria_scores']['integration'] = 0.3
            else:
                validation_result['criteria_scores']['integration'] = min(0.9, 0.5 + component_count * 0.1)
            
            # 4. 置信度和复杂度评估
            confidence_score = tree_level_query.confidence
            complexity_score = tree_level_query.complexity_score
            
            validation_result['criteria_scores']['confidence'] = confidence_score
            validation_result['criteria_scores']['complexity_balance'] = complexity_score
            
            # 计算总分
            scores = validation_result['criteria_scores']
            validation_result['overall_score'] = sum(scores.values()) / len(scores)
            
            # 生成建议
            if validation_result['overall_score'] < 0.6:
                validation_result['recommendations'].append("建议重新生成整合问题")
            elif validation_result['overall_score'] < 0.8:
                validation_result['recommendations'].append("建议微调问题复杂度")
            else:
                validation_result['recommendations'].append("整合质量良好")
            
        except Exception as e:
            logger.error(f"验证整合质量时出错: {e}")
            validation_result['issues'].append(f"验证过程出错: {str(e)}")
        
        return validation_result 