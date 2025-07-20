#!/usr/bin/env python3
"""
Linguistic Deep Query Framework
基于语言学+科学化的Short Answer Deep Research Query构建流程

实现5个层级的问题深化流程：
层级0️⃣：原始文档
层级1️⃣：初始问题与Short Answer抽取
层级2️⃣及之后：系列深化与并行扩展（基于关键词替换）

核心思想：通过搜索获得的描述来替换问题中的关键词，使问题更加抽象和间接
"""

import logging
import json
import time
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Integrated prompt templates from complete_prompt_template_system.py
class IntegratedPromptTemplates:
    """集成的提示词模板系统"""
    
    @staticmethod
    def get_prompt_1_short_answer_extraction(text_content: str) -> str:
        """Prompt-1: Short Answer Extraction & Initial Question Generation"""
        return f"""**Given the following text snippet:**
【TEXT_CONTENT】
{text_content[:2000]}

**Task:**
1. Extract **3 clear and unique Short Answers** (proper nouns or numbers) from the text.
2. For each Short Answer, construct a **clear question**.

**Requirements:**
* Each question must contain at least **two explicit keywords** to ensure the Short Answer is precise, unique, and requires no ambiguous interpretation.
* All extracted keywords must be **highly specific** (e.g., proper nouns, numbers, technical terms), **distinctive**, and **unique** (not repeated).
* The query must be based on the original document (requiring a web search, not answerable by common sense) and have only one correct, solvable answer.

**Output Format:**
Question 1: [Generated question with at least 2 explicit keywords]
Answer 1: [Specific proper noun, number, or technical term]

Question 2: [Generated question with at least 2 explicit keywords]  
Answer 2: [Specific proper noun, number, or technical term]

Question 3: [Generated question with at least 2 explicit keywords]
Answer 3: [Specific proper noun, number, or technical term]"""
    
    @staticmethod
    def get_prompt_2_keyword_extraction_replacement(question_previous_level: str, answer_unchanged: str) -> str:
        """Prompt-2: Keyword Extraction & Replacement Descriptions"""
        return f"""**Given the following question and its Short Answer from the previous level:**
【QUESTION_PREVIOUS_LEVEL】
{question_previous_level}

【ANSWER_UNCHANGED】  
{answer_unchanged}

**Task:**
1. From the 【QUESTION_PREVIOUS_LEVEL】, extract all **minimal keywords** (typically nouns or numbers) sufficient to uniquely identify the 【ANSWER_UNCHANGED】.
2. For each extracted keyword, simulate a **search operation**. From the *search results*, identify and extract a **new, more indirect or abstract descriptive phrase** to replace the original keyword.

**Output Format:**
Keywords Extracted:
- Keyword 1: [Extracted Keyword 1]
- Keyword 2: [Extracted Keyword 2]

Replacement Descriptions (from search results):
- [Extracted Keyword 1] → [New, more indirect/abstract description 1]
- [Extracted Keyword 2] → [New, more indirect/abstract description 2]"""
    
    @staticmethod
    def get_prompt_3_new_question_generation_validation(question_previous_level: str, target_keyword: str, keyword_replacements: List[Dict[str, str]]) -> str:
        """Prompt-3: New Question Generation & Validation - 🔥 修正：答案是目标关键词"""
        replacements_text = "\n".join([
            f"- {kr['original']} → {kr['replacement']}"
            for kr in keyword_replacements
        ])
        
        return f"""**Based on the provided keyword replacement descriptions, construct a new, more challenging question:**

**Original Question:** {question_previous_level}
**Target Answer (First Keyword):** {target_keyword}

**Keyword Replacement Descriptions:**
{replacements_text}

**CRITICAL REQUIREMENT:**
The new question must have "{target_keyword}" as its ONLY correct answer. This follows the workflow requirement that extension questions' answers are keywords from the root query.

**Task:**
1. Construct a **New Question** by replacing the original keywords with their respective replacement descriptions.
2. Ensure the new question naturally leads to "{target_keyword}" as the answer.
3. **Validate** the New Question against all criteria.

**Output Format:**
New Question: [Constructed question using replacement descriptions that answers to "{target_keyword}"]

**Validation Results:**
✓ Answer Consistency: Pass/Fail - [Does the question lead to "{target_keyword}" as answer?]
✓ Keyword Uniqueness: Pass/Fail - [Are the replacement descriptions unique enough?]  
✓ Inference Depth (≤2 hops): Pass/Fail - [Reasoning]
✓ No Cyclic/Shallow Exposure: Pass/Fail - [Reasoning]

**Overall Validation Conclusion:** Pass/Fail"""

class ExpansionType(Enum):
    """扩展类型"""
    SERIES = "series"      # 系列深化：对同一关键词继续深化
    PARALLEL = "parallel"  # 并行扩展：对多个关键词同时扩展

@dataclass
class ShortAnswer:
    """短答案数据结构"""
    answer_text: str
    answer_type: str  # noun, number, name, date, location
    confidence: float
    extraction_source: str  # 从文档中的哪里提取的

@dataclass
class KeywordReplacement:
    """关键词替换记录"""
    original_keyword: str
    replacement_description: str
    search_query: str
    search_results: List[str]
    uniqueness_verified: bool
    confidence: float

@dataclass
class LinguisticQuestion:
    """语言学问题结构"""
    question_text: str
    answer: str
    level: int
    keywords: List[str]
    keyword_replacements: List[KeywordReplacement]
    validation_passed: bool
    max_hops_required: int
    parent_question_id: Optional[str] = None
    question_id: str = ""

@dataclass
class HopTrajectory:
    """每一步hop的轨迹记录"""
    level: int
    original_question: str
    original_answer: str
    keyword_replacements: List[KeywordReplacement]
    new_question: str
    validation_passed: bool
    verification_details: Dict[str, Any]
    hop_success: bool
    processing_time: float

class LinguisticDeepQueryFramework:
    """语言学深度查询框架"""
    
    def __init__(self, api_client=None, search_client=None):
        self.api_client = api_client
        self.search_client = search_client
        self.max_levels = 5
        self.max_hops_allowed = 2
        self.trajectory_history: List[HopTrajectory] = []
        
        # 统计信息
        self.stats = {
            'documents_processed': 0,
            'short_answers_extracted': 0,
            'questions_generated': 0,
            'successful_hops': 0,
            'failed_hops': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'series_extensions': 0,
            'parallel_extensions': 0
        }
    
    def set_api_client(self, api_client):
        """设置API客户端"""
        self.api_client = api_client
    
    def set_search_client(self, search_client):
        """设置搜索客户端"""
        self.search_client = search_client
    
    def process_document_with_linguistic_depth(self, document_content: str, document_id: str) -> Dict[str, Any]:
        """
        使用语言学深度框架处理文档
        
        Args:
            document_content: 原始文档内容
            document_id: 文档ID
            
        Returns:
            完整的处理结果，包含所有层级的问题
        """
        logger.info(f"开始语言学深度处理文档: {document_id}")
        start_time = time.time()
        
        try:
            # 层级0️⃣：原始文档（已提供）
            
            # 层级1️⃣：初始问题与Short Answer抽取
            short_answers = self._extract_short_answers(document_content)
            if not short_answers:
                logger.warning(f"未能从文档 {document_id} 中提取到Short Answer")
                return self._create_empty_result(document_id, "No short answers extracted")
            
            initial_questions = self._generate_initial_questions(short_answers, document_content)
            if not initial_questions:
                logger.warning(f"未能为文档 {document_id} 生成初始问题")
                return self._create_empty_result(document_id, "No initial questions generated")
            
            # 层级2️⃣及之后：系列深化与并行扩展
            all_questions = {}
            all_trajectories = []
            
            # 为每个初始问题构建深化链
            for i, initial_q in enumerate(initial_questions):
                question_chain, trajectories = self._build_question_chain(initial_q, document_content, max_depth=self.max_levels-1)
                all_questions[f"chain_{i}"] = question_chain
                all_trajectories.extend(trajectories)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 🔥 新增：生成Tree Level Query整合问题
            tree_level_query = None
            if all_questions and self.api_client:  # 如果有问题链并且有API客户端，尝试生成整合问题
                # 准备问题树数据用于整合
                tree_data = self._prepare_tree_data_for_integration(all_questions, short_answers, document_id)
                
                # 使用TreeLevelQueryIntegrator生成整合问题
                from tree_level_query_integrator import TreeLevelQueryIntegrator
                tree_integrator = TreeLevelQueryIntegrator(api_client=self.api_client)
                
                tree_level_query = tree_integrator.generate_tree_level_query(
                    tree_data, integration_strategy='keyword_replacement'  # 适合语言学模式
                )
                
                if tree_level_query:
                    logger.info(f"🎯 语言学模式生成Tree Level Query: {tree_level_query.integrated_question[:60]}...")
                else:
                    logger.warning("语言学模式Tree Level Query生成失败")

            # 构建结果
            result = {
                'success': True,
                'document_id': document_id,
                'processing_time': processing_time,
                'short_answers': [self._serialize_short_answer(sa) for sa in short_answers],
                'initial_questions': [self._serialize_question(q) for q in initial_questions],
                'question_chains': all_questions,
                'trajectories': [self._serialize_trajectory(t) for t in all_trajectories],
                'tree_level_query': self._serialize_tree_level_query(tree_level_query) if tree_level_query else None,  # 🔥 新增
                'statistics': {
                    'total_questions': sum(len(chain) for chain in all_questions.values()),
                    'total_levels': max(len(chain) for chain in all_questions.values()) if all_questions else 0,
                    'successful_hops': len([t for t in all_trajectories if t.hop_success]),
                    'validation_pass_rate': len([t for t in all_trajectories if t.validation_passed]) / max(len(all_trajectories), 1),
                    'tree_level_query_generated': tree_level_query is not None  # 🔥 新增统计
                },
                'framework_version': '1.0_linguistic'
            }
            
            self.stats['documents_processed'] += 1
            logger.info(f"语言学深度处理完成: {document_id}, 耗时: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"语言学深度处理失败 {document_id}: {e}")
            return self._create_empty_result(document_id, str(e))
    
    def _extract_short_answers(self, document_content: str) -> List[ShortAnswer]:
        """
        层级1️⃣：从文档中提取Short Answer
        实现Prompt-1的逻辑 - 使用IntegratedPromptTemplates
        """
        if not self.api_client:
            logger.error("需要API客户端来提取Short Answer")
            return []
        
        try:
            # 🔥 使用IntegratedPromptTemplates的Prompt-1
            prompt = IntegratedPromptTemplates.get_prompt_1_short_answer_extraction(document_content)

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # 解析响应
            parsed_data = self._parse_json_response(response)
            if not parsed_data or 'short_answers' not in parsed_data:
                logger.warning("无法解析Short Answer响应")
                return []
            
            short_answers = []
            for sa_data in parsed_data['short_answers'][:3]:  # 限制最多3个
                short_answer = ShortAnswer(
                    answer_text=sa_data.get('answer', ''),
                    answer_type=sa_data.get('answer_type', 'unknown'),
                    confidence=sa_data.get('confidence', 0.5),
                    extraction_source=document_content[:200]
                )
                short_answers.append(short_answer)
            
            self.stats['short_answers_extracted'] += len(short_answers)
            logger.info(f"提取到 {len(short_answers)} 个Short Answer")
            
            return short_answers
            
        except Exception as e:
            logger.error(f"提取Short Answer失败: {e}")
            return []
    
    def _generate_initial_questions(self, short_answers: List[ShortAnswer], document_content: str) -> List[LinguisticQuestion]:
        """生成初始问题（层级1️⃣）"""
        if not self.api_client:
            return []
        
        try:
            questions = []
            
            for i, sa in enumerate(short_answers):
                # Prompt说明: 基于Short Answer生成明确问题，包含循环预防逻辑
                base_prompt = f"""Based on the following Short Answer, generate a clear and specific question:

Short Answer: {sa.answer_text}
Answer Type: {sa.answer_type}
Document Context: {document_content[:1000]}

Requirements:
1. The question must contain at least two explicit keywords
2. The question must uniquely determine the answer
3. The question should be objective and verifiable
4. Avoid subjective or "how" type questions

🔄 CIRCULAR PREVENTION REQUIREMENTS:
- AVOID time-based questions if answer contains dates/years
- AVOID entity property questions if answer is an entity name
- AVOID direct "who/what/when" questions that simply reverse the statement
- USE indirect, contextual descriptions instead of direct terms

GOOD EXAMPLES:
- Instead of "When was X launched?" → "What milestone occurred in the year of technological breakthrough?"
- Instead of "Which company developed Y?" → "What organization pioneered the revolutionary Z technology?"
- Instead of "Who invented A?" → "Which innovator contributed to the field of B?"

OUTPUT REQUIREMENTS:
- Question must be indirect and require reasoning
- Question must avoid obvious circular patterns
- Question must use descriptive/contextual language

输出格式（JSON）：
{{
    "question": "生成的问题",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "confidence": 0.0-1.0
}}"""

                response = self.api_client.generate_response(
                    prompt=base_prompt,
                    temperature=0.4,
                    max_tokens=300
                )
                
                parsed = self._parse_json_response(response)
                if parsed and 'question' in parsed:
                    question = LinguisticQuestion(
                        question_text=parsed['question'],
                        answer=sa.answer_text,
                        level=1,
                        keywords=parsed.get('keywords', []),
                        keyword_replacements=[],
                        validation_passed=True,  # 初始问题默认通过
                        max_hops_required=1,
                        question_id=f"q1_{i}"
                    )
                    questions.append(question)
            
            self.stats['questions_generated'] += len(questions)
            logger.info(f"生成 {len(questions)} 个初始问题")
            
            return questions
            
        except Exception as e:
            logger.error(f"生成初始问题失败: {e}")
            return []
    
    def _build_question_chain(self, initial_question: LinguisticQuestion, document_content: str, max_depth: int) -> Tuple[List[LinguisticQuestion], List[HopTrajectory]]:
        """
        构建问题链：从初始问题开始，逐层深化
        实现层级2️⃣及之后的逻辑，支持Series和Parallel扩展
        """
        question_chain = [initial_question]
        trajectories = []
        current_questions = [initial_question]  # 支持并行扩展的多个问题
        
        for depth in range(2, max_depth + 1):
            logger.info(f"构建深度 {depth} 的问题")
            
            # 🔥 决定扩展类型：Series vs Parallel
            extension_type = self._choose_extension_type(depth, len(current_questions))
            
            if extension_type == ExpansionType.SERIES:
                # Series扩展：对当前最后一个问题进行深化
                logger.info(f"执行Series扩展 (深度 {depth})")
                new_question, trajectory = self._perform_linguistic_hop(current_questions[-1], depth, document_content)
                
                trajectories.append(trajectory)
                
                if trajectory.hop_success and new_question:
                    question_chain.append(new_question)
                    current_questions = [new_question]  # Series: 只保留最新问题
                    self.stats['successful_hops'] += 1
                    self.stats['series_extensions'] += 1
                else:
                    logger.info(f"Series扩展失败，停止构建链")
                    self.stats['failed_hops'] += 1
                    break
            
            elif extension_type == ExpansionType.PARALLEL:
                # Parallel扩展：为每个当前问题生成并行问题
                logger.info(f"执行Parallel扩展 (深度 {depth})")
                parallel_questions = []
                
                for i, current_q in enumerate(current_questions[:2]):  # 限制最多2个并行
                    new_question, trajectory = self._perform_linguistic_hop(current_q, depth, document_content)
                    trajectories.append(trajectory)
                    
                    if trajectory.hop_success and new_question:
                        # 为并行问题添加标识
                        new_question.question_id = f"{new_question.question_id}_parallel_{i}"
                        parallel_questions.append(new_question)
                        question_chain.append(new_question)
                        self.stats['successful_hops'] += 1
                        self.stats['parallel_extensions'] += 1
                    else:
                        self.stats['failed_hops'] += 1
                
                if parallel_questions:
                    current_questions = parallel_questions  # Parallel: 保留所有并行问题
                else:
                    logger.info(f"Parallel扩展失败，停止构建链")
                    break
        
        return question_chain, trajectories
    
    def _choose_extension_type(self, depth: int, current_questions_count: int) -> ExpansionType:
        """
        选择扩展类型：Series vs Parallel
        
        Args:
            depth: 当前深度
            current_questions_count: 当前问题数量
            
        Returns:
            选择的扩展类型
        """
        # 🔥 扩展类型选择策略
        
        # 1. 如果已有多个并行问题，优先Series深化
        if current_questions_count > 1:
            logger.info(f"已有 {current_questions_count} 个并行问题，选择Series深化")
            return ExpansionType.SERIES
        
        # 2. 奇数深度倾向于Parallel，偶数深度倾向于Series
        if depth % 2 == 1:  # 奇数深度：尝试Parallel扩展
            logger.info(f"深度 {depth} (奇数)，选择Parallel扩展")
            return ExpansionType.PARALLEL
        else:  # 偶数深度：Series深化
            logger.info(f"深度 {depth} (偶数)，选择Series扩展")
            return ExpansionType.SERIES
    
    def _perform_linguistic_hop(self, current_question: LinguisticQuestion, target_level: int, document_content: str) -> Tuple[Optional[LinguisticQuestion], HopTrajectory]:
        """
        执行一次语言学hop：关键词提取、搜索替换、新问题生成
        实现Prompt-2和Prompt-3的逻辑
        """
        start_time = time.time()
        hop_trajectory = HopTrajectory(
            level=target_level,
            original_question=current_question.question_text,
            original_answer=current_question.answer,
            keyword_replacements=[],
            new_question="",
            validation_passed=False,
            verification_details={},
            hop_success=False,
            processing_time=0.0
        )
        
        try:
            # 步骤1：提取关键词
            keywords = self._extract_keywords_from_question(current_question.question_text)
            if not keywords:
                hop_trajectory.verification_details['error'] = "No keywords extracted"
                hop_trajectory.processing_time = time.time() - start_time
                return None, hop_trajectory
            
            # 步骤2：为每个关键词生成替换描述
            keyword_replacements = []
            for keyword in keywords[:3]:  # 限制最多3个关键词
                replacement = self._generate_keyword_replacement(keyword, current_question.answer)
                if replacement:
                    keyword_replacements.append(replacement)
            
            if not keyword_replacements:
                hop_trajectory.verification_details['error'] = "No keyword replacements generated"
                hop_trajectory.processing_time = time.time() - start_time
                return None, hop_trajectory
            
            hop_trajectory.keyword_replacements = keyword_replacements
            
            # 步骤3：生成新问题
            new_question_text = self._generate_new_question_with_replacements(
                current_question.question_text, 
                keyword_replacements
            )
            
            if not new_question_text:
                hop_trajectory.verification_details['error'] = "Failed to generate new question"
                hop_trajectory.processing_time = time.time() - start_time
                return None, hop_trajectory
            
            # 步骤4：验证新问题
            # 🔥 关键修正：验证时使用目标关键词作为答案
            target_keyword = keyword_replacements[0].original_keyword if keyword_replacements else current_question.answer
            validation_result = self._validate_new_question(
                original_question=current_question.question_text,
                new_question=new_question_text,
                answer=target_keyword,  # 🔥 使用目标关键词
                keyword_replacements=keyword_replacements
            )
            
            hop_trajectory.new_question = new_question_text
            hop_trajectory.validation_passed = validation_result['passed']
            hop_trajectory.verification_details = validation_result
            
            if validation_result['passed']:
                # 🔥 关键修正：新问题的答案是被替换的关键词，而不是原始答案
                # 选择第一个验证通过的关键词作为新问题的答案
                target_keyword = keyword_replacements[0].original_keyword if keyword_replacements else current_question.answer
                
                # 创建新问题对象
                new_question = LinguisticQuestion(
                    question_text=new_question_text,
                    answer=target_keyword,  # 🔥 答案变成关键词！
                    level=target_level,
                    keywords=[kr.original_keyword for kr in keyword_replacements],
                    keyword_replacements=keyword_replacements,
                    validation_passed=True,
                    max_hops_required=min(current_question.max_hops_required + 1, self.max_hops_allowed),
                    parent_question_id=current_question.question_id,
                    question_id=f"q{target_level}_{int(time.time() % 10000)}"
                )
                
                hop_trajectory.hop_success = True
                self.stats['validation_passed'] += 1
                
                hop_trajectory.processing_time = time.time() - start_time
                return new_question, hop_trajectory
            else:
                self.stats['validation_failed'] += 1
                hop_trajectory.processing_time = time.time() - start_time
                return None, hop_trajectory
                
        except Exception as e:
            logger.error(f"执行linguistic hop失败: {e}")
            hop_trajectory.verification_details['error'] = str(e)
            hop_trajectory.processing_time = time.time() - start_time
            return None, hop_trajectory
    
    def _extract_keywords_from_question(self, question: str) -> List[str]:
        """
        从问题中提取关键词
        实现Prompt-2的步骤1
        """
        if not self.api_client:
            return []
        
        try:
            # 🔥 使用IntegratedPromptTemplates的关键词提取逻辑
            prompt = f"""From the following question, extract all **minimal keywords** (typically nouns or numbers) that are meaningful for replacement:

Question: {question}

Requirements:
1. Extract specific, meaningful keywords
2. Focus on **proper nouns**, **numbers**, **technical terms**, **dates**
3. Each keyword must be **independently meaningful**
4. Avoid generic terms like "system", "method", "approach"
5. Prefer single-word or short-phrase keywords (1-3 words)

Output Format (JSON):
{{
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.2,
                max_tokens=200
            )
            
            parsed = self._parse_json_response(response)
            if parsed and 'keywords' in parsed:
                return parsed['keywords'][:5]  # 限制最多5个关键词
            
            return []
            
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return []
    
    def _generate_keyword_replacement(self, keyword: str, original_answer: str) -> Optional[KeywordReplacement]:
        """
        为关键词生成替换描述
        实现Prompt-2的步骤2
        """
        if not self.api_client or not self.search_client:
            return None
        
        try:
            # 执行搜索
            search_query = f"{keyword} definition characteristics"
            search_results = self.search_client(search_query)
            
            if not search_results or 'results' not in search_results:
                return None
            
            # 从搜索结果中生成替换描述
            search_content = " ".join([result.get('content', '')[:200] for result in search_results['results'][:3]])
            
            # Prompt说明: 基于搜索结果为关键词生成抽象替换描述
            prompt = f"""Based on search results, generate a more abstract or indirect replacement description for the keyword:

Keyword: {keyword}
Original Answer: {original_answer}
Search Results: {search_content}

Requirements:
1. The replacement description must uniquely identify the original keyword
2. The description should be more abstract or indirect while maintaining accuracy
3. Avoid directly using the original keyword
4. Ensure the replaced question can still determine the original answer

Output Format (JSON):
{{
    "replacement_description": "Abstract replacement description",
    "uniqueness_confidence": 0.0-1.0,
    "reasoning": "Why this description uniquely identifies the original keyword"
}}"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.4,
                max_tokens=300
            )
            
            parsed = self._parse_json_response(response)
            if parsed and 'replacement_description' in parsed:
                return KeywordReplacement(
                    original_keyword=keyword,
                    replacement_description=parsed['replacement_description'],
                    search_query=search_query,
                    search_results=[r.get('content', '')[:100] for r in search_results['results'][:3]],
                    uniqueness_verified=parsed.get('uniqueness_confidence', 0.0) >= 0.7,
                    confidence=parsed.get('uniqueness_confidence', 0.5)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"生成关键词替换失败 {keyword}: {e}")
            return None
    
    def _generate_new_question_with_replacements(self, original_question: str, keyword_replacements: List[KeywordReplacement]) -> Optional[str]:
        """
        基于关键词替换生成新问题
        实现Prompt-3的逻辑
        """
        if not self.api_client:
            return None
        
        try:
            # 🔥 关键修正：获取目标关键词（第一个关键词作为新问题的答案）
            target_keyword = keyword_replacements[0].original_keyword if keyword_replacements else "unknown"
            
            # 转换为Prompt-3需要的格式
            replacements_dict = [
                {'original': kr.original_keyword, 'replacement': kr.replacement_description}
                for kr in keyword_replacements
            ]
            
            # 🔥 使用修正后的IntegratedPromptTemplates的Prompt-3
            prompt = IntegratedPromptTemplates.get_prompt_3_new_question_generation_validation(
                original_question, target_keyword, replacements_dict
            )
            
            # 简化为问题生成部分
            prompt += f"""

**FOR THIS STEP - ONLY GENERATE THE NEW QUESTION:**
Output Format (JSON):
{{
    "new_question": "Constructed question that has '{target_keyword}' as the answer",
    "confidence": 0.0-1.0,
    "target_answer_confirmed": "{target_keyword}",
    "reasoning": "How the question was constructed to answer '{target_keyword}'"
}}"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=400
            )
            
            parsed = self._parse_json_response(response)
            if parsed and 'new_question' in parsed:
                return parsed['new_question']
            
            return None
            
        except Exception as e:
            logger.error(f"生成新问题失败: {e}")
            return None
    
    def _validate_new_question(self, original_question: str, new_question: str, answer: str, keyword_replacements: List[KeywordReplacement]) -> Dict[str, Any]:
        """
        验证新问题
        实现Prompt-3的验证逻辑
        """
        if not self.api_client:
            return {'passed': False, 'reason': 'No API client'}
        
        try:
            # 🔥 使用IntegratedPromptTemplates的验证逻辑
            prompt = f"""**Validate the following new question against all criteria:**

**Original Question:** {original_question}
**New Question:** {new_question}
**Answer:** {answer}

**CRITICAL VALIDATION CRITERIA:**

**1. Answer Consistency Check:**
* Does the new question still uniquely lead to the original answer ({answer})?
* Can someone answering this question arrive at exactly "{answer}" and nothing else?

**2. Keyword Uniqueness Check:**
* Do the replacement descriptions uniquely determine their original keywords through indirect inference?
* Can each replacement description be traced back to exactly one original keyword?

**3. Inference Depth Check (Max Hops ≤ 2):**
* Can the answer be determined within a maximum of two search/reasoning steps from the New Question?
* Is the question challenging but not impossibly indirect?

**4. No Cyclic/Shallow Exposure Check:**
* Does the New Question avoid cyclic descriptions or exposing shallow, original information?
* Is it genuinely deeper/more abstract than the original question?
* Does it avoid patterns like "A occurred in Year B" leading to "What year did A occur?"

**5. Shortcut Check:**
* Does the new question avoid containing keywords that could directly pinpoint other answers?

**Output Format (JSON):**
{{
    "answer_consistency": true/false,
    "keyword_uniqueness": true/false,
    "inference_depth": true/false,
    "no_cyclic_exposure": true/false,
    "shortcut_check": true/false,
    "overall_passed": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Detailed validation analysis"
}}"""

            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500
            )
            
            parsed = self._parse_json_response(response)
            if parsed:
                return {
                    'passed': parsed.get('overall_passed', False),
                    'answer_consistency': parsed.get('answer_consistency', False),
                    'keyword_uniqueness': parsed.get('keyword_uniqueness', False),
                    'inference_depth': parsed.get('inference_depth', False),
                    'no_cyclic_exposure': parsed.get('no_cyclic_exposure', False),
                    'shortcut_check': parsed.get('shortcut_check', False),
                    'confidence': parsed.get('confidence', 0.0),
                    'reasoning': parsed.get('reasoning', '')
                }
            
            return {'passed': False, 'reason': 'Failed to parse validation response'}
            
        except Exception as e:
            logger.error(f"验证新问题失败: {e}")
            return {'passed': False, 'reason': str(e)}
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            # 查找JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                return json.loads(json_text)
            
            return None
            
        except Exception as e:
            logger.warning(f"解析JSON响应失败: {e}")
            return None
    
    def _serialize_short_answer(self, sa: ShortAnswer) -> Dict[str, Any]:
        """序列化ShortAnswer"""
        return {
            'answer_text': sa.answer_text,
            'answer_type': sa.answer_type,
            'confidence': sa.confidence,
            'extraction_source': sa.extraction_source[:100]
        }
    
    def _serialize_question(self, q: LinguisticQuestion) -> Dict[str, Any]:
        """序列化LinguisticQuestion"""
        return {
            'question_id': q.question_id,
            'question_text': q.question_text,
            'answer': q.answer,
            'level': q.level,
            'keywords': q.keywords,
            'keyword_replacements': [self._serialize_replacement(kr) for kr in q.keyword_replacements],
            'validation_passed': q.validation_passed,
            'max_hops_required': q.max_hops_required,
            'parent_question_id': q.parent_question_id
        }
    
    def _serialize_replacement(self, kr: KeywordReplacement) -> Dict[str, Any]:
        """序列化KeywordReplacement"""
        return {
            'original_keyword': kr.original_keyword,
            'replacement_description': kr.replacement_description,
            'search_query': kr.search_query,
            'uniqueness_verified': kr.uniqueness_verified,
            'confidence': kr.confidence
        }
    
    def _serialize_trajectory(self, trajectory: HopTrajectory) -> Dict[str, Any]:
        """序列化HopTrajectory"""
        return {
            'level': trajectory.level,
            'original_question': trajectory.original_question,
            'original_answer': trajectory.original_answer,
            'keyword_replacements': [
                {
                    'original_keyword': kr.original_keyword,
                    'replacement_description': kr.replacement_description,
                    'search_query': kr.search_query,
                    'confidence': kr.confidence
                } for kr in trajectory.keyword_replacements
            ],
            'new_question': trajectory.new_question,
            'validation_passed': trajectory.validation_passed,
            'verification_details': trajectory.verification_details,
            'hop_success': trajectory.hop_success,
            'processing_time': trajectory.processing_time
        }
    
    def _prepare_tree_data_for_integration(self, all_questions: Dict[str, List[LinguisticQuestion]], 
                                         short_answers: List[ShortAnswer], document_id: str) -> Dict[str, Any]:
        """为Tree Level Query整合准备数据"""
        # 获取第一个链的根问题作为主要根问题
        first_chain = list(all_questions.values())[0] if all_questions else []
        if not first_chain:
            return {}
        
        root_question = first_chain[0]
        
        # 构建tree_data格式
        tree_data = {
            'root_question': {
                'question': root_question.question_text,
                'answer': short_answers[0].answer_text if short_answers else root_question.answer,  # 使用原始短答案
                'keywords': root_question.keywords
            },
            'nodes': {}
        }
        
        # 添加所有扩展节点
        node_id_counter = 0
        for chain_id, question_chain in all_questions.items():
            for level, question in enumerate(question_chain[1:], 1):  # 跳过根问题
                node_id = f"linguistic_{chain_id}_{level}_{node_id_counter}"
                tree_data['nodes'][node_id] = {
                    'question': question.question_text,
                    'answer': question.answer,  # 语言学模式：答案是关键词
                    'depth_level': level,
                    'parent_node_id': 'root' if level == 1 else f"linguistic_{chain_id}_{level-1}_{node_id_counter-1}",
                    'keywords': question.keywords,
                    'extension_type': 'keyword_replacement'
                }
                node_id_counter += 1
        
        return tree_data
    
    def _serialize_tree_level_query(self, tree_level_query) -> Dict[str, Any]:
        """序列化TreeLevelQuery"""
        if not tree_level_query:
            return None
        
        return {
            'integrated_question': tree_level_query.integrated_question,
            'root_answer': tree_level_query.root_answer,
            'integration_depth': tree_level_query.integration_depth,
            'component_questions': tree_level_query.component_questions,
            'reasoning_path': tree_level_query.reasoning_path,
            'confidence': tree_level_query.confidence,
            'complexity_score': tree_level_query.complexity_score,
            'metadata': tree_level_query.metadata
        }

    def _create_empty_result(self, document_id: str, reason: str) -> Dict[str, Any]:
        """创建空结果"""
        return {
            'success': False,
            'document_id': document_id,
            'error': reason,
            'short_answers': [],
            'initial_questions': [],
            'question_chains': {},
            'trajectories': [],
            'statistics': {},
            'framework_version': '1.0_linguistic'
        }
    
    def get_framework_statistics(self) -> Dict[str, Any]:
        """获取框架统计信息"""
        return {
            'framework_stats': self.stats.copy(),
            'trajectory_count': len(self.trajectory_history),
            'processing_summary': {
                'documents_processed': self.stats['documents_processed'],
                'success_rate': self.stats['successful_hops'] / max(self.stats['successful_hops'] + self.stats['failed_hops'], 1),
                'avg_questions_per_doc': self.stats['questions_generated'] / max(self.stats['documents_processed'], 1)
            }
        }
    
    def process_single_short_answer_with_linguistic_depth(self, document_content: str, document_id: str, 
                                                        short_answer_text: str, short_answer_type: str) -> Dict[str, Any]:
        """
        处理单个短答案的语言学深度查询（与经典模式保持一致的处理方式）
        
        Args:
            document_content: 原始文档内容
            document_id: 文档ID  
            short_answer_text: 短答案文本
            short_answer_type: 短答案类型
            
        Returns:
            完整的处理结果，针对单个短答案的语言学深化
        """
        logger.info(f"开始语言学深度处理单个短答案: {document_id} - {short_answer_text}")
        start_time = time.time()
        
        try:
            # 构建ShortAnswer对象
            short_answer = ShortAnswer(
                answer_text=short_answer_text,
                answer_type=short_answer_type,
                confidence=1.0,
                extraction_source=document_content[:100]
            )
            
            # 层级1️⃣：为这个短答案生成初始问题
            initial_question = self._generate_single_initial_question(short_answer, document_content)
            if not initial_question:
                logger.warning(f"未能为短答案 {short_answer_text} 生成初始问题")
                return self._create_empty_result(document_id, "No initial question generated for short answer")
            
            # 层级2️⃣及之后：为这个问题构建深化链
            question_chain, trajectories = self._build_question_chain(initial_question, document_content, max_depth=self.max_levels-1)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 构建结果
            result = {
                'success': True,
                'document_id': document_id,
                'processing_time': processing_time,
                'short_answer': self._serialize_short_answer(short_answer),
                'initial_question': self._serialize_question(initial_question),
                'question_chains': {'main_chain': question_chain},  # 单个链
                'trajectories': [self._serialize_trajectory(t) for t in trajectories],
                'statistics': {
                    'total_questions': len(question_chain),
                    'total_levels': len(question_chain),
                    'successful_hops': len([t for t in trajectories if t.hop_success]),
                    'validation_pass_rate': len([t for t in trajectories if t.validation_passed]) / max(len(trajectories), 1)
                },
                'framework_version': '1.0_linguistic_single_sa'
            }
            
            self.stats['documents_processed'] += 1
            logger.info(f"语言学深度处理单个短答案完成: {document_id}, 耗时: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"语言学深度处理单个短答案失败 {document_id}: {e}")
            return self._create_empty_result(document_id, str(e))
    
    def _generate_single_initial_question(self, short_answer: ShortAnswer, document_content: str) -> Optional[LinguisticQuestion]:
        """为单个短答案生成初始问题"""
        if not self.api_client:
            return None
        
        try:
            # Prompt说明: 为单个短答案生成明确问题，包含循环预防逻辑
            base_prompt = f"""Based on the following Short Answer, generate a clear and specific question:

Short Answer: {short_answer.answer_text}
Answer Type: {short_answer.answer_type}
Document Context: {document_content[:1000]}

Requirements:
1. The question must contain at least two explicit keywords
2. The question must uniquely determine the answer
3. The question should be objective and verifiable
4. Avoid subjective or "how" type questions

🔄 CIRCULAR PREVENTION REQUIREMENTS:
- AVOID time-based questions if answer contains dates/years
- AVOID entity property questions if answer is an entity name
- AVOID direct "who/what/when" questions that simply reverse the statement
- USE indirect, contextual descriptions instead of direct terms

OUTPUT REQUIREMENTS:
- Question must be indirect and require reasoning
- Question must avoid obvious circular patterns
- Question must use descriptive/contextual language

输出格式（JSON）：
{{
    "question": "Generated question",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "confidence": 0.0-1.0
}}"""

            response = self.api_client.generate_response(
                prompt=base_prompt,
                temperature=0.3,
                max_tokens=400
            )
            
            parsed = self._parse_json_response(response)
            if parsed and 'question' in parsed:
                return LinguisticQuestion(
                    question_id=f"q_1",
                    question_text=parsed['question'],
                    answer=short_answer.answer_text,
                    level=1,
                    keywords=parsed.get('keywords', []),
                    keyword_replacements=[],
                    validation_passed=True,
                    max_hops_required=0,
                    parent_question_id=""
                )
            
            return None
            
        except Exception as e:
            logger.error(f"生成单个初始问题失败: {e}")
            return None 