#!/usr/bin/env python3
"""
Simple Trajectory Recorder
只记录过程数据变化，不使用LLM，专注于轨迹记录本身的功能
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProcessStep:
    """处理步骤记录"""
    step_name: str
    step_type: str  # 'generation', 'validation', 'extraction', 'search'
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: float
    duration: float
    success: bool

@dataclass
class TreeTrajectory:
    """问题树生成轨迹"""
    trajectory_id: str
    document_id: str
    start_time: float
    end_time: float
    
    # 处理步骤
    process_steps: List[ProcessStep]
    
    # 最终统计
    total_steps: int
    successful_steps: int
    failed_steps: int
    total_duration: float
    success_rate: float
    
    # 树结构统计
    final_tree_depth: int
    final_tree_size: int
    total_questions: int
    total_keywords_extracted: int
    total_web_searches: int
    
    # 质量指标
    average_validation_score: float
    hierarchy_compliance_rate: float
    shortcut_prevention_rate: float

class SimpleTrajectoryRecorder:
    """简化的轨迹记录器 - 只记录数据，不调用LLM"""
    
    def __init__(self):
        self.current_trajectory: Optional[TreeTrajectory] = None
        self.trajectories: List[TreeTrajectory] = []
        self.step_counter = 0
        
    def start_trajectory(self, document_id: str) -> str:
        """开始记录轨迹"""
        trajectory_id = f"traj_{int(time.time())}_{len(self.trajectories)}"
        
        self.current_trajectory = TreeTrajectory(
            trajectory_id=trajectory_id,
            document_id=document_id,
            start_time=time.time(),
            end_time=0,
            process_steps=[],
            total_steps=0,
            successful_steps=0,
            failed_steps=0,
            total_duration=0,
            success_rate=0.0,
            final_tree_depth=0,
            final_tree_size=0,
            total_questions=0,
            total_keywords_extracted=0,
            total_web_searches=0,
            average_validation_score=0.0,
            hierarchy_compliance_rate=0.0,
            shortcut_prevention_rate=0.0
        )
        
        self.step_counter = 0
        logger.info(f"Started trajectory recording: {trajectory_id}")
        return trajectory_id
    
    def record_step(self, step_name: str, step_type: str, input_data: Dict[str, Any], 
                   output_data: Dict[str, Any], success: bool, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录单个处理步骤"""
        if not self.current_trajectory:
            logger.warning("No active trajectory to record step")
            return
        
        step_start = time.time()
        self.step_counter += 1
        
        step = ProcessStep(
            step_name=step_name,
            step_type=step_type,
            input_data=input_data.copy() if input_data else {},
            output_data=output_data.copy() if output_data else {},
            metadata=metadata.copy() if metadata else {},
            timestamp=step_start,
            duration=0.1,  # 简化处理，不精确计时
            success=success
        )
        
        self.current_trajectory.process_steps.append(step)
        self.current_trajectory.total_steps += 1
        
        if success:
            self.current_trajectory.successful_steps += 1
        else:
            self.current_trajectory.failed_steps += 1
        
        logger.debug(f"Recorded step {self.step_counter}: {step_name} ({'✓' if success else '✗'})")
    
    def record_root_generation(self, document_content: str, short_answer: str, 
                             answer_type: str, generated_question: Optional[str]) -> None:
        """记录根问题生成"""
        self.record_step(
            step_name="root_question_generation",
            step_type="generation",
            input_data={
                "document_length": len(document_content),
                "short_answer": short_answer,
                "answer_type": answer_type
            },
            output_data={
                "generated_question": generated_question,
                "question_length": len(generated_question) if generated_question else 0
            },
            success=generated_question is not None,
            metadata={"step_order": self.step_counter + 1}
        )
    
    def record_root_validation(self, question: str, answer: str, validation_result: Any) -> None:
        """记录根问题验证"""
        # 提取验证结果数据（不调用LLM）
        validation_data = {
            "passed": getattr(validation_result, 'passed', False),
            "overall_score": getattr(validation_result, 'overall_score', 0.0),
            "validity_score": getattr(validation_result, 'validity_score', 0.0),
            "uniqueness_score": getattr(validation_result, 'uniqueness_score', 0.0),
            "specificity_score": getattr(validation_result, 'specificity_score', 0.0),
            "issues_count": len(getattr(validation_result, 'issues', []))
        }
        
        self.record_step(
            step_name="root_question_validation",
            step_type="validation", 
            input_data={
                "question": question,
                "answer": answer
            },
            output_data=validation_data,
            success=validation_data["passed"],
            metadata={"validation_type": "dual_model"}
        )
    
    def record_keyword_extraction(self, question: str, answer: str, extracted_keywords: List[Any]) -> None:
        """记录关键词提取"""
        keywords_data = []
        total_confidence = 0.0
        
        for kw in extracted_keywords:
            if hasattr(kw, 'keyword'):
                confidence = getattr(kw, 'extraction_confidence', 0.0)
                keywords_data.append({
                    "keyword": kw.keyword,
                    "type": getattr(kw, 'keyword_type', 'unknown'),
                    "confidence": confidence
                })
                total_confidence += confidence
        
        avg_confidence = total_confidence / max(len(keywords_data), 1)
        
        self.record_step(
            step_name="keyword_extraction",
            step_type="extraction",
            input_data={
                "question": question,
                "answer": answer
            },
            output_data={
                "keywords_count": len(keywords_data),
                "keywords": keywords_data,
                "average_confidence": avg_confidence
            },
            success=len(keywords_data) > 0,
            metadata={"extraction_method": "llm_based"}
        )
        
        self.current_trajectory.total_keywords_extracted += len(keywords_data)
    
    def record_web_search(self, search_query: str, search_results: List[str], success: bool) -> None:
        """记录Web搜索"""
        self.record_step(
            step_name="web_search",
            step_type="search",
            input_data={
                "search_query": search_query
            },
            output_data={
                "results_count": len(search_results),
                "has_results": len(search_results) > 0
            },
            success=success,
            metadata={"search_engine": "web_search_api"}
        )
        
        self.current_trajectory.total_web_searches += 1
    
    def record_extension_generation(self, parent_keyword: str, extension_type: str, 
                                  generated_question: Optional[str], generated_answer: str,
                                  hierarchy_valid: bool, shortcut_prevented: bool) -> None:
        """记录扩展生成"""
        self.record_step(
            step_name=f"extension_generation_{extension_type}",
            step_type="generation",
            input_data={
                "parent_keyword": parent_keyword,
                "extension_type": extension_type
            },
            output_data={
                "generated_question": generated_question,
                "generated_answer": generated_answer,
                "hierarchy_valid": hierarchy_valid,
                "shortcut_prevented": shortcut_prevented
            },
            success=generated_question is not None,
            metadata={
                "extension_type": extension_type,
                "hierarchy_compliance": hierarchy_valid,
                "shortcut_prevention": shortcut_prevented
            }
        )
        
        if generated_question:
            self.current_trajectory.total_questions += 1
    
    def record_compliance_check(self, check_type: str, context: Dict[str, Any], 
                               compliant: bool, violations: List[str]) -> None:
        """记录WorkFlow符合性检查"""
        self.record_step(
            step_name=f"compliance_check_{check_type}",
            step_type="validation",
            input_data={
                "check_type": check_type,
                "context_keys": list(context.keys())
            },
            output_data={
                "compliant": compliant,
                "violations_count": len(violations),
                "violations": violations
            },
            success=compliant,
            metadata={"compliance_type": "workflow_enforcement"}
        )
    
    def finalize_trajectory(self, final_tree_depth: int, final_tree_size: int) -> TreeTrajectory:
        """完成轨迹记录"""
        if not self.current_trajectory:
            return None
        
        self.current_trajectory.end_time = time.time()
        self.current_trajectory.total_duration = (
            self.current_trajectory.end_time - self.current_trajectory.start_time
        )
        self.current_trajectory.final_tree_depth = final_tree_depth
        self.current_trajectory.final_tree_size = final_tree_size
        
        # 计算成功率
        if self.current_trajectory.total_steps > 0:
            self.current_trajectory.success_rate = (
                self.current_trajectory.successful_steps / self.current_trajectory.total_steps
            )
        
        # 计算质量指标（基于已记录的数据）
        validation_scores = []
        hierarchy_compliant_count = 0
        shortcut_prevented_count = 0
        extension_count = 0
        
        for step in self.current_trajectory.process_steps:
            if step.step_type == "validation" and "overall_score" in step.output_data:
                validation_scores.append(step.output_data["overall_score"])
            
            if step.step_name.startswith("extension_generation"):
                extension_count += 1
                if step.metadata.get("hierarchy_compliance", False):
                    hierarchy_compliant_count += 1
                if step.metadata.get("shortcut_prevention", False):
                    shortcut_prevented_count += 1
        
        # 设置质量指标
        if validation_scores:
            self.current_trajectory.average_validation_score = sum(validation_scores) / len(validation_scores)
        
        if extension_count > 0:
            self.current_trajectory.hierarchy_compliance_rate = hierarchy_compliant_count / extension_count
            self.current_trajectory.shortcut_prevention_rate = shortcut_prevented_count / extension_count
        
        # 保存并重置
        completed_trajectory = self.current_trajectory
        self.trajectories.append(completed_trajectory)
        
        logger.info(f"Finalized trajectory {completed_trajectory.trajectory_id}: "
                   f"{completed_trajectory.success_rate:.1%} success rate, "
                   f"{completed_trajectory.total_steps} total steps, "
                   f"{completed_trajectory.total_questions} questions generated")
        
        self.current_trajectory = None
        return completed_trajectory
    
    def get_trajectory_summary(self) -> Dict[str, Any]:
        """获取轨迹摘要统计"""
        if not self.trajectories:
            return {"message": "No trajectories recorded"}
        
        total_trajectories = len(self.trajectories)
        total_processing_time = sum(t.total_duration for t in self.trajectories)
        total_questions = sum(t.total_questions for t in self.trajectories)
        total_searches = sum(t.total_web_searches for t in self.trajectories)
        
        avg_success_rate = sum(t.success_rate for t in self.trajectories) / total_trajectories
        avg_validation_score = sum(t.average_validation_score for t in self.trajectories) / total_trajectories
        avg_hierarchy_compliance = sum(t.hierarchy_compliance_rate for t in self.trajectories) / total_trajectories
        
        return {
            "total_trajectories": total_trajectories,
            "total_processing_time": round(total_processing_time, 2),
            "average_processing_time": round(total_processing_time / total_trajectories, 2),
            "total_questions_generated": total_questions,
            "total_web_searches": total_searches,
            "average_success_rate": round(avg_success_rate, 3),
            "average_validation_score": round(avg_validation_score, 3),
            "average_hierarchy_compliance": round(avg_hierarchy_compliance, 3),
            "trajectories_completed": total_trajectories
        }
    
    def export_trajectories(self) -> List[Dict[str, Any]]:
        """导出轨迹数据"""
        return [asdict(trajectory) for trajectory in self.trajectories] 