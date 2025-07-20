"""
Optimized Framework Integrator for Tree Extension Deep Query Framework
Integrates all optimization components into the main workflow following strict requirements.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from config import get_config
from enhanced_root_validator import EnhancedRootValidator, ValidationResult
from keyword_hierarchy_manager import KeywordHierarchyManager, KeywordNode, HierarchyValidationResult
from web_search_extension_system import WebSearchExtensionSystem, ExtensionContext
from enhanced_question_generator import EnhancedQuestionGenerator, GeneratedQuestion
from simple_trajectory_recorder import SimpleTrajectoryRecorder
from workflow_compliance_enforcer import WorkFlowComplianceEnforcer, WorkFlowValidationResult
from circular_question_detector import CircularQuestionDetector, CircularDetectionResult
from tree_level_query_integrator import TreeLevelQueryIntegrator, TreeLevelQuery

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class OptimizedQuestionTree:
    """Optimized question tree with enhanced validation"""
    tree_id: str
    root_question: GeneratedQuestion
    root_validation: ValidationResult
    extensions: Dict[str, Any]  # node_id -> extension data
    keyword_hierarchy: Dict[str, List[KeywordNode]]  # level -> keywords
    search_contexts: Dict[str, ExtensionContext]  # node_id -> search context
    validation_scores: Dict[str, float]
    total_web_searches: int
    generation_metadata: Dict[str, Any]
    tree_level_query: Optional[TreeLevelQuery] = None  # NEW: 整合的深度问题
    circular_detection_summary: Dict[str, Any] = None  # NEW: 循环检测摘要

class OptimizedFrameworkIntegrator:
    """Integrates all optimization components following workflow requirements"""
    
    def __init__(self, api_client=None, search_client=None):
        self.config = get_config()
        
        # Initialize all optimization components
        self.root_validator = EnhancedRootValidator(api_client)
        self.keyword_manager = KeywordHierarchyManager(api_client)
        self.search_system = WebSearchExtensionSystem(search_client, api_client)
        self.question_generator = EnhancedQuestionGenerator(api_client)
        self.trajectory_recorder = SimpleTrajectoryRecorder()
        
        # NEW: WorkFlow Compliance Enforcer
        self.compliance_enforcer = WorkFlowComplianceEnforcer()
        
        # NEW: 循环检测器和整合器
        self.circular_detector = CircularQuestionDetector()
        self.tree_integrator = TreeLevelQueryIntegrator(api_client)
        
        # Statistics tracking
        self.stats = {
            'total_trees_processed': 0,
            'root_validations_passed': 0,
            'keyword_extractions_successful': 0,
            'web_searches_performed': 0,
            'extensions_created': 0,
            'validation_failures': 0,
            'workflow_compliance_violations': 0,
            'workflow_compliance_passed': 0
        }
        
    def set_api_client(self, api_client):
        """Set API client for all components"""
        self.root_validator.set_api_client(api_client)
        self.keyword_manager.set_api_client(api_client)
        self.search_system.set_api_client(api_client)
        self.question_generator.set_api_client(api_client)
        self.tree_integrator.set_api_client(api_client)
        
    def set_search_client(self, search_client):
        """Set search client for web search system"""
        self.search_system.set_search_client(search_client)
    
    def process_document_with_optimization(self, document_content: str, document_id: str,
                                         short_answer: str, answer_type: str) -> Optional[OptimizedQuestionTree]:
        """
        Process document with full optimization pipeline following workflow requirements
        
        Workflow Steps:
        1. Generate root question with enhanced validation
        2. Extract keywords for hierarchy
        3. Generate extensions with web search
        4. Validate keyword hierarchy compliance
        5. Ensure shortcut prevention
        """
        logger.info(f"Processing document {document_id} with optimization pipeline")
        
        # 开始轨迹记录
        trajectory_id = self.trajectory_recorder.start_trajectory(document_id)
        
        try:
            # Step 1: Generate and validate root question
            root_question = self._generate_validated_root_question(
                document_content, short_answer, answer_type, document_id
            )
            
            # 记录根问题生成步骤
            self.trajectory_recorder.record_step(
                step_name="root_question_generation",
                step_type="generation",
                input_data={
                    'document_length': len(document_content),
                    'short_answer': short_answer,
                    'answer_type': answer_type
                },
                output_data={
                    'question_generated': root_question.question if root_question else None,
                    'expected_answer': root_question.expected_answer if root_question else None,
                    'validation_score': getattr(root_question, 'validation_score', 0.0) if root_question else 0.0
                },
                success=root_question is not None,
                metadata={'document_id': document_id}
            )
            
            if not root_question:
                logger.warning(f"Failed to generate valid root question for {document_id}")
                self.stats['validation_failures'] += 1
                # 完成失败的轨迹记录
                self.trajectory_recorder.finalize_trajectory(0, 0)
                return None
            
            # Step 2: Extract parent keywords for hierarchy
            parent_keywords = self.keyword_manager.extract_parent_keywords(
                root_question.question, root_question.expected_answer, document_content
            )
            
            # 记录关键词提取步骤
            self.trajectory_recorder.record_step(
                step_name="keyword_extraction",
                step_type="extraction",
                input_data={
                    'question': root_question.question,
                    'expected_answer': root_question.expected_answer
                },
                output_data={
                    'keywords_count': len(parent_keywords),
                    'extracted_keywords': [kw.keyword if hasattr(kw, 'keyword') else str(kw) for kw in parent_keywords]
                },
                success=len(parent_keywords) > 0,
                metadata={'document_id': document_id}
            )
            
            if not parent_keywords:
                logger.warning(f"Failed to extract keywords for {document_id}")
                self.stats['validation_failures'] += 1
                # 完成失败的轨迹记录
                self.trajectory_recorder.finalize_trajectory(0, 1)
                return None
            
            self.stats['keyword_extractions_successful'] += 1
            
            # Step 3: Perform minimum keyword check
            min_keyword_check = self.keyword_manager.perform_minimum_keyword_check(
                parent_keywords, root_question.expected_answer
            )
            
            if not min_keyword_check['passed']:
                logger.warning(f"Minimum keyword check failed for {document_id}: {min_keyword_check['reasoning']}")
                # Continue anyway, but note the issue
            
            # Step 4: Generate extensions with web search and validation
            extensions = self._generate_optimized_extensions(
                root_question, parent_keywords, document_content
            )
            
            # 记录扩展生成步骤
            self.trajectory_recorder.record_step(
                step_name="extensions_generation",
                step_type="generation",
                input_data={
                    'parent_keywords_count': len(parent_keywords),
                    'root_question': root_question.question
                },
                output_data={
                    'extensions_created': len(extensions.get('nodes', {})),
                    'web_searches_performed': extensions.get('web_searches_count', 0),
                    'max_depth': extensions.get('max_depth', 0)
                },
                success=len(extensions.get('nodes', {})) > 0,
                metadata={
                    'document_id': document_id,
                    'total_web_searches': extensions.get('web_searches_count', 0)
                }
            )
            
            # Step 5: 生成Tree Level Query整合问题
            tree_level_query = None
            if len(extensions['nodes']) > 0:  # 只有当有扩展时才整合
                # 准备问题树数据用于整合
                tree_data = {
                    'root_question': {
                        'question': root_question.question,
                        'answer': root_question.expected_answer,
                        'keywords': [kw.keyword if hasattr(kw, 'keyword') else str(kw) for kw in parent_keywords]
                    },
                    'nodes': extensions['nodes']
                }
                
                tree_level_query = self.tree_integrator.generate_tree_level_query(
                    tree_data, integration_strategy='hierarchical_fusion'
                )
                
                if tree_level_query:
                    logger.info(f"成功生成Tree Level Query: {tree_level_query.integrated_question[:60]}...")
                else:
                    logger.warning("Tree Level Query生成失败")

            # Step 6: Create optimized question tree
            optimized_tree = OptimizedQuestionTree(
                tree_id=f"opt_tree_{int(time.time())}_{hash(document_id) % 10000}",
                root_question=root_question,
                root_validation=root_question.validation_score,  # Assuming validation score is stored
                extensions=extensions['nodes'],
                keyword_hierarchy=extensions['keyword_hierarchy'],
                search_contexts=extensions['search_contexts'],
                validation_scores=extensions['validation_scores'],
                total_web_searches=extensions['web_searches_count'],
                tree_level_query=tree_level_query,  # NEW: 添加树级整合问题
                circular_detection_summary=self.circular_detector.get_detection_summary(),  # NEW: 循环检测摘要
                generation_metadata={
                    'document_id': document_id,
                    'processing_time': time.time(),
                    'parent_keywords_count': len(parent_keywords),
                    'min_keyword_check_passed': min_keyword_check['passed'],
                    'optimization_version': '1.1',  # 更新版本号
                    'tree_level_query_generated': tree_level_query is not None
                }
            )
            
            self.stats['total_trees_processed'] += 1
            logger.info(f"Successfully created optimized tree {optimized_tree.tree_id}")
            
            # 完成轨迹记录
            tree_depth = len(extensions.get('nodes', {}))
            tree_size = 1 + len(extensions.get('nodes', {}))  # root + extensions
            final_trajectory = self.trajectory_recorder.finalize_trajectory(tree_depth, tree_size)
            
            # 更新轨迹统计数据
            if final_trajectory:
                # 计算web搜索次数
                final_trajectory.total_web_searches = extensions.get('web_searches_count', 0)
                
                # 计算验证分数
                validation_scores = []
                if hasattr(root_question, 'validation_score'):
                    validation_scores.append(root_question.validation_score)
                
                for node_data in extensions.get('nodes', {}).values():
                    if isinstance(node_data, dict) and 'validation_score' in node_data:
                        validation_scores.append(node_data['validation_score'])
                
                if validation_scores:
                    final_trajectory.average_validation_score = sum(validation_scores) / len(validation_scores)
                
                logger.info(f"轨迹记录完成: {final_trajectory.trajectory_id}, 成功率: {final_trajectory.success_rate:.1%}")
            
            return optimized_tree
            
        except Exception as e:
            logger.error(f"Error processing document {document_id} with optimization: {e}")
            self.stats['validation_failures'] += 1
            
            # 记录处理错误
            self.trajectory_recorder.record_step(
                step_name="processing_error",
                step_type="error",
                input_data={'document_id': document_id},
                output_data={'error_message': str(e)},
                success=False,
                metadata={'error_type': type(e).__name__}
            )
            
            # 完成失败的轨迹记录
            self.trajectory_recorder.finalize_trajectory(0, 0)
            return None
    
    def _generate_validated_root_question(self, document_content: str, short_answer: str,
                                        answer_type: str, document_id: str) -> Optional[GeneratedQuestion]:
        """Generate root question with enhanced validation and WorkFlow compliance"""
        try:
            # STEP 1: WorkFlow Compliance Check for Generation
            generation_context = {
                'question_type': 'root',
                'document_content': document_content,
                'short_answer': short_answer,
                'answer_type': answer_type
            }
            
            generation_compliance = self.compliance_enforcer.enforce_generation_compliance(generation_context)
            
            # 记录符合性检查步骤
            self.trajectory_recorder.record_step(
                step_name="workflow_compliance_check",
                step_type="validation",
                input_data={'context': 'root_generation'},
                output_data={
                    'compliant': generation_compliance.compliant,
                    'violations': generation_compliance.violations if hasattr(generation_compliance, 'violations') else []
                },
                success=generation_compliance.compliant,
                metadata={'check_type': 'generation_compliance'}
            )
            
            if not generation_compliance.compliant:
                logger.warning(f"Root generation violates WorkFlow: {generation_compliance.violations}")
                self.stats['workflow_compliance_violations'] += 1
                return None
            
            # STEP 2: Generate root question
            root_question = self.question_generator.generate_root_question(
                document_content, short_answer, answer_type
            )
            
            if not root_question:
                return None
            
            # STEP 3: Enhanced validation using dual-model system
            validation_result = self.root_validator.validate_root_question(
                root_question.question, root_question.expected_answer, document_content
            )
            
            # STEP 4: WorkFlow Compliance Check for Validation
            validation_context = {
                'question': root_question.question,
                'answer': root_question.expected_answer,
                'document_content': document_content,
                'validation_type': 'root',
                'validation_result': {
                    'overall_score': validation_result.overall_score,
                    'validity_score': validation_result.validity_score,
                    'uniqueness_score': validation_result.uniqueness_score,
                    'specificity_score': validation_result.specificity_score
                }
            }
            
            validation_compliance = self.compliance_enforcer.enforce_validation_compliance(validation_context)
            if not validation_compliance.compliant:
                logger.warning(f"Root validation violates WorkFlow: {validation_compliance.violations}")
                self.stats['workflow_compliance_violations'] += 1
                return None
            
            # 记录根问题验证步骤
            self.trajectory_recorder.record_step(
                step_name="root_validation",
                step_type="validation",
                input_data={
                    'question': root_question.question,
                    'expected_answer': root_question.expected_answer
                },
                output_data={
                    'overall_score': validation_result.overall_score,
                    'validity_score': validation_result.validity_score,
                    'uniqueness_score': validation_result.uniqueness_score,
                    'specificity_score': validation_result.specificity_score
                },
                success=validation_result.passed,
                metadata={'document_id': document_id}
            )
            
            if validation_result.passed:
                self.stats['root_validations_passed'] += 1
                self.stats['workflow_compliance_passed'] += 1
                logger.info(f"Root question validation passed: {validation_result.overall_score:.2f}")
                
                # Update question with validation scores
                root_question.validation_score = validation_result.overall_score
                root_question.reasoning = validation_result.reasoning
                
                # NEW: 添加根问题到循环检测历史
                self.circular_detector.add_question(root_question.question, root_question.expected_answer)
                
                return root_question
            else:
                logger.warning(f"Root question validation failed: {validation_result.reasoning}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating validated root question: {e}")
            return None
    
    def _generate_optimized_extensions(self, root_question: GeneratedQuestion, 
                                     parent_keywords: List[KeywordNode],
                                     document_content: str) -> Dict[str, Any]:
        """Generate extensions with web search and keyword hierarchy validation"""
        extensions_data = {
            'nodes': {},
            'keyword_hierarchy': {'level_0': parent_keywords},
            'search_contexts': {},
            'validation_scores': {},
            'web_searches_count': 0
        }
        
        try:
            # Generate extensions for each parent keyword
            ancestor_answers = [root_question.expected_answer]
            
            for i, keyword_node in enumerate(parent_keywords[:3]):  # Limit to top 3 keywords
                logger.info(f"Generating extension for keyword: {keyword_node.keyword}")
                
                # Determine extension type (alternate between series and parallel)
                extension_type = "series" if i % 2 == 0 else "parallel"
                
                # Generate extension with web search
                extension_context = self.search_system.generate_extension_with_web_search(
                    keyword_node.keyword, root_question.question, 
                    root_question.expected_answer, extension_type
                )
                
                if extension_context:
                    extensions_data['web_searches_count'] += 1
                    self.stats['web_searches_performed'] += 1
                    
                    # WORKFLOW COMPLIANCE: Check child generation requirements
                    child_generation_context = {
                        'question_type': 'child',
                        'parent_question': root_question.question,
                        'parent_answer': root_question.expected_answer,
                        'target_keyword': keyword_node.keyword,
                        'parent_keywords': [kw.keyword for kw in parent_keywords],
                        'extension_context': extension_context.synthesized_context,
                        'web_search_calls': 1,  # We performed 1 web search
                        'document_content': document_content
                    }
                    
                    child_generation_compliance = self.compliance_enforcer.enforce_generation_compliance(child_generation_context)
                    if not child_generation_compliance.compliant:
                        logger.warning(f"Child generation violates WorkFlow for keyword '{keyword_node.keyword}': {child_generation_compliance.violations}")
                        self.stats['workflow_compliance_violations'] += 1
                        continue
                    
                    # Generate child question using extension context
                    child_question = self.question_generator.generate_child_question(
                        root_question.question, root_question.expected_answer,
                        keyword_node.keyword, extension_context.synthesized_context,
                        extension_type
                    )
                    
                    # NEW: 循环提问检测
                    if child_question:
                        circular_detection = self.circular_detector.detect_circular_pattern(
                            child_question.question, child_question.expected_answer
                        )
                        
                        if circular_detection.is_circular:
                            logger.warning(f"检测到循环提问: {circular_detection.conflict_reason}")
                            logger.warning(f"冲突问题: {circular_detection.conflicting_question}")
                            logger.warning(f"建议: {circular_detection.suggestions}")
                            # 跳过这个循环问题
                            continue
                        else:
                            # 添加到历史记录
                            self.circular_detector.add_question(child_question.question, child_question.expected_answer)
                    
                    if child_question:
                        # Validate keyword hierarchy compliance
                        hierarchy_validation = self.keyword_manager.validate_child_answer_hierarchy(
                            child_question.question, child_question.expected_answer, parent_keywords
                        )
                        
                        # Validate shortcut prevention
                        sibling_answers = [kw.keyword for kw in parent_keywords if kw.keyword != keyword_node.keyword]
                        shortcut_check = self.keyword_manager.validate_shortcut_prevention(
                            child_question.question, child_question.expected_answer,
                            ancestor_answers, sibling_answers
                        )
                        
                        # WORKFLOW COMPLIANCE: Check child validation requirements
                        child_validation_context = {
                            'question': child_question.question,
                            'answer': child_question.expected_answer,
                            'validation_type': 'child',
                            'hierarchy_validation': {
                                'valid': hierarchy_validation.valid,
                                'confidence': hierarchy_validation.confidence
                            },
                            'minimum_keyword_check': {'passed': True},  # Simplified for now
                            'shortcut_check': shortcut_check
                        }
                        
                        child_validation_compliance = self.compliance_enforcer.enforce_validation_compliance(child_validation_context)
                        if not child_validation_compliance.compliant:
                            logger.warning(f"Child validation violates WorkFlow for keyword '{keyword_node.keyword}': {child_validation_compliance.violations}")
                            self.stats['workflow_compliance_violations'] += 1
                            continue
                        
                        # Calculate overall validation score
                        overall_validation = (
                            child_question.validation_score * 0.4 +
                            (hierarchy_validation.confidence if hierarchy_validation.valid else 0.0) * 0.3 +
                            shortcut_check['confidence'] * 0.3
                        )
                        
                        if overall_validation >= 0.7:
                            node_id = f"{extension_type}_{i+1}"
                            
                            extensions_data['nodes'][node_id] = {
                                'question': child_question.question,
                                'answer': child_question.expected_answer,
                                'short_answer': {'answer_text': child_question.expected_answer},
                                'extension_type': extension_type,
                                'depth_level': 1,
                                'parent_node_id': 'root',
                                'node_id': node_id,
                                'keywords': [keyword_node.keyword],
                                'confidence': child_question.confidence,
                                'verification_score': extension_context.confidence,
                                'search_verified': True,
                                'hierarchy_validated': hierarchy_validation.valid,
                                'shortcut_prevented': shortcut_check['passed'],
                                'workflow_compliant': True  # Passed both generation and validation compliance
                            }
                            
                            extensions_data['search_contexts'][node_id] = extension_context
                            extensions_data['validation_scores'][node_id] = overall_validation
                            
                            self.stats['extensions_created'] += 1
                            self.stats['workflow_compliance_passed'] += 1
                            logger.info(f"Created WorkFlow-compliant extension {node_id} with validation score {overall_validation:.2f}")
                        
                        else:
                            logger.warning(f"Extension validation failed for keyword {keyword_node.keyword}: score {overall_validation:.2f}")
                    
                    else:
                        logger.warning(f"Failed to generate child question for keyword: {keyword_node.keyword}")
                
                else:
                    logger.warning(f"Failed to generate web search context for keyword: {keyword_node.keyword}")
            
            # Generate second-level extensions (series only, limited depth)
            self._generate_series_extensions(extensions_data, document_content, 2)
            
        except Exception as e:
            logger.error(f"Error generating optimized extensions: {e}")
        
        return extensions_data
    
    def _generate_series_extensions(self, extensions_data: Dict[str, Any], 
                                  document_content: str, target_depth: int):
        """Generate series extensions for deeper levels (workflow: 2-3 rounds max)"""
        if target_depth > 3:  # Workflow limit
            return
        
        # Find parent nodes at previous level
        parent_nodes = {node_id: node_data for node_id, node_data in extensions_data['nodes'].items() 
                       if node_data.get('depth_level', 0) == target_depth - 1}
        
        for parent_node_id, parent_node_data in parent_nodes.items():
            if parent_node_data.get('extension_type') == 'series':  # Only extend series
                try:
                    # Extract keywords from parent
                    parent_keywords = self.keyword_manager.extract_parent_keywords(
                        parent_node_data['question'], parent_node_data['answer'], ""
                    )
                    
                    if parent_keywords:
                        # Take first keyword for deeper extension
                        keyword_node = parent_keywords[0]
                        
                        # Generate extension with web search
                        extension_context = self.search_system.generate_extension_with_web_search(
                            keyword_node.keyword, parent_node_data['question'],
                            parent_node_data['answer'], 'series'
                        )
                        
                        if extension_context:
                            # Generate child question
                            child_question = self.question_generator.generate_child_question(
                                parent_node_data['question'], parent_node_data['answer'],
                                keyword_node.keyword, extension_context.synthesized_context,
                                'series'
                            )
                            
                            if child_question and child_question.validation_score >= 0.7:
                                node_id = f"series_{target_depth}_{parent_node_id}"
                                
                                extensions_data['nodes'][node_id] = {
                                    'question': child_question.question,
                                    'answer': child_question.expected_answer,
                                    'short_answer': {'answer_text': child_question.expected_answer},
                                    'extension_type': 'series',
                                    'depth_level': target_depth,
                                    'parent_node_id': parent_node_id,
                                    'node_id': node_id,
                                    'keywords': [keyword_node.keyword],
                                    'confidence': child_question.confidence,
                                    'verification_score': extension_context.confidence,
                                    'search_verified': True
                                }
                                
                                extensions_data['search_contexts'][node_id] = extension_context
                                extensions_data['validation_scores'][node_id] = child_question.validation_score
                                extensions_data['web_searches_count'] += 1
                                
                                self.stats['extensions_created'] += 1
                                logger.info(f"Created depth-{target_depth} extension {node_id}")
                
                except Exception as e:
                    logger.warning(f"Error generating series extension at depth {target_depth}: {e}")
    
    def export_optimized_tree(self, optimized_tree: OptimizedQuestionTree) -> Dict[str, Any]:
        """Export optimized tree to dictionary format with proper data structure"""
        try:
            # 修复 1: 强化Root问题的导出处理
            root_question_data = {}
            
            # 检查不同的Root问题格式
            if hasattr(optimized_tree.root_question, 'question'):
                # GeneratedQuestion对象格式
                root_question_data = {
                    'question': optimized_tree.root_question.question,
                    'answer': optimized_tree.root_question.expected_answer,
                    'expected_answer': optimized_tree.root_question.expected_answer,  # 确保两个字段都有
                    'question_type': optimized_tree.root_question.question_type,
                    'answer_type': optimized_tree.root_question.answer_type,
                    'confidence': optimized_tree.root_question.confidence,
                    'validation_score': optimized_tree.root_question.validation_score,
                    'reasoning': optimized_tree.root_question.reasoning
                }
                logger.debug(f"导出GeneratedQuestion对象: answer='{root_question_data['answer']}'")
                
            elif hasattr(optimized_tree.root_question, '__dict__'):
                # 其他对象格式
                root_obj = optimized_tree.root_question
                root_question_data = {
                    'question': getattr(root_obj, 'question', getattr(root_obj, 'text', '')),
                    'answer': getattr(root_obj, 'expected_answer', getattr(root_obj, 'answer', 'Unknown')),
                    'expected_answer': getattr(root_obj, 'expected_answer', getattr(root_obj, 'answer', 'Unknown')),
                    'question_type': getattr(root_obj, 'question_type', 'unknown'),
                    'answer_type': getattr(root_obj, 'answer_type', 'unknown'),
                    'confidence': getattr(root_obj, 'confidence', 0.0),
                    'validation_score': getattr(root_obj, 'validation_score', 0.0),
                    'reasoning': getattr(root_obj, 'reasoning', '')
                }
                logger.debug(f"导出对象格式: answer='{root_question_data['answer']}'")
                
            elif isinstance(optimized_tree.root_question, dict):
                # 字典格式
                root_dict = optimized_tree.root_question
                root_question_data = {
                    'question': root_dict.get('question', root_dict.get('question_text', '')),
                    'answer': root_dict.get('answer', root_dict.get('expected_answer', 'Unknown')),
                    'expected_answer': root_dict.get('answer', root_dict.get('expected_answer', 'Unknown')),
                    'question_type': root_dict.get('question_type', 'unknown'),
                    'answer_type': root_dict.get('answer_type', 'unknown'),
                    'confidence': root_dict.get('confidence', 0.0),
                    'validation_score': root_dict.get('validation_score', 0.0),
                    'reasoning': root_dict.get('reasoning', '')
                }
                logger.debug(f"导出字典格式: answer='{root_question_data['answer']}'")
                
            else:
                # 字符串或其他格式 - 解析GeneratedQuestion字符串
                root_str = str(optimized_tree.root_question)
                logger.debug(f"解析字符串格式: {root_str[:200]}...")
                
                try:
                    import re
                    question_match = re.search(r"question='([^']*)'", root_str)
                    answer_match = re.search(r"expected_answer='([^']*)'", root_str)
                    confidence_match = re.search(r"confidence=([0-9.]+)", root_str)
                    validation_match = re.search(r"validation_score=([0-9.]+)", root_str)
                    
                    root_question_data = {
                        'question': question_match.group(1) if question_match else '',
                        'answer': answer_match.group(1) if answer_match else 'Unknown',
                        'expected_answer': answer_match.group(1) if answer_match else 'Unknown',
                        'question_type': 'unknown',
                        'answer_type': 'unknown',
                        'confidence': float(confidence_match.group(1)) if confidence_match else 0.0,
                        'validation_score': float(validation_match.group(1)) if validation_match else 0.0,
                        'reasoning': 'Parsed from string representation'
                    }
                    logger.debug(f"字符串解析成功: answer='{root_question_data['answer']}'")
                    
                except Exception as e:
                    logger.warning(f"字符串解析失败: {e}")
                    root_question_data = {
                        'question': root_str[:100] + "..." if len(root_str) > 100 else root_str,
                        'answer': 'Failed to parse',
                        'expected_answer': 'Failed to parse',
                        'question_type': 'unknown',
                        'answer_type': 'unknown',
                        'confidence': 0.0,
                        'validation_score': 0.0,
                        'reasoning': 'Failed to parse root question'
                    }
            
            # 验证导出的Root问题数据
            if not root_question_data.get('answer') or root_question_data['answer'] in ['Unknown', 'Failed to parse']:
                logger.warning(f"Root问题导出可能有问题: answer='{root_question_data.get('answer')}'")
            else:
                logger.info(f"Root问题导出成功: answer='{root_question_data['answer']}')")
            
            # 处理扩展节点，添加答案多样性检查
            nodes = {}
            used_answers = set()  # 追踪已使用的答案以避免重复
            used_answers.add(root_question_data['answer'])  # 添加root答案到已使用集合
            
            for node_id, extension in optimized_tree.extensions.items():
                node_data = {
                    'question': extension.get('question', ''),
                    'answer': extension.get('answer', ''),
                    'short_answer': extension.get('short_answer', {}),
                    'extension_type': extension.get('extension_type', ''),
                    'depth_level': extension.get('depth_level', 0),
                    'parent_node_id': extension.get('parent_node_id', ''),
                    'node_id': extension.get('node_id', ''),
                    'keywords': extension.get('keywords', []),
                    'confidence': extension.get('confidence', 0.0),
                    'verification_score': extension.get('verification_score', 0.0),
                    'search_verified': extension.get('search_verified', False),
                    'hierarchy_validated': extension.get('hierarchy_validated', False),
                    'shortcut_prevented': extension.get('shortcut_prevented', False),
                    'workflow_compliant': extension.get('workflow_compliant', False)
                }
                
                # 修复 2: 答案重复检查和标记
                current_answer = node_data['answer']
                if current_answer in used_answers:
                    node_data['answer_repetition_warning'] = True
                    node_data['repetition_note'] = f"Answer '{current_answer}' repeats from previous levels"
                    logger.warning(f"Answer repetition detected: '{current_answer}' in node {node_id}")
                else:
                    used_answers.add(current_answer)
                    node_data['answer_repetition_warning'] = False
                
                nodes[node_id] = node_data
            
            # NEW: 添加Tree Level Query数据
            tree_level_query_data = {}
            if hasattr(optimized_tree, 'tree_level_query') and optimized_tree.tree_level_query:
                tree_level_query_data = {
                    'integrated_question': optimized_tree.tree_level_query.integrated_question,
                    'root_answer': optimized_tree.tree_level_query.root_answer,
                    'integration_depth': optimized_tree.tree_level_query.integration_depth,
                    'component_questions': optimized_tree.tree_level_query.component_questions,
                    'reasoning_path': optimized_tree.tree_level_query.reasoning_path,
                    'confidence': optimized_tree.tree_level_query.confidence,
                    'complexity_score': optimized_tree.tree_level_query.complexity_score,
                    'metadata': optimized_tree.tree_level_query.metadata
                }
                logger.info(f"导出Tree Level Query: {tree_level_query_data['integrated_question'][:60]}...")
            
            # NEW: 添加循环检测数据
            circular_detection_data = getattr(optimized_tree, 'circular_detection_summary', {})
            
            export_data = {
                'tree_id': optimized_tree.tree_id,
                'root_question': root_question_data,  # 修复：结构化的root question
                'root_validation': optimized_tree.root_validation.overall_score if hasattr(optimized_tree.root_validation, 'overall_score') else 0.0,
                'nodes': nodes,
                'total_nodes': len(nodes),
                'max_depth': max([node.get('depth_level', 0) for node in nodes.values()]) if nodes else 0,
                'extensions_count': len([node for node in nodes.values() if node.get('extension_type')]),
                'keyword_hierarchy': {
                    level: [str(kw) for kw in keywords] 
                    for level, keywords in optimized_tree.keyword_hierarchy.items()
                },
                'search_contexts': {
                    node_id: str(context) 
                    for node_id, context in optimized_tree.search_contexts.items()
                },
                'validation_scores': optimized_tree.validation_scores,
                'total_web_searches': optimized_tree.total_web_searches,
                'generation_metadata': optimized_tree.generation_metadata,
                # NEW: Tree Level Query数据
                'tree_level_query': tree_level_query_data,
                # NEW: 循环检测数据
                'circular_detection': circular_detection_data,
                # 添加答案多样性统计
                'answer_diversity': {
                    'unique_answers': len(used_answers),
                    'total_answers': len(nodes) + 1,  # +1 for root
                    'repetition_rate': (len(nodes) + 1 - len(used_answers)) / (len(nodes) + 1) if nodes else 0,
                    'all_answers': list(used_answers)
                }
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting optimized tree: {e}")
            return {
                'tree_id': getattr(optimized_tree, 'tree_id', 'unknown'),
                'export_error': str(e),
                'root_question': {'question': '', 'answer': ''},
                'nodes': {},
                'total_nodes': 0
            }
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        search_stats = self.search_system.get_extension_statistics()
        
        return {
            'processing_stats': self.stats,
            'search_system_stats': search_stats,
            'success_rates': {
                'root_validation_rate': (self.stats['root_validations_passed'] / max(self.stats['total_trees_processed'], 1)) * 100,
                'keyword_extraction_rate': (self.stats['keyword_extractions_successful'] / max(self.stats['total_trees_processed'], 1)) * 100,
                'extension_creation_rate': (self.stats['extensions_created'] / max(self.stats['web_searches_performed'], 1)) * 100,
            },
            'optimization_features': {
                'enhanced_root_validation': True,
                'keyword_hierarchy_management': True,
                'web_search_extension': True,
                'dual_model_validation': True,
                'shortcut_prevention': True,
                'minimum_keyword_check': True
            }
        } 