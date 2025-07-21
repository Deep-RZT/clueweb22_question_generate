#!/usr/bin/env python3
"""
Agent深度推理测试框架 (Agent Depth Reasoning Test Framework)
基于新的6步设计，为智能Agent构建深度推理测试题

核心理念：
- 为智能Agent出题，测试其深度推理能力
- 防止普通LLM直接获取答案
- 通过多层级问题树训练Agent逐步推理
- 最终生成嵌套式综合问题

设计流程：
Step1: 提取3个Short Answer，构建最小精确问题
Step2: 提取Root Query的最小关键词
Step3: 针对每个关键词做Series深度扩展
Step4: 针对所有关键词做Parallel横向扩展  
Step5: 重复构建最多3层问题树
Step6: 糅合所有层级生成最终综合问题
"""

import logging
import json
import time
import re
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import uuid

# 导入循环问题处理器和并行验证器
from utils.circular_problem_handler import CircularProblemHandler
from utils.parallel_keyword_validator import create_parallel_validator

# 设置日志
logger = logging.getLogger(__name__)

@dataclass
class ShortAnswer:
    """短答案数据结构"""
    answer_text: str
    answer_type: str  # noun, number, name, date, location
    confidence: float
    extraction_source: str
    document_position: int

@dataclass
class MinimalKeyword:
    """最小精确关键词"""
    keyword: str
    keyword_type: str  # proper_noun, number, technical_term, date
    uniqueness_score: float  # 唯一性分数
    necessity_score: float   # 必要性分数（移除后是否还能确定答案）
    extraction_context: str
    position_in_query: int

@dataclass
class PreciseQuery:
    """精确问题结构"""
    query_id: str
    query_text: str
    answer: str
    minimal_keywords: List[MinimalKeyword]
    generation_method: str  # web_search, llm_analysis
    validation_passed: bool
    layer_level: int  # 0=root, 1=first_extension, 2=second_extension
    parent_query_id: Optional[str] = None
    extension_type: str = "root"  # root, series, parallel

@dataclass
class QuestionTreeNode:
    """问题树节点"""
    node_id: str
    query: PreciseQuery
    parent_id: Optional[str]
    children_ids: List[str] = field(default_factory=list)
    layer: int = 0
    branch_type: str = "root"  # root, series, parallel

@dataclass
class AgentReasoningTree:
    """Agent推理测试树"""
    tree_id: str
    root_node: QuestionTreeNode
    all_nodes: Dict[str, QuestionTreeNode] = field(default_factory=dict)
    max_layers: int = 3
    final_composite_query: str = ""
    trajectory_records: List[Dict] = field(default_factory=list)

class AgentDepthReasoningFramework:
    """Agent深度推理测试框架主类"""
    
    def __init__(self, api_client=None, search_client=None):
        self.api_client = api_client
        self.search_client = search_client
        self.max_short_answers = 3
        self.max_tree_layers = 3
        self.trajectory_records = []
        
        # 初始化循环问题处理器
        self.circular_handler = CircularProblemHandler()
        
        # 初始化并行关键词验证器
        self.parallel_validator = create_parallel_validator(api_client, max_workers=3) if api_client else None
        
        # 统计信息
        self.stats = {
            'documents_processed': 0,
            'short_answers_extracted': 0,
            'root_queries_generated': 0,
            'minimal_keywords_found': 0,
            'series_extensions_created': 0,
            'parallel_extensions_created': 0,
            'final_composite_queries': 0,
            'total_reasoning_trees': 0
        }
    
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
    
    def set_search_client(self, search_client):
        """设置搜索客户端"""
        self.search_client = search_client
    
    def process_document_for_agent_reasoning(self, document_content: str, document_id: str) -> Dict[str, Any]:
        """
        处理文档，生成Agent推理测试数据
        
        Args:
            document_content: 文档内容
            document_id: 文档ID
            
        Returns:
            完整的Agent推理测试结果
        """
        logger.info(f"🎯 开始为Agent生成深度推理测试题: {document_id}")
        start_time = time.time()
        
        try:
            # Step 1: 提取Short Answer并构建最小精确问题
            logger.info("📍 Step 1: 提取Short Answer并构建Root Query")
            root_queries = self._step1_extract_short_answers_and_build_root_queries(
                document_content, document_id
            )
            
            if not root_queries:
                return self._create_error_result(document_id, "Step 1 failed: No root queries generated")
            
            # 为每个Root Query构建推理树
            reasoning_trees = []
            for i, root_query in enumerate(root_queries):
                logger.info(f"🌳 构建推理树 {i+1}/{len(root_queries)}")
                
                # Step 2: 提取Root Query的最小关键词
                logger.info("📍 Step 2: 提取Root Query最小关键词")
                minimal_keywords = self._step2_extract_minimal_keywords(root_query)
                
                if not minimal_keywords:
                    logger.warning(f"跳过Root Query {root_query.query_id}: 无法提取最小关键词")
                    continue
                
                # 根据关键词数量决定树结构
                if len(minimal_keywords) == 1:
                    logger.info("🔗 单关键词模式: 构建2层Series树")
                    tree = self._build_single_keyword_tree(root_query, minimal_keywords[0])
                else:
                    logger.info(f"🌐 多关键词模式: 构建3层Series+Parallel树 ({len(minimal_keywords)}个关键词)")
                    tree = self._build_multi_keyword_tree(root_query, minimal_keywords)
                
                if tree:
                    # Step 6: 生成最终综合问题
                    logger.info("📍 Step 6: 生成最终综合问题")
                    tree.final_composite_query = self._step6_generate_composite_query(tree)
                    reasoning_trees.append(tree)
                    self.stats['total_reasoning_trees'] += 1
            
            # 计算处理时间
            processing_time = time.time() - start_time
            self.stats['documents_processed'] += 1
            
            # 记录循环处理器统计
            self.circular_handler.log_statistics()
            
            result = self._create_success_result(
                document_id, reasoning_trees, processing_time
            )
            
            # 添加循环处理器统计到结果中
            result['circular_handler_stats'] = self.circular_handler.get_statistics()
            
            return result
            
        except Exception as e:
            logger.error(f"处理文档失败 {document_id}: {e}")
            return self._create_error_result(document_id, str(e))
    
    def _step1_extract_short_answers_and_build_root_queries(
        self, document_content: str, document_id: str
    ) -> List[PreciseQuery]:
        """
        Step 1: 提取Short Answer并构建最小精确问题
        
        要求：
        - 最多3个明确且唯一的Short Answer
        - 为每个Short Answer构建明确问题（使用Web搜索+LLM）
        - 问题包含至少两个关键词确保答案唯一
        - 移除非必要关键词，保留最小精确问题
        """
        if not self.api_client:
            return []
        
        try:
            # 1.1 提取Short Answer
            short_answers = self._extract_unique_short_answers(document_content)
            logger.info(f"提取到 {len(short_answers)} 个Short Answer")
            
            if not short_answers:
                return []
            
            # 1.2 为每个Short Answer构建Root Query
            root_queries = []
            for i, short_answer in enumerate(short_answers[:self.max_short_answers]):
                logger.info(f"为Short Answer '{short_answer.answer_text}' 构建Root Query")
                
                # 使用Web搜索增强问题生成
                root_query = self._build_minimal_precise_query(
                    short_answer, document_content, f"{document_id}_root_{i}"
                )
                
                if root_query and root_query.validation_passed:
                    root_queries.append(root_query)
                    self.stats['root_queries_generated'] += 1
                    
                    # 记录轨迹
                    self._record_trajectory({
                        'step': 'step1_root_query_generation',
                        'query_id': root_query.query_id,
                        'query_text': root_query.query_text,
                        'answer': root_query.answer,
                        'minimal_keywords': [kw.keyword for kw in root_query.minimal_keywords],
                        'keyword_count': len(root_query.minimal_keywords),
                        'validation_passed': root_query.validation_passed
                    })
            
            logger.info(f"✅ Step 1完成: 生成 {len(root_queries)} 个Root Query")
            return root_queries
            
        except Exception as e:
            logger.error(f"Step 1执行失败: {e}")
            return []
    
    def _step2_extract_minimal_keywords(self, root_query: PreciseQuery) -> List[MinimalKeyword]:
        """
        Step 2: 提取Root Query的最小关键词
        
        要求：
        - 提取能确定答案的最小数量关键词
        - 数字、名词等可作为精确答案的关键词
        - 验证每个关键词的必要性
        """
        if not self.api_client:
            return []
        
        try:
            logger.info(f"分析Root Query的最小关键词: {root_query.query_text}")
            
            # 2.1 初步提取关键词
            candidate_keywords = self._extract_candidate_keywords(
                root_query.query_text, root_query.answer
            )
            
            # 2.2 验证关键词必要性（移除测试）
            minimal_keywords = self._validate_keyword_necessity(
                root_query.query_text, root_query.answer, candidate_keywords
            )
            
            # 2.3 关键词唯一性评分
            for keyword in minimal_keywords:
                keyword.uniqueness_score = self._calculate_keyword_uniqueness(
                    keyword.keyword, root_query.answer
                )
            
            logger.info(f"✅ 提取到 {len(minimal_keywords)} 个最小关键词: {[kw.keyword for kw in minimal_keywords]}")
            self.stats['minimal_keywords_found'] += len(minimal_keywords)
            
            # 只有当有关键词时才记录轨迹
            if minimal_keywords:
                self._record_trajectory({
                    'step': 'step2_minimal_keywords',
                    'root_query_id': root_query.query_id,
                    'minimal_keywords': [{
                        'keyword': kw.keyword,
                        'type': kw.keyword_type,
                        'uniqueness_score': kw.uniqueness_score,
                        'necessity_score': kw.necessity_score
                    } for kw in minimal_keywords],
                    'total_count': len(minimal_keywords)
                })
            else:
                # 记录关键词提取失败的情况
                self._record_trajectory({
                    'step': 'step2_minimal_keywords_failed',
                    'root_query_id': root_query.query_id,
                    'error': 'No minimal keywords extracted',
                    'total_count': 0
                })
            
            return minimal_keywords
            
        except Exception as e:
            logger.error(f"Step 2执行失败: {e}")
            return []
    
    def _build_single_keyword_tree(
        self, root_query: PreciseQuery, keyword: MinimalKeyword
    ) -> Optional[AgentReasoningTree]:
        """
        构建单关键词推理树（2层Series）
        
        结构:
        Root → Series1 → Series2
        """
        try:
            tree_id = f"single_{root_query.query_id}_{int(time.time())}"
            
            # 创建根节点
            root_node = QuestionTreeNode(
                node_id=f"{tree_id}_root",
                query=root_query,
                parent_id=None,
                layer=0,
                branch_type="root"
            )
            
            # 创建推理树
            tree = AgentReasoningTree(
                tree_id=tree_id,
                root_node=root_node,
                max_layers=2  # 单关键词只需2层
            )
            tree.all_nodes[root_node.node_id] = root_node
            
            # Step 3: 第一层Series扩展
            series1_query = self._step3_create_series_extension(
                root_query, keyword, layer=1, tree_id=tree_id
            )
            
            if series1_query:
                series1_node = QuestionTreeNode(
                    node_id=f"{tree_id}_series1",
                    query=series1_query,
                    parent_id=root_node.node_id,
                    layer=1,
                    branch_type="series"
                )
                tree.all_nodes[series1_node.node_id] = series1_node
                root_node.children_ids.append(series1_node.node_id)
                
                # 第二层Series扩展
                series1_keywords = self._step2_extract_minimal_keywords(series1_query)
                if series1_keywords:
                    series2_query = self._step3_create_series_extension(
                        series1_query, series1_keywords[0], layer=2, tree_id=tree_id
                    )
                    
                    if series2_query:
                        series2_node = QuestionTreeNode(
                            node_id=f"{tree_id}_series2",
                            query=series2_query,
                            parent_id=series1_node.node_id,
                            layer=2,
                            branch_type="series"
                        )
                        tree.all_nodes[series2_node.node_id] = series2_node
                        series1_node.children_ids.append(series2_node.node_id)
            
            logger.info(f"✅ 单关键词推理树构建完成: {len(tree.all_nodes)} 个节点")
            return tree
            
        except Exception as e:
            logger.error(f"单关键词树构建失败: {e}")
            return None
    
    def _build_multi_keyword_tree(
        self, root_query: PreciseQuery, keywords: List[MinimalKeyword]
    ) -> Optional[AgentReasoningTree]:
        """
        构建多关键词推理树（3层Series+Parallel）
        
        结构:
        Root → Series1/Parallel1 → Series2/Parallel2
        """
        try:
            tree_id = f"multi_{root_query.query_id}_{int(time.time())}"
            
            # 创建根节点
            root_node = QuestionTreeNode(
                node_id=f"{tree_id}_root",
                query=root_query,
                parent_id=None,
                layer=0,
                branch_type="root"
            )
            
            # 创建推理树
            tree = AgentReasoningTree(
                tree_id=tree_id,
                root_node=root_node,
                max_layers=3
            )
            tree.all_nodes[root_node.node_id] = root_node
            
            # Step 3: 针对每个关键词创建Series扩展
            # Step 4: 针对所有关键词创建Parallel扩展
            first_layer_nodes = []
            
            # Series扩展（选择第一个关键词）
            series1_query = self._step3_create_series_extension(
                root_query, keywords[0], layer=1, tree_id=tree_id
            )
            if series1_query:
                series1_node = QuestionTreeNode(
                    node_id=f"{tree_id}_series1",
                    query=series1_query,
                    parent_id=root_node.node_id,
                    layer=1,
                    branch_type="series"
                )
                tree.all_nodes[series1_node.node_id] = series1_node
                root_node.children_ids.append(series1_node.node_id)
                first_layer_nodes.append(series1_node)
                self.stats['series_extensions_created'] += 1
            
            # Parallel扩展（所有关键词）
            parallel_queries = self._step4_create_parallel_extensions(
                root_query, keywords, layer=1, tree_id=tree_id
            )
            for i, parallel_query in enumerate(parallel_queries):
                parallel_node = QuestionTreeNode(
                    node_id=f"{tree_id}_parallel1_{i}",
                    query=parallel_query,
                    parent_id=root_node.node_id,
                    layer=1,
                    branch_type="parallel"
                )
                tree.all_nodes[parallel_node.node_id] = parallel_node
                root_node.children_ids.append(parallel_node.node_id)
                first_layer_nodes.append(parallel_node)
                self.stats['parallel_extensions_created'] += 1
            
            # Step 5: 重复过程构建第二层
            for node in first_layer_nodes:
                self._build_second_layer_extensions(tree, node)
            
            logger.info(f"✅ 多关键词推理树构建完成: {len(tree.all_nodes)} 个节点")
            return tree
            
        except Exception as e:
            logger.error(f"多关键词树构建失败: {e}")
            return None
    
    def _step3_create_series_extension(
        self, parent_query: PreciseQuery, keyword: MinimalKeyword, 
        layer: int, tree_id: str
    ) -> Optional[PreciseQuery]:
        """
        Step 3: 创建Series深度扩展
        
        要求：
        - 针对单个关键词生成新问题
        - 使用Web搜索+LLM分析
        - 新问题不能与Root问题有任何关联
        """
        try:
            logger.info(f"创建Series扩展 (Layer {layer}): 关键词 '{keyword.keyword}'")
            
            # 使用智能Web搜索获取关键词相关信息 (集成循环检测)
            search_context = self._smart_web_search_for_keyword(
                keyword.keyword, parent_query.query_text, parent_query.answer
            )
            
            # 生成无关联的新问题
            extension_query = self._generate_unrelated_query(
                keyword, search_context, layer, f"{tree_id}_series_{layer}"
            )
            
            if extension_query:
                # 验证无关联性
                if self._validate_no_correlation(parent_query.query_text, extension_query.query_text):
                    logger.info(f"✅ Series扩展成功: {extension_query.query_text}")
                    return extension_query
                else:
                    logger.warning("Series扩展失败: 与父问题存在关联")
            
            return None
            
        except Exception as e:
            logger.error(f"Step 3执行失败: {e}")
            return None
    
    def _step4_create_parallel_extensions(
        self, root_query: PreciseQuery, keywords: List[MinimalKeyword], 
        layer: int, tree_id: str
    ) -> List[PreciseQuery]:
        """
        Step 4: 创建Parallel横向扩展
        
        要求：
        - 针对所有关键词分别生成问题
        - 每个问题都不能与Root问题关联
        - 生成n个不同的最精确问题
        """
        try:
            logger.info(f"创建Parallel扩展 (Layer {layer}): {len(keywords)} 个关键词")
            
            parallel_queries = []
            for i, keyword in enumerate(keywords):
                # 为每个关键词生成独立问题 (集成循环检测)
                search_context = self._smart_web_search_for_keyword(
                    keyword.keyword, root_query.query_text, root_query.answer
                )
                
                extension_query = self._generate_unrelated_query(
                    keyword, search_context, layer, f"{tree_id}_parallel_{layer}_{i}"
                )
                
                if extension_query:
                    # 验证与Root问题无关联
                    if self._validate_no_correlation(root_query.query_text, extension_query.query_text):
                        parallel_queries.append(extension_query)
                        logger.info(f"✅ Parallel扩展 {i+1}: {extension_query.query_text}")
                    else:
                        logger.warning(f"Parallel扩展 {i+1} 失败: 与Root问题存在关联")
            
            logger.info(f"✅ 完成Parallel扩展: {len(parallel_queries)}/{len(keywords)} 个问题")
            return parallel_queries
            
        except Exception as e:
            logger.error(f"Step 4执行失败: {e}")
            return []
    
    def _step6_generate_composite_query(self, tree: AgentReasoningTree) -> str:
        """
        Step 6: 生成最终综合问题
        
        要求：
        - 糅合所有层级的query问题
        - 生成嵌套式 (query,query,query...) 综合问题
        - 答案仍然是Root的答案
        - 需要Agent逐步推理才能解答
        """
        try:
            logger.info(f"生成最终综合问题: Tree {tree.tree_id}")
            
            # 收集所有层级的问题
            queries_by_layer = {}
            for node in tree.all_nodes.values():
                layer = node.layer
                if layer not in queries_by_layer:
                    queries_by_layer[layer] = []
                queries_by_layer[layer].append(node.query.query_text)
            
            # 构建嵌套式综合问题
            composite_query = self._build_nested_composite_query(
                queries_by_layer, tree.root_node.query.answer
            )
            
            if composite_query:
                logger.info(f"✅ 最终综合问题生成成功")
                self.stats['final_composite_queries'] += 1
                
                # 记录轨迹
                self._record_trajectory({
                    'step': 'step6_composite_query',
                    'tree_id': tree.tree_id,
                    'original_root_answer': tree.root_node.query.answer,
                    'total_layers': max(queries_by_layer.keys()) + 1,
                    'queries_per_layer': {str(k): len(v) for k, v in queries_by_layer.items()},
                    'composite_query_length': len(composite_query),
                    'complexity_score': self._calculate_complexity_score(composite_query),
                    'composite_query': composite_query
                })
                
                # 记录完整推理树结构
                self._record_complete_tree_trajectory(tree)
                
                return composite_query
            
            return ""
            
        except Exception as e:
            logger.error(f"Step 6执行失败: {e}")
            return ""
    
    def _record_trajectory(self, record: Dict[str, Any]):
        """记录轨迹数据"""
        record['timestamp'] = time.time()
        record['step_id'] = len(self.trajectory_records) + 1
        self.trajectory_records.append(record)
    
    def _record_complete_tree_trajectory(self, tree: AgentReasoningTree):
        """记录完整的推理树轨迹结构"""
        try:
            # 记录推理树的所有节点
            for node_id, node in tree.all_nodes.items():
                if hasattr(node, 'precise_query') and node.precise_query:
                    self._record_trajectory({
                        'step': f'tree_node_layer_{node.layer}',
                        'tree_id': tree.tree_id,
                        'node_id': node_id,
                        'layer': node.layer,
                        'query_text': node.precise_query.query_text,
                        'answer': node.precise_query.answer,
                        'minimal_keywords': [kw.keyword for kw in node.precise_query.minimal_keywords] if hasattr(node.precise_query, 'minimal_keywords') else [],
                        'keyword_count': len(node.precise_query.minimal_keywords) if hasattr(node.precise_query, 'minimal_keywords') else 0,
                        'parent_id': node.parent_id,
                        'children_ids': node.children_ids,
                        'branch_type': node.branch_type if hasattr(node, 'branch_type') else 'unknown',
                        'validation_passed': node.precise_query.validation_passed if hasattr(node.precise_query, 'validation_passed') else True
                    })
            
            # 记录最终综合问题
            if tree.final_composite_query:
                self._record_trajectory({
                    'step': 'final_composite_query_complete',
                    'tree_id': tree.tree_id,
                    'composite_query': tree.final_composite_query,
                    'root_answer': tree.root_answer,
                    'total_nodes': len(tree.all_nodes),
                    'max_depth': tree.max_depth,
                    'complexity_score': tree.complexity_score if hasattr(tree, 'complexity_score') else 0.0
                })
            
            logger.info(f"✅ 完整推理树轨迹记录完成: {len(tree.all_nodes)} 个节点")
            
        except Exception as e:
            logger.error(f"记录完整推理树轨迹失败: {e}")
    
    def _create_success_result(
        self, document_id: str, reasoning_trees: List[AgentReasoningTree], 
        processing_time: float
    ) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            'success': True,
            'document_id': document_id,
            'reasoning_trees': reasoning_trees,
            'processing_time': processing_time,
            'trajectory_records': self.trajectory_records.copy(),
            'statistics': self.stats.copy(),
            'framework_type': 'agent_depth_reasoning',
            'total_trees': len(reasoning_trees),
            'total_composite_queries': sum(1 for tree in reasoning_trees if tree.final_composite_query)
        }
    
    def _create_error_result(self, document_id: str, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'success': False,
            'document_id': document_id,
            'error': error_message,
            'trajectory_records': self.trajectory_records.copy(),
            'statistics': self.stats.copy(),
            'framework_type': 'agent_depth_reasoning'
        }
    
    # ============ 辅助方法占位符 ============
    # 这些方法需要具体实现
    
    def _extract_unique_short_answers(self, document_content: str) -> List[ShortAnswer]:
        """提取唯一短答案"""
        if not self.api_client:
            return []
        
        try:
            # 使用改进的提取提示词，参考WorkFlow设计
            prompt = f"""**TASK: Extract precise, objective facts from this document that can serve as Short Answers for Agent reasoning tests.**

**DOCUMENT TO ANALYZE:**
{document_content[:2000]}

**EXTRACTION REQUIREMENTS (Following WorkFlow):**
1. Extract **3 clear and unique Short Answers** (proper nouns or numbers)
2. Each answer must be **highly specific** (proper nouns, numbers, technical terms)
3. All answers should be **distinctive** and not too broad or ambiguous
4. All answers must be **unique** and not repeated
5. Answers must be **verifiable** through web search (not common sense)

**TARGET ANSWER TYPES (Priority Order):**
1. **PROPER NOUNS**: Companies, organizations, technologies, products, people
2. **NUMBERS**: Specific quantities, measurements, percentages, years, prices
3. **TECHNICAL TERMS**: Scientific terminology, algorithms, model numbers
4. **DATES**: Specific time references, launch dates, establishment dates
5. **LOCATIONS**: Cities, countries, specific places

**QUALITY CRITERIA:**
- Must be **objective facts** (not subjective opinions)
- Must have **single correct answers** (no ambiguity)
- Must be **document-based** (require web search, not common sense)
- Must be **short phrases** (1-8 words maximum)

**Output Format (JSON):**
{{
    "short_answers": [
        {{
            "answer_text": "exact answer text",
            "answer_type": "noun/number/name/date/location",
            "confidence": 0.0-1.0,
            "extraction_source": "surrounding context sentence",
            "document_position": approximate_position,
            "reasoning": "why this makes a good objective answer"
        }}
    ]
}}

**TARGET: Extract exactly 3 high-quality Short Answers that will challenge Agent reasoning.**"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # 解析响应
            parsed_data = self._parse_json_response(response)
            if not parsed_data or 'short_answers' not in parsed_data:
                logger.warning("无法解析Short Answer响应，尝试从原始响应中提取")
                # 尝试从响应中直接提取信息
                return self._extract_short_answers_from_text(response, document_content)
            
            short_answers = []
            for i, sa_data in enumerate(parsed_data['short_answers'][:3]):
                # 安全地解析document_position
                try:
                    doc_position = int(sa_data.get('document_position', i * 100))
                except (ValueError, TypeError):
                    doc_position = i * 100  # 使用默认值
                
                # 安全地解析confidence
                try:
                    confidence = float(sa_data.get('confidence', 0.5))
                except (ValueError, TypeError):
                    confidence = 0.5  # 使用默认值
                
                short_answer = ShortAnswer(
                    answer_text=sa_data.get('answer_text', ''),
                    answer_type=sa_data.get('answer_type', 'unknown'),
                    confidence=confidence,
                    extraction_source=sa_data.get('extraction_source', '')[:200],
                    document_position=doc_position
                )
                if short_answer.answer_text.strip():
                    short_answers.append(short_answer)
            
            self.stats['short_answers_extracted'] += len(short_answers)
            logger.info(f"提取到 {len(short_answers)} 个Short Answer")
            
            return short_answers
            
        except Exception as e:
            logger.error(f"提取Short Answer失败: {e}")
            return []
    
    def _extract_short_answers_from_text(self, response: str, document_content: str) -> List[ShortAnswer]:
        """从响应文本中直接提取Short Answer（后备方法）"""
        try:
            import re
            
            short_answers = []
            
            # 尝试提取类似 "Answer 1:", "Question 1:" 的模式
            answer_patterns = [
                r'(?:Answer|answer)\s*\d*:\s*([^\n\r]+)',
                r'answer_text["\']?\s*:\s*["\']([^"\']+)["\']',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # 专有名词模式
                r'(\d+(?:\.\d+)?\s*(?:seconds|years|GWh|mph|%|dollars?))',  # 数字+单位模式
            ]
            
            for i, pattern in enumerate(answer_patterns):
                matches = re.findall(pattern, response, re.IGNORECASE)
                for j, match in enumerate(matches[:3]):  # 最多3个
                    if len(match.strip()) > 2 and len(match.strip()) < 50:
                        short_answer = ShortAnswer(
                            answer_text=match.strip(),
                            answer_type=self._guess_answer_type(match.strip()),
                            confidence=0.6,  # 较低的置信度
                            extraction_source=f"Pattern extraction from response",
                            document_position=j * 100
                        )
                        short_answers.append(short_answer)
                
                if short_answers:
                    break  # 找到答案就停止
            
            logger.info(f"从文本中提取到 {len(short_answers)} 个Short Answer")
            return short_answers[:3]  # 最多返回3个
            
        except Exception as e:
            logger.error(f"文本提取Short Answer失败: {e}")
            return []
    
    def _guess_answer_type(self, text: str) -> str:
        """猜测答案类型"""
        text_lower = text.lower()
        
        # 数字检测
        if any(char.isdigit() for char in text):
            return "number"
        
        # 时间/日期检测
        time_keywords = ['year', 'date', '20', '19', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
        if any(keyword in text_lower for keyword in time_keywords):
            return "date"
        
        # 地点检测
        location_keywords = ['city', 'country', 'university', 'center', 'institute', 'lab', 'factory']
        if any(keyword in text_lower for keyword in location_keywords):
            return "location"
        
        # 专有名词检测（首字母大写）
        if text and text[0].isupper():
            return "name"
        
        return "noun"
    
    def _build_minimal_precise_query(
        self, short_answer: ShortAnswer, document_content: str, query_id: str
    ) -> Optional[PreciseQuery]:
        """构建最小精确问题"""
        if not self.api_client:
            return None
        
        try:
            logger.info(f"为Short Answer '{short_answer.answer_text}' 构建最小精确问题")
            
            # Step 1: 使用Web搜索增强问题生成
            search_context = ""
            if self.search_client:
                search_results = self.search_client(f"{short_answer.answer_text} definition characteristics")
                if search_results and 'results' in search_results:
                    search_context = " ".join([
                        result.get('content', '')[:200] 
                        for result in search_results['results'][:2]
                    ])
            
            # Step 2: 生成问题（包含至少两个关键词）
            generation_prompt = f"""**TASK: Generate a minimal, precise question for Agent reasoning testing.**

**SHORT ANSWER TO TARGET:** {short_answer.answer_text}
**ANSWER TYPE:** {short_answer.answer_type}
**DOCUMENT CONTEXT:** {short_answer.extraction_source}
**WEB SEARCH CONTEXT:** {search_context[:300] if search_context else "Not available"}

**REQUIREMENTS (Following WorkFlow):**
1. Question must have **exactly ONE correct answer**: "{short_answer.answer_text}"
2. Question must contain **at least TWO explicit keywords** to ensure precision
3. Question must be **based on document/web knowledge** (not common sense)
4. Question must be **solvable** and **unambiguous**
5. Question should **require web search** to verify the answer

**DESIGN PRINCIPLES:**
- Make the question **specific enough** that only "{short_answer.answer_text}" is correct
- Include **contextual constraints** that eliminate other possible answers
- Use **precise language** that requires factual knowledge
- Avoid questions that are too broad or too narrow

**Output Format (JSON):**
{{
    "question_text": "Generated question with at least 2 explicit keywords",
    "minimal_keywords": ["keyword1", "keyword2"],
    "generation_method": "web_search/llm_analysis",
    "confidence": 0.0-1.0,
    "reasoning": "Why this question uniquely identifies the answer"
}}

**TARGET: Generate ONE precise question that challenges Agent reasoning.**"""

            response = self.api_client.generate_response(
                prompt=generation_prompt,
                temperature=0.4,
                max_tokens=600
            )
            
            parsed_data = self._parse_json_response(response)
            if not parsed_data or 'question_text' not in parsed_data:
                logger.warning("无法解析问题生成响应")
                return None
            
            # Step 3: 移除非必要关键词
            question_text = parsed_data['question_text']
            initial_keywords = parsed_data.get('minimal_keywords', [])
            
            # 验证和优化关键词
            optimized_keywords = self._optimize_minimal_keywords(
                question_text, short_answer.answer_text, initial_keywords
            )
            
            # Step 4: 创建MinimalKeyword对象
            minimal_keywords = []
            for i, kw in enumerate(optimized_keywords):
                minimal_keyword = MinimalKeyword(
                    keyword=kw,
                    keyword_type=self._classify_keyword_type(kw),
                    uniqueness_score=0.8,
                    necessity_score=0.9,
                    extraction_context=question_text,
                    position_in_query=question_text.find(kw)
                )
                minimal_keywords.append(minimal_keyword)
            
            # Step 5: 最终验证
            validation_passed = self._validate_root_query(
                question_text, short_answer.answer_text, minimal_keywords
            )
            
            precise_query = PreciseQuery(
                query_id=query_id,
                query_text=question_text,
                answer=short_answer.answer_text,
                minimal_keywords=minimal_keywords,
                generation_method=parsed_data.get('generation_method', 'llm_analysis'),
                validation_passed=validation_passed,
                layer_level=0,
                extension_type="root"
            )
            
            logger.info(f"✅ Root Query构建完成: {question_text}")
            return precise_query
            
        except Exception as e:
            logger.error(f"构建最小精确问题失败: {e}")
            return None
    
    def _extract_candidate_keywords(self, query_text: str, answer: str) -> List[MinimalKeyword]:
        """提取候选关键词"""
        if not self.api_client:
            return []
        
        try:
            # 参考WorkFlow设计：Extract n sub-keywords where n is minimal
            prompt = f"""**TASK: Extract minimal sub-keywords from query for Agent reasoning testing.**

**QUERY:** {query_text}
**ANSWER:** {answer}

**EXTRACTION REQUIREMENTS (Following WorkFlow):**
1. Extract **n sub-keywords** where n is the **MINIMAL number** sufficient to identify answer
2. Keywords must be **HIGHLY SPECIFIC** (proper nouns, numbers, technical terms)
3. Keywords must be **DISTINCTIVE** and not too broad or ambiguous
4. Keywords must be **UNIQUE** and not repeated
5. Each keyword should be able to serve as a child question answer

**KEYWORD PRIORITIES:**
1. **PROPER NOUNS**: Names, companies, organizations, technologies
2. **NUMBERS**: Specific quantities, measurements, years, prices
3. **TECHNICAL TERMS**: Scientific/technical terminology, algorithms
4. **DATES**: Specific time references, periods
5. **LOCATIONS**: Cities, countries, institutions

**EXTRACTION RULES:**
- Focus on **CONTENT WORDS** (nouns, proper nouns, numbers, dates)
- Avoid **QUESTION WORDS**: "what", "which", "who", "when", "where", "how", "why"
- Avoid **COMMON WORDS**: "the", "a", "an", "in", "on", "at", "for", "with"
- Prefer **single-word or short-phrase** keywords (1-3 words)
- Each keyword must be **independently meaningful**

**Output Format (JSON):**
{{
    "candidate_keywords": [
        {{
            "keyword": "exact keyword text",
            "keyword_type": "proper_noun/number/technical_term/date/location",
            "extraction_context": "surrounding phrase or sentence",
            "specificity_score": 0.0-1.0,
            "necessity_reasoning": "why this keyword is necessary"
        }}
    ],
    "minimal_count": "minimum number needed to identify answer"
}}

**TARGET: Extract 2-5 highly specific keywords that together uniquely identify the answer.**"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            parsed_data = self._parse_json_response(response)
            if not parsed_data or 'candidate_keywords' not in parsed_data:
                return []
            
            candidate_keywords = []
            for kw_data in parsed_data['candidate_keywords']:
                # 安全地解析分数
                try:
                    uniqueness_score = float(kw_data.get('specificity_score', 0.5))
                except (ValueError, TypeError):
                    uniqueness_score = 0.5
                
                keyword_text = kw_data.get('keyword', '')
                keyword = MinimalKeyword(
                    keyword=keyword_text,
                    keyword_type=kw_data.get('keyword_type', 'unknown'),
                    uniqueness_score=uniqueness_score,
                    necessity_score=0.8,  # 将在后续验证中计算
                    extraction_context=kw_data.get('extraction_context', ''),
                    position_in_query=query_text.find(keyword_text) if keyword_text else -1
                )
                if keyword.keyword.strip():
                    candidate_keywords.append(keyword)
            
            logger.info(f"提取到 {len(candidate_keywords)} 个候选关键词")
            return candidate_keywords
            
        except Exception as e:
            logger.error(f"提取候选关键词失败: {e}")
            return []
    
    def _validate_keyword_necessity(
        self, query_text: str, answer: str, keywords: List[MinimalKeyword]
    ) -> List[MinimalKeyword]:
        """验证关键词必要性"""
        if not self.api_client or not keywords:
            return keywords
        
        try:
            # 参考WorkFlow：Perform Minimum Keyword Check - masking test
            logger.info(f"验证 {len(keywords)} 个关键词的必要性")
            
            # 使用并行验证器
            if self.parallel_validator:
                necessary_keywords = self.parallel_validator.validate_keywords_parallel(
                    keywords, query_text, answer
                )
            else:
                # 回退到串行验证
                necessary_keywords = []
                for keyword in keywords:
                    # 为每个关键词执行masking测试
                    masking_prompt = f"""**TASK: Perform Minimum Keyword Check for Agent reasoning testing.**

**ORIGINAL QUERY:** {query_text}
**TARGET ANSWER:** {answer}
**KEYWORD TO TEST:** {keyword.keyword}

**MASKING TEST (Following WorkFlow):**
Mask the keyword "{keyword.keyword}" from the query and check if the remaining keywords and descriptions can still uniquely identify the answer "{answer}".

**MODIFIED QUERY (with keyword masked):** {query_text.replace(keyword.keyword, '[MASKED]')}

**EVALUATION CRITERIA:**
1. Can the modified query still **uniquely identify** the answer "{answer}"?
2. Are the **remaining keywords sufficient** to eliminate other possible answers?
3. Does masking this keyword create **ambiguity** or **multiple possible answers**?
4. Is this keyword **essential** for answer precision?

**NECESSITY LEVELS:**
- **ESSENTIAL** (1.0): Masking creates ambiguity, multiple answers possible
- **IMPORTANT** (0.8): Masking reduces precision significantly  
- **HELPFUL** (0.6): Masking has minor impact on precision
- **REDUNDANT** (0.3): Masking has no impact, other keywords sufficient

**Output Format (JSON):**
{{
    "is_necessary": true/false,
    "necessity_score": 0.0-1.0,
    "masking_impact": "essential/important/helpful/redundant",
    "reasoning": "detailed explanation of why this keyword is/isn't necessary",
    "alternative_answers_without_keyword": ["list", "of", "possible", "answers"]
}}

**TARGET: Determine if this keyword is essential for unique answer identification.**"""

                    response = self.api_client.generate_response(
                        prompt=masking_prompt,
                        temperature=0.2,
                        max_tokens=400
                    )
                    
                    parsed_data = self._parse_json_response(response)
                    if parsed_data:
                        is_necessary = parsed_data.get('is_necessary', True)
                        
                        # 安全地解析necessity_score
                        try:
                            necessity_score = float(parsed_data.get('necessity_score', 0.8))
                        except (ValueError, TypeError):
                            necessity_score = 0.8
                        
                        # 更新关键词的必要性分数
                        keyword.necessity_score = necessity_score
                        
                        # 只保留必要的关键词（分数 > 0.5）
                        if is_necessary and necessity_score > 0.5:
                            necessary_keywords.append(keyword)
                            logger.info(f"✅ 关键词 '{keyword.keyword}' 是必要的 (分数: {necessity_score:.2f})")
                        else:
                            logger.info(f"❌ 关键词 '{keyword.keyword}' 不是必要的 (分数: {necessity_score:.2f})")
                    else:
                        # 解析失败，保守地保留关键词
                        necessary_keywords.append(keyword)
            
            logger.info(f"验证完成: {len(necessary_keywords)}/{len(keywords)} 个关键词是必要的")
            return necessary_keywords
            
        except Exception as e:
            logger.error(f"验证关键词必要性失败: {e}")
            return keywords
    
    def _calculate_keyword_uniqueness(self, keyword: str, answer: str) -> float:
        """计算关键词唯一性分数"""
        # TODO: 实现唯一性计算
        return 0.8
    
    def _web_search_for_keyword(self, keyword: str) -> str:
        """为关键词进行Web搜索"""
        if not self.search_client:
            return f"Search context for {keyword}"
        
        try:
            # 构建搜索查询
            search_query = f"{keyword} definition characteristics properties"
            
            # 执行搜索
            search_results = self.search_client(search_query, max_results=3)
            
            if search_results and 'results' in search_results:
                # 提取搜索内容
                search_content = []
                for result in search_results['results'][:3]:
                    content = result.get('content', '')
                    snippet = result.get('snippet', '')
                    combined = f"{snippet} {content}"[:300]
                    if combined.strip():
                        search_content.append(combined)
                
                search_context = " ".join(search_content)
                logger.info(f"🌐 Web搜索 '{keyword}': 获取 {len(search_content)} 个结果")
                return search_context
            else:
                logger.warning(f"Web搜索 '{keyword}' 无结果")
                return f"Search context for {keyword}"
                
        except Exception as e:
            logger.error(f"Web搜索 '{keyword}' 失败: {e}")
            return f"Search context for {keyword}"
    
    def _smart_web_search_for_keyword(self, keyword: str, parent_question: str, parent_answer: str) -> str:
        """智能Web搜索 - 集成循环问题处理器"""
        
        # 如果没有搜索客户端，使用简单上下文
        if not self.search_client:
            return f"Search context for {keyword}"
        
        try:
            # 1. 使用循环问题处理器评估和处理循环风险
            search_results = self.circular_handler.handle_circular_risk(
                keyword, parent_question, parent_answer, self
            )
            
            # 2. 如果循环处理器返回None，表示跳过该关键词
            if search_results is None:
                logger.warning(f"🚫 循环风险过高，跳过关键词: {keyword}")
                self.stats['circular_reasoning_prevented'] = self.stats.get('circular_reasoning_prevented', 0) + 1
                return ""  # 返回空字符串表示跳过
            
            # 3. 处理搜索结果
            if search_results:
                search_content = []
                for result in search_results[:3]:  # 最多使用3个结果
                    content = result.get('content', '')
                    snippet = result.get('snippet', '')
                    combined = f"{snippet} {content}"[:300]
                    if combined.strip():
                        search_content.append(combined)
                
                if search_content:
                    search_context = " ".join(search_content)
                    logger.info(f"🌐 智能搜索 '{keyword}': 获取 {len(search_content)} 个结果 (循环已检测)")
                    return search_context
            
            # 4. 如果没有有效结果，回退到原始搜索
            logger.info(f"🔄 循环处理无结果，回退到标准搜索: {keyword}")
            return self._web_search_for_keyword(keyword)
                
        except Exception as e:
            logger.error(f"智能搜索 '{keyword}' 失败: {e}")
            # 出错时回退到标准搜索
            return self._web_search_for_keyword(keyword)
    
    def search(self, query: str, max_results: int = 3):
        """提供给循环处理器使用的搜索接口"""
        if not self.search_client:
            return None
        
        try:
            results = self.search_client(query, max_results=max_results)
            if results and 'results' in results:
                return results['results']
            return None
        except Exception as e:
            logger.error(f"搜索接口调用失败: {e}")
            return None
    
    def _generate_unrelated_query(
        self, keyword: MinimalKeyword, search_context: str, 
        layer: int, query_id: str
    ) -> Optional[PreciseQuery]:
        """生成无关联问题"""
        if not self.api_client:
            return None
        
        try:
            logger.info(f"为关键词 '{keyword.keyword}' 生成无关联问题 (Layer {layer})")
            
            # 参考WorkFlow设计：设计对应问题，确保无关联性和无循环推理
            generation_prompt = f"""**TASK: Generate an unrelated question for Agent reasoning testing with NO CIRCULAR REASONING.**

**TARGET KEYWORD (must be the answer):** {keyword.keyword}
**KEYWORD TYPE:** {keyword.keyword_type}
**WEB SEARCH CONTEXT:** {search_context[:500]}
**LAYER LEVEL:** {layer}

**CRITICAL REQUIREMENTS (Following WorkFlow):**
1. The question must have **"{keyword.keyword}"** as the ONLY correct answer
2. The question must be **completely unrelated** to any parent questions
3. The question must be based on **web search context** (not original document)
4. The question must be **solvable** and **unambiguous**
5. The question must require **web search verification** to answer

**CIRCULAR REASONING PREVENTION (CRITICAL):**
- **AVOID entity-attribute swaps**: If parent asks "What company was founded in 2003?" → DON'T ask "When was Tesla founded?"
- **AVOID reverse relationships**: If parent asks "What acceleration does Model S have?" → DON'T ask "Which car has 2.1 second acceleration?"
- **AVOID temporal inversions**: If parent mentions year/date → DON'T ask about events in that year
- **AVOID attribute reversals**: If parent asks about property X of entity Y → DON'T ask about entity with property X

**NO CORRELATION RULES:**
- **NO shared topic** with parent questions
- **NO shared context** with parent questions  
- **NO similar wording** or phrasing patterns
- **NO conceptual overlap** with parent domain
- **USE different knowledge domain** entirely
- **NO logical dependency** between questions

**GENERATION STRATEGY:**
- Base the question on **WEB SEARCH CONTEXT** only
- Focus on **completely different aspects** of the keyword
- Use **different knowledge domains** (if keyword is from tech domain, ask about geography/history/etc.)
- Ensure **no logical path** connects the questions
- Make answer verification require **external search**

**SAFE DESIGN PATTERNS:**
- Domain Switch: Tech keyword → Ask about geography/history/biology
- Context Switch: Business keyword → Ask about science/arts/sports  
- Time Switch: Modern keyword → Ask about historical/ancient context
- Scale Switch: Macro keyword → Ask about micro/personal level

**DANGEROUS PATTERNS TO AVOID:**
- Attribute reversal: "What X does Y have?" ↔ "What Y has X?"
- Temporal reversal: "What happened in year Y?" ↔ "When did X happen?"
- Entity-property swap: "Which entity has property P?" ↔ "What property does entity E have?"

**Output Format (JSON):**
{{
    "question_text": "Generated unrelated question",
    "answer": "{keyword.keyword}",
    "minimal_keywords": ["extracted", "keywords"],
    "generation_method": "web_search",
    "layer_level": {layer},
    "no_correlation_verified": true/false,
    "circular_reasoning_check": "explanation of how circular reasoning was avoided",
    "domain_switch": "explanation of knowledge domain switch",
    "reasoning": "Why this question is completely unrelated and non-circular"
}}

**TARGET: Generate ONE completely unrelated question with NO circular reasoning that has "{keyword.keyword}" as the definitive answer.**"""

            response = self.api_client.generate_response(
                prompt=generation_prompt,
                temperature=0.5,  # 更高创造性，确保多样性
                max_tokens=600
            )
            
            parsed_data = self._parse_json_response(response)
            if not parsed_data or 'question_text' not in parsed_data:
                logger.warning("无法解析无关联问题生成响应")
                return None
            
            # 创建MinimalKeyword对象
            minimal_keywords = []
            for kw in parsed_data.get('minimal_keywords', []):
                minimal_keyword = MinimalKeyword(
                    keyword=kw,
                    keyword_type=self._classify_keyword_type(kw),
                    uniqueness_score=0.7,
                    necessity_score=0.8,
                    extraction_context=parsed_data['question_text'],
                    position_in_query=parsed_data['question_text'].find(kw)
                )
                minimal_keywords.append(minimal_keyword)
            
            # 验证问题质量
            validation_passed = self._validate_unrelated_query(
                parsed_data['question_text'], 
                keyword.keyword,
                minimal_keywords
            )
            
            precise_query = PreciseQuery(
                query_id=query_id,
                query_text=parsed_data['question_text'],
                answer=keyword.keyword,
                minimal_keywords=minimal_keywords,
                generation_method="web_search",
                validation_passed=validation_passed,
                layer_level=layer,
                extension_type="series" if "series" in query_id else "parallel"
            )
            
            logger.info(f"✅ 无关联问题生成: {parsed_data['question_text']}")
            return precise_query
            
        except Exception as e:
            logger.error(f"生成无关联问题失败: {e}")
            return None
    
    def _validate_no_correlation(self, query1: str, query2: str) -> bool:
        """验证两个问题无关联"""
        if not self.api_client:
            return True  # 无法验证时保守返回True
        
        try:
            # 首先进行循环检测
            has_circular_reasoning = self._detect_circular_reasoning(query1, query2)
            if has_circular_reasoning:
                logger.warning(f"❌ 检测到循环推理风险")
                return False
            
            # 然后进行关联性检测
            correlation_prompt = f"""**TASK: Verify NO CORRELATION and NO CIRCULAR REASONING between two questions for Agent reasoning testing.**

**PARENT QUESTION:** {query1}
**CHILD QUESTION:** {query2}

**CRITICAL CHECKS:**
1. **CIRCULAR REASONING CHECK**: Do these questions form a circular reasoning loop?
   - Example BAD: Q1="Which company was founded in 2003?" A1="Tesla" → Q2="What year was Tesla founded?" A2="2003"
   - Example BAD: Q1="What acceleration can Model S achieve?" A1="2.1 seconds" → Q2="Which Tesla model has 2.1 second acceleration?" A2="Model S"

2. **CORRELATION CHECK**: Are the questions related in topic or context?
   - Questions must address **completely different domains**
   - No shared entities, attributes, or logical connections

**EVALUATION CRITERIA:**
1. **Circular Reasoning**: Would answering both questions create a logical loop?
2. **Topic Independence**: Do questions address completely different topics?
3. **Entity Overlap**: Do questions share the same entities or attributes?
4. **Logical Dependency**: Does one question's answer help answer the other?
5. **Domain Separation**: Are questions in completely different knowledge domains?

**FAILURE CONDITIONS (return false):**
- Any circular reasoning detected
- Shared entities with swapped attributes
- Questions that mutually inform each other
- Same knowledge domain with different angles

**Output Format (JSON):**
{{
    "has_circular_reasoning": true/false,
    "has_correlation": true/false,
    "correlation_score": 0.0-1.0,
    "circular_reasoning_explanation": "explanation if circular reasoning detected",
    "shared_entities": ["list", "of", "shared", "entities"],
    "validation_passed": true/false,
    "reasoning": "detailed explanation"
}}

**TARGET: Ensure questions are completely independent with NO circular reasoning.**"""

            response = self.api_client.generate_response(
                prompt=correlation_prompt,
                temperature=0.2,
                max_tokens=500
            )
            
            parsed_data = self._parse_json_response(response)
            if parsed_data:
                has_circular_reasoning = parsed_data.get('has_circular_reasoning', False)
                has_correlation = parsed_data.get('has_correlation', False)
                
                # 安全地解析correlation_score
                try:
                    correlation_score = float(parsed_data.get('correlation_score', 0.0))
                except (ValueError, TypeError):
                    correlation_score = 0.0
                
                validation_passed = parsed_data.get('validation_passed', True)
                
                # 验证通过条件：无循环推理 且 无关联 且 低相关性分数
                no_issues = (not has_circular_reasoning and 
                           not has_correlation and 
                           correlation_score < 0.3 and 
                           validation_passed)
                
                if no_issues:
                    logger.info(f"✅ 无关联和循环验证通过 (相关性分数: {correlation_score:.2f})")
                else:
                    if has_circular_reasoning:
                        logger.warning(f"❌ 检测到循环推理: {parsed_data.get('circular_reasoning_explanation', 'Unknown')}")
                    else:
                        logger.warning(f"❌ 检测到关联性 (相关性分数: {correlation_score:.2f})")
                
                return no_issues
            else:
                # 解析失败，保守返回False
                logger.warning("无法解析关联性验证响应")
                return False
                
        except Exception as e:
            logger.error(f"验证关联性失败: {e}")
            return True  # 验证失败时保守返回True
    
    def _detect_circular_reasoning(self, query1: str, query2: str) -> bool:
        """检测循环推理风险"""
        try:
            # 预处理
            q1_lower = query1.lower()
            q2_lower = query2.lower()
            
            # 移除标点符号并分词
            import re
            q1_words = set(re.findall(r'\b\w+\b', q1_lower))
            q2_words = set(re.findall(r'\b\w+\b', q2_lower))
            
            # 扩展的停用词表
            stop_words = {
                'what', 'which', 'who', 'when', 'where', 'how', 'why', 'the', 'a', 'an', 'and', 'or', 'but', 
                'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'can', 'could',
                'will', 'would', 'should', 'may', 'might', 'has', 'have', 'had', 'do', 'does', 'did', 'be',
                'been', 'being', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
                'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
            
            # 提取有意义的词汇
            q1_meaningful = q1_words - stop_words
            q2_meaningful = q2_words - stop_words
            
            # 移除单字母词汇
            q1_meaningful = {word for word in q1_meaningful if len(word) > 1}
            q2_meaningful = {word for word in q2_meaningful if len(word) > 1}
            
            # 检查重叠词汇
            overlap = q1_meaningful & q2_meaningful
            
            # 循环推理模式检测
            circular_patterns = [
                # 模式1：实体-属性交换
                self._detect_entity_attribute_swap(q1_lower, q2_lower, overlap),
                
                # 模式2：时间-事件交换  
                self._detect_temporal_event_swap(q1_lower, q2_lower, overlap),
                
                # 模式3：因果关系逆转
                self._detect_cause_effect_reversal(q1_lower, q2_lower, overlap),
                
                # 模式4：高重叠率（保留原有检测）
                self._detect_high_overlap(q1_meaningful, q2_meaningful, overlap)
            ]
            
            # 如果任何模式检测为True，则认为存在循环风险
            has_circular = any(circular_patterns)
            
            if has_circular:
                logger.info(f"循环推理检测：重叠词汇 {overlap}, 模式检测结果 {circular_patterns}")
            
            return has_circular
            
        except Exception as e:
            logger.error(f"循环推理检测失败: {e}")
            return False
    
    def _detect_entity_attribute_swap(self, q1: str, q2: str, overlap: set) -> bool:
        """检测实体-属性交换模式"""
        # 实体词汇（通常是专有名词）
        entity_indicators = ['tesla', 'spacex', 'apple', 'google', 'microsoft', 'amazon', 'meta', 'nvidia', 
                           'model', 'iphone', 'galaxy', 'company', 'corporation', 'manufacturer']
        
        # 属性词汇
        attribute_indicators = ['founded', 'established', 'created', 'built', 'year', 'when', 'where', 'located', 
                              'headquartered', 'based', 'price', 'cost', 'acceleration', 'speed', 'capacity',
                              'produces', 'makes', 'manufactures', 'electric', 'vehicle', 'product', 'type']
        
        # 检查是否有实体和属性的交换
        q1_has_entity = any(entity in q1 for entity in entity_indicators)
        q2_has_entity = any(entity in q2 for entity in entity_indicators)
        q1_has_attribute = any(attr in q1 for attr in attribute_indicators)
        q2_has_attribute = any(attr in q2 for attr in attribute_indicators)
        
        # 特殊检测：产品-制造商循环
        if self._detect_product_manufacturer_cycle(q1, q2, overlap):
            return True
        
        # 特殊检测：地点-实体循环
        if self._detect_location_entity_cycle(q1, q2, overlap):
            return True
        
        # 如果两个问题都涉及实体和属性，且有重叠，可能是交换模式
        if (q1_has_entity and q2_has_entity and q1_has_attribute and q2_has_attribute and 
            len(overlap) >= 1):  # 降低阈值从2到1
            return True
        
        return False
    
    def _detect_temporal_event_swap(self, q1: str, q2: str, overlap: set) -> bool:
        """检测时间-事件交换模式"""
        time_indicators = ['year', 'when', 'date', '19', '20', 'founded', 'established', 'created']
        event_indicators = ['company', 'organization', 'founded', 'established', 'event', 'happened']
        
        # 检查时间相关的问题模式
        q1_has_time = any(time_word in q1 for time_word in time_indicators)
        q2_has_time = any(time_word in q2 for time_word in time_indicators)
        q1_has_event = any(event_word in q1 for event_word in event_indicators)
        q2_has_event = any(event_word in q2 for event_word in event_indicators)
        
        # 经典时间-事件循环模式
        if ((q1_has_time and q2_has_time) or (q1_has_event and q2_has_event)) and len(overlap) >= 1:
            # 进一步检查是否是"什么时候发生"和"什么在某时间发生"的模式
            if (('when' in q1 or 'year' in q1) and ('founded' in q2 or 'established' in q2)) or \
               (('when' in q2 or 'year' in q2) and ('founded' in q1 or 'established' in q1)):
                return True
        
        return False
    
    def _detect_cause_effect_reversal(self, q1: str, q2: str, overlap: set) -> bool:
        """检测因果关系逆转模式"""
        # 这里简化处理，主要检查明显的逆向关系
        reversal_patterns = [
            ('produces', 'made by'),
            ('makes', 'manufactured by'),  
            ('owns', 'owned by'),
            ('creates', 'created by'),
            ('develops', 'developed by')
        ]
        
        for forward, reverse in reversal_patterns:
            if ((forward in q1 and reverse in q2) or (reverse in q1 and forward in q2)) and len(overlap) >= 1:
                return True
        
        return False
    
    def _detect_high_overlap(self, q1_meaningful: set, q2_meaningful: set, overlap: set) -> bool:
        """检测高重叠率"""
        if len(q1_meaningful) == 0 or len(q2_meaningful) == 0:
            return False
        
        overlap_ratio = len(overlap) / max(len(q1_meaningful), len(q2_meaningful))
        
        # 降低阈值，更敏感地检测重叠
        if overlap_ratio > 0.4:  # 从0.6降低到0.4
            return True
        
        # 特别检查：如果有3个或更多重叠的关键词，也认为是高风险
        if len(overlap) >= 3:
            return True
        
        return False
    
    def _detect_product_manufacturer_cycle(self, q1: str, q2: str, overlap: set) -> bool:
        """检测产品-制造商循环"""
        # 产品相关词汇
        product_words = ['model', 'product', 'vehicle', 'car', 'phone', 'device', 'electric']
        
        # 制造商相关词汇
        manufacturer_words = ['company', 'manufacturer', 'makes', 'produces', 'tesla', 'apple', 'google']
        
        # 检测模式：问A公司生产什么 vs 问什么产品由A公司生产
        q1_has_product = any(word in q1 for word in product_words)
        q2_has_product = any(word in q2 for word in product_words)
        q1_has_manufacturer = any(word in q1 for word in manufacturer_words)
        q2_has_manufacturer = any(word in q2 for word in manufacturer_words)
        
        # 如果两个问题都涉及产品和制造商关系，且有重叠实体
        if ((q1_has_product and q2_has_manufacturer) or (q1_has_manufacturer and q2_has_product)) and len(overlap) >= 1:
            return True
        
        return False
    
    def _detect_location_entity_cycle(self, q1: str, q2: str, overlap: set) -> bool:
        """检测地点-实体循环"""
        # 地点相关词汇
        location_words = ['where', 'located', 'headquartered', 'based', 'headquarters', 'austin', 'california', 'texas']
        
        # 实体相关词汇
        entity_words = ['company', 'organization', 'tesla', 'spacex', 'google', 'apple']
        
        # 检测模式：问实体在哪里 vs 问什么实体在某地
        q1_has_location = any(word in q1 for word in location_words)
        q2_has_location = any(word in q2 for word in location_words)
        q1_has_entity = any(word in q1 for word in entity_words)
        q2_has_entity = any(word in q2 for word in entity_words)
        
        # 如果两个问题都涉及地点和实体关系，且有重叠
        if ((q1_has_location and q2_has_entity) or (q1_has_entity and q2_has_location)) and len(overlap) >= 1:
            return True
        
        return False
    
    def _build_second_layer_extensions(self, tree: AgentReasoningTree, parent_node: QuestionTreeNode):
        """构建第二层扩展"""
        # TODO: 实现第二层扩展构建
        pass
    
    def _build_nested_composite_query(self, queries_by_layer: Dict[int, List[str]], root_answer: str) -> str:
        """构建嵌套式综合问题"""
        if not self.api_client or not queries_by_layer:
            return "Composite query placeholder"
        
        try:
            logger.info(f"构建嵌套式综合问题，目标答案: {root_answer}")
            
            # 收集所有层级的问题
            all_queries = []
            layer_summary = []
            
            for layer in sorted(queries_by_layer.keys()):
                queries = queries_by_layer[layer]
                all_queries.extend(queries)
                layer_summary.append(f"Layer {layer}: {len(queries)} queries")
            
            # 生成有逻辑链条的综合问题 
            composite_prompt = f"""**TASK: Create a LOGICAL REASONING CHAIN for Agent testing (NOT simple concatenation).**

**TARGET FINAL ANSWER:** {root_answer}
**AVAILABLE SUB-QUESTIONS:** {chr(10).join([f"Q{i+1}: {q}" for i, q in enumerate(all_queries)])}
**LAYER STRUCTURE:** {' | '.join(layer_summary)}

**CRITICAL REQUIREMENTS for AGENT REASONING:**
1. **LOGICAL CHAIN**: Each step's answer must be INPUT for next step
2. **DEPENDENCY**: Question2 depends on Answer1, Question3 depends on Answer2, etc.
3. **NO SHORTCUTS**: Agent cannot jump directly to final answer
4. **STEP-BY-STEP**: Must solve in sequence to reach {root_answer}

**FORBIDDEN PATTERNS (avoid these):**
❌ "First find X, then find Y, then find Z" (independent questions)
❌ "Determine A, understand B, evaluate C" (no logical connection)  
❌ Simple concatenation without reasoning dependencies

**REQUIRED PATTERN (use this):**
✅ "To find {root_answer}, you must follow this reasoning chain:
Step 1: First determine [KEY_INFO_1] by solving [SUB_QUESTION_1]
Step 2: Use [KEY_INFO_1] to identify [KEY_INFO_2] through [SUB_QUESTION_2]  
Step 3: Apply [KEY_INFO_2] to finally determine {root_answer}"

**REASONING CHAIN STRUCTURE:**
Each step must provide information NEEDED for the next step.
Answer₁ → Input₂ → Answer₂ → Input₃ → Final Answer

**EXAMPLES of GOOD REASONING CHAINS:**
- "To identify the company, first find what technology was developed in year X, then determine which company pioneered that technology in location Y."
- "To determine the temperature, first identify the instrument type from description Z, then find which mission used that instrument, then lookup the operating temperature."

**Output Format (JSON):**
{{
    "composite_query": "Logical reasoning chain question requiring genuine step-by-step solving",
    "reasoning_steps": ["Step 1: Get X to use in Step 2", "Step 2: Use X to get Y for Step 3", "Step 3: Use Y to find {root_answer}"],
    "dependency_chain": "Answer1 → Question2 → Answer2 → Question3 → {root_answer}",
    "agent_difficulty": "medium/hard", 
    "prevents_direct_answer": "Why Agent must solve step-by-step instead of direct answer",
    "final_answer_confirmed": "{root_answer}"
}}

**TARGET: Generate ONE reasoning chain that requires genuine sequential Agent reasoning to reach {root_answer}.**"""

            response = self.api_client.generate_response(
                prompt=composite_prompt,
                temperature=0.6,  # 较高创造性用于复杂问题构建
                max_tokens=800
            )
            
            parsed_data = self._parse_json_response(response)
            if parsed_data and 'composite_query' in parsed_data:
                composite_query = parsed_data['composite_query']
                reasoning_steps = parsed_data.get('reasoning_steps', [])
                difficulty = parsed_data.get('agent_difficulty', 'medium')
                
                logger.info(f"✅ 嵌套式综合问题生成完成")
                logger.info(f"  难度级别: {difficulty}")
                logger.info(f"  推理步骤: {len(reasoning_steps)} 步")
                logger.info(f"  问题长度: {len(composite_query)} 字符")
                
                return composite_query
            else:
                logger.warning("无法解析综合问题生成响应")
                # 生成简单的嵌套问题作为后备
                return self._generate_simple_nested_query(all_queries, root_answer)
                
        except Exception as e:
            logger.error(f"构建嵌套式综合问题失败: {e}")
            return self._generate_simple_nested_query(queries_by_layer.get(0, ["What is the answer?"]), root_answer)
    
    def _generate_simple_nested_query(self, queries: List[str], root_answer: str) -> str:
        """生成简单的嵌套问题作为后备"""
        if not queries:
            return f"What is the answer that requires multi-step reasoning to identify {root_answer}?"
        
        # 选择前3个问题构建简单嵌套
        selected_queries = queries[:3]
        if len(selected_queries) == 1:
            return f"To determine the final answer, consider: {selected_queries[0]}"
        elif len(selected_queries) == 2:
            return f"Given that {selected_queries[0]}, and considering {selected_queries[1]}, what is the final answer?"
        else:
            return f"To identify the target answer, first determine {selected_queries[0]}, then analyze {selected_queries[1]}, and finally evaluate {selected_queries[2]}. What is the final answer?"
    
    def _calculate_complexity_score(self, composite_query: str) -> float:
        """计算复杂度分数"""
        try:
            # 基于多个因素计算复杂度分数
            length_score = min(len(composite_query) / 500, 1.0)  # 长度因子
            
            # 嵌套层次分析
            nesting_indicators = ['given that', 'considering', 'first determine', 'then analyze', 'finally']
            nesting_score = sum(1 for indicator in nesting_indicators if indicator in composite_query.lower()) / len(nesting_indicators)
            
            # 推理关键词分析
            reasoning_keywords = ['requires', 'analyze', 'determine', 'evaluate', 'identify', 'consider']
            reasoning_score = sum(1 for keyword in reasoning_keywords if keyword in composite_query.lower()) / len(reasoning_keywords)
            
            # 综合计算
            complexity = (length_score * 0.3 + nesting_score * 0.4 + reasoning_score * 0.3)
            
            return min(max(complexity, 0.1), 1.0)  # 限制在0.1-1.0范围内
            
        except Exception as e:
            logger.error(f"计算复杂度分数失败: {e}")
            return 0.8
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # 尝试提取JSON部分
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
            
            try:
                # 尝试查找并修复常见的JSON格式问题
                import re
                # 移除可能的markdown代码块标记
                cleaned = re.sub(r'```json\s*|\s*```', '', response)
                cleaned = cleaned.strip()
                
                # 找到最外层的大括号
                json_start = cleaned.find('{')
                json_end = cleaned.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = cleaned[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
            
            logger.warning(f"无法解析JSON响应: {response[:200]}...")
            return None
    
    def _classify_keyword_type(self, keyword: str) -> str:
        """分类关键词类型"""
        keyword_lower = keyword.lower()
        
        # 数字检测
        if any(char.isdigit() for char in keyword):
            return "number"
        
        # 技术术语检测（包含特定后缀）
        tech_suffixes = ['algorithm', 'protocol', 'system', 'technology', 'method']
        if any(suffix in keyword_lower for suffix in tech_suffixes):
            return "technical_term"
        
        # 日期检测
        date_indicators = ['year', 'date', '20', '19']
        if any(indicator in keyword_lower for indicator in date_indicators):
            return "date"
        
        # 地点检测
        location_indicators = ['city', 'country', 'location', 'university', 'center']
        if any(indicator in keyword_lower for indicator in location_indicators):
            return "location"
        
        # 专有名词检测（首字母大写）
        if keyword and keyword[0].isupper():
            return "proper_noun"
        
        return "noun"
    
    def _optimize_minimal_keywords(self, question_text: str, answer: str, initial_keywords: List[str]) -> List[str]:
        """优化最小关键词列表"""
        if not initial_keywords:
            return []
        
        # 简单的优化：移除过于通用的词
        generic_words = {'the', 'a', 'an', 'is', 'was', 'are', 'were', 'what', 'which', 'how', 'system', 'method'}
        
        optimized = []
        for keyword in initial_keywords:
            if keyword.lower() not in generic_words and len(keyword) > 2:
                optimized.append(keyword)
        
        # 确保至少有一个关键词
        if not optimized and initial_keywords:
            optimized = [initial_keywords[0]]
        
        return optimized[:5]  # 最多5个关键词
    
    def _validate_root_query(self, question_text: str, answer: str, keywords: List[MinimalKeyword]) -> bool:
        """验证Root Query的质量"""
        try:
            # 基本验证
            if not question_text or not answer or not keywords:
                return False
            
            # 长度检查
            if len(question_text) < 10 or len(answer) < 2:
                return False
            
            # 关键词数量检查
            if len(keywords) < 1:
                return False
            
            # 答案包含检查（答案应该不在问题中直接出现）
            if answer.lower() in question_text.lower():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证Root Query失败: {e}")
            return False
    
    def _validate_unrelated_query(self, question_text: str, answer: str, keywords: List[MinimalKeyword]) -> bool:
        """验证无关联问题的质量"""
        try:
            # 复用Root Query验证逻辑
            basic_validation = self._validate_root_query(question_text, answer, keywords)
            
            if not basic_validation:
                return False
            
            # 额外的无关联性检查
            # 确保问题中包含答案相关的关键词
            answer_in_question = any(answer.lower() in kw.keyword.lower() or kw.keyword.lower() in answer.lower() 
                                   for kw in keywords)
            
            return not answer_in_question  # 答案不应该直接出现在关键词中
            
        except Exception as e:
            logger.error(f"验证无关联问题失败: {e}")
            return False
    
    def _build_second_layer_extensions(self, tree: AgentReasoningTree, parent_node: QuestionTreeNode):
        """构建第二层扩展"""
        try:
            logger.info(f"为节点 {parent_node.node_id} 构建第二层扩展")
            
            # 提取父节点的关键词
            parent_keywords = self._step2_extract_minimal_keywords(parent_node.query)
            
            if not parent_keywords:
                logger.warning(f"无法为节点 {parent_node.node_id} 提取关键词")
                return
            
            # 为第一个关键词创建Series扩展
            if parent_keywords:
                series_query = self._step3_create_series_extension(
                    parent_node.query, parent_keywords[0], layer=2, 
                    tree_id=f"{tree.tree_id}_series2"
                )
                
                if series_query:
                    series_node = QuestionTreeNode(
                        node_id=f"{parent_node.node_id}_series2",
                        query=series_query,
                        parent_id=parent_node.node_id,
                        layer=2,
                        branch_type="series"
                    )
                    tree.all_nodes[series_node.node_id] = series_node
                    parent_node.children_ids.append(series_node.node_id)
                    self.stats['series_extensions_created'] += 1
            
            logger.info(f"✅ 第二层扩展构建完成")
            
        except Exception as e:
            logger.error(f"构建第二层扩展失败: {e}") 