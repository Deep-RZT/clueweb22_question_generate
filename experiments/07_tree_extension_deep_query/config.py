"""
Configuration file for Tree Extension Deep Query Framework (Experiment 07)
Defines all parameters for document processing, question generation, and extension logic.
"""

import os
from typing import Dict, Any, List

class TreeExtensionConfig:
    """Configuration class for the Tree Extension Deep Query Framework"""
    
    def __init__(self):
        # Basic settings
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.experiment_name = "tree_extension_deep_query"
        self.version = "1.0.0"
        
        # Data paths
        self.clueweb22_path = os.path.join(self.project_root, "data", "clueweb22")
        self.output_dir = os.path.join(os.path.dirname(__file__), "results")
        self.log_dir = os.path.join(os.path.dirname(__file__), "logs")
        
        # Target settings
        self.target_total_questions = 800  # Final goal: 8 topics × 100 docs
        self.initial_test_questions = 100  # For initial analysis
        self.max_docs_per_topic = 100
        
        # Document screening
        self.document_quality_threshold = 0.6  # LLM screening threshold
        self.min_document_length = 200  # Minimum characters
        self.max_document_length = 10000  # Maximum characters for processing
        
        # Short answer criteria
        self.answer_types = ["noun", "number", "name", "date", "location"]
        self.min_answer_length = 2  # Minimum characters
        self.max_answer_length = 50  # Maximum characters
        self.avoid_answer_types = ["how", "why", "opinion", "subjective"]
        
        # Extension structure
        self.max_series_depth = 3  # Maximum series extension layers
        self.parallel_branches = 2  # Number of parallel extensions
        self.extension_selection_method = "llm_choice"  # LLM decides parallel vs series
        
        # Search integration
        self.max_search_calls_per_extension = 1  # Limit API calls
        self.search_timeout = 30  # Seconds
        self.enable_search_verification = True  # Enabled: Fixing Deep Research API calls
        
        # Verification thresholds (优化后的合理阈值)
        self.validity_threshold = 0.65  # Minimum validity score
        self.uniqueness_threshold = 0.65  # Minimum uniqueness score
        self.avoid_circular_references = True
        
        # API settings
        self.openai_model = "gpt-4o"
        self.openai_temperature = 0.3  # Lower for more consistent results
        self.max_tokens_per_request = 2000
        self.api_retry_attempts = 3
        self.api_retry_delay = 2  # Seconds
        
        # Trajectory recording
        self.record_full_trajectory = True
        self.record_reasoning_steps = True
        self.record_keyword_mapping = True
        self.record_verification_details = True
        
        # Output settings
        self.export_formats = ["json", "excel"]
        self.include_analysis_report = True
        self.timestamp_outputs = True
        
        # Production targets (as specified in requirements)
        self.target_total_questions = 800  # 8 topics × 100 questions each
        self.initial_analysis_batch = 100  # Generate 100 first for analysis
        self.questions_per_topic = 100  # Target per topic
        self.expected_topics = 8  # Expected number of topics in clueweb22
        
        # Quality control
        self.minimum_keyword_count = 2  # Minimum keywords for uniqueness identification
        self.filter_advertisement_content = True  # Screen out ads and irrelevant content
        self.objective_fact_priority = True  # Prioritize names, numbers, dates
        self.avoid_explanatory_questions = True  # Avoid how/why questions
        
        # Quality control
        self.enable_quality_filters = True
        self.filter_inappropriate_content = True
        self.filter_advertising_content = True
        self.filter_meaningless_content = True
        
        # Performance settings
        self.batch_size = 10  # Documents processed in batch
        self.parallel_processing = False  # Keep false for API rate limits
        self.progress_save_interval = 5  # Save progress every N questions (防止长时间运行时的数据丢失)
        
        # Debug settings
        self.debug_mode = False
        self.verbose_logging = True
        self.save_intermediate_results = True

    def get_clueweb22_file_pattern(self) -> str:
        """Get the file pattern for ClueWeb22 English documents"""
        return "**/en*.txt"
    
    def get_prompt_settings(self) -> Dict[str, Any]:
        """Get settings specific to prompt engineering"""
        return {
            "language": "english",
            "style": "instructional_guidance",
            "avoid_domain_hints": True,
            "focus_on_reasoning": True,
            "minimize_answer_hints": True
        }
    
    def get_extension_rules(self) -> Dict[str, Any]:
        """Get rules for question extension logic"""
        return {
            "parallel_extension": {
                "type": "intersection_exploration",
                "focus": "comparative_reasoning",
                "avoid": "repetitive_content"
            },
            "series_extension": {
                "type": "keyword_replacement_deepening",
                "focus": "progressive_complexity",
                "avoid": "circular_references"
            },
            "verification_required": True,
            "maintain_answer_objectivity": True
        }
    
    def get_trajectory_schema(self) -> Dict[str, Any]:
        """Get the schema for trajectory recording"""
        return {
            "document_id": "string",
            "short_answer": "string",
            "base_question": "string",
            "extension_tree": {
                "parallel_branches": "list",
                "series_layers": "list"
            },
            "verification_results": "dict",
            "keyword_mapping": "dict",
            "reasoning_steps": "list",
            "search_calls": "list",
            "final_score": "float"
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Check paths exist
            if not os.path.exists(self.clueweb22_path):
                print(f"Warning: ClueWeb22 path not found: {self.clueweb22_path}")
                return False
            
            # Create output directories
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(self.log_dir, exist_ok=True)
            
            # Validate thresholds
            if not (0 <= self.validity_threshold <= 1):
                raise ValueError("Validity threshold must be between 0 and 1")
            
            if not (0 <= self.uniqueness_threshold <= 1):
                raise ValueError("Uniqueness threshold must be between 0 and 1")
            
            # Validate extension settings
            if self.max_series_depth < 1 or self.max_series_depth > 5:
                raise ValueError("Series depth must be between 1 and 5")
            
            if self.parallel_branches < 1 or self.parallel_branches > 5:
                raise ValueError("Parallel branches must be between 1 and 5")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

# Global config instance
config = TreeExtensionConfig()

# Utility function to get config
def get_config() -> TreeExtensionConfig:
    """Get the global configuration instance"""
    return config

# Validate configuration on import
if not config.validate_config():
    print("Warning: Configuration validation failed. Please check settings.") 