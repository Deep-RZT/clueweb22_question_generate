"""
Document Loader for Tree Extension Deep Query Framework
Handles loading and preprocessing of ClueWeb22 English documents.
"""

import os
import glob
import logging
import re
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
from pathlib import Path

from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class DocumentData:
    """Data structure for a single document"""
    doc_id: str
    file_path: str
    content: str
    topic: str
    length: int
    language: str = "en"
    
    def is_valid(self) -> bool:
        """Check if document meets basic quality criteria"""
        config = get_config()
        return (
            config.min_document_length <= self.length <= config.max_document_length
            and bool(self.content.strip())
            and self.language == "en"
        )

class DocumentLoader:
    """Loads and processes ClueWeb22 English documents"""
    
    def __init__(self):
        self.config = get_config()
        self.loaded_documents = []
        self.topics_found = set()
        
    def discover_topics(self) -> List[str]:
        """Discover available topics in the ClueWeb22 dataset"""
        logger.info(f"Discovering topics in {self.config.clueweb22_path}")
        
        if not os.path.exists(self.config.clueweb22_path):
            logger.error(f"ClueWeb22 path not found: {self.config.clueweb22_path}")
            return []
        
        topics = set()
        
        # Search for English document files directly in the directory
        search_pattern = os.path.join(self.config.clueweb22_path, "clueweb22-en*.txt")
        
        for file_path in glob.glob(search_pattern):
            # Extract topic from filename
            filename = os.path.basename(file_path)
            # Pattern: clueweb22-en0000-00-00000_top000.txt
            # Extract the first part as topic: en0000-00-00000
            topic_match = re.match(r'clueweb22-(en\d+-\d+-\d+)', filename)
            if topic_match:
                topic_base = topic_match.group(1)
                # Use just the first segment for topic grouping: en0000
                topic_segment = topic_base.split('-')[0]
                topics.add(topic_segment)
        
        topics_list = sorted(list(topics))
        logger.info(f"Found {len(topics_list)} English topics: {topics_list}")
        self.topics_found = topics
        
        return topics_list
    
    def load_documents_from_topic(self, topic: str, max_docs: Optional[int] = None) -> List[DocumentData]:
        """Load documents from a specific topic"""
        logger.info(f"Loading documents from topic: {topic}")
        
        if max_docs is None:
            max_docs = self.config.max_docs_per_topic
        
        documents = []
        # Updated pattern to match actual ClueWeb22 file structure
        # For topic like "en0000", search for clueweb22-en0000-*.txt
        search_pattern = os.path.join(self.config.clueweb22_path, f"clueweb22-{topic}-*.txt")
        
        file_paths = glob.glob(search_pattern)
        logger.info(f"Found {len(file_paths)} potential files for topic {topic}")
        
        for file_path in file_paths[:max_docs]:
            try:
                doc = self._load_single_document(file_path, topic)
                if doc and doc.is_valid():
                    documents.append(doc)
                    logger.debug(f"Loaded document: {doc.doc_id} ({doc.length} chars)")
                else:
                    logger.debug(f"Skipped invalid document: {file_path}")
                    
            except Exception as e:
                logger.warning(f"Error loading document {file_path}: {e}")
                continue
        
        logger.info(f"Successfully loaded {len(documents)} valid documents from topic {topic}")
        return documents
    
    def _load_single_document(self, file_path: str, topic: str) -> Optional[DocumentData]:
        """Load a single document file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract document ID from filename
            filename = os.path.basename(file_path)
            doc_id = os.path.splitext(filename)[0]
            
            # Clean content
            content = self._clean_content(content)
            
            if not content:
                return None
            
            return DocumentData(
                doc_id=doc_id,
                file_path=file_path,
                content=content,
                topic=topic,
                length=len(content),
                language="en"
            )
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and preprocess document content"""
        if not content:
            return ""
        
        # Remove common web artifacts
        content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
        content = re.sub(r'\s+', ' ', content)     # Normalize whitespace
        content = content.strip()
        
        # Remove URLs
        content = re.sub(r'http[s]?://\S+', '', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '', content)
        
        # Clean up extra spaces
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def load_all_documents(self, max_total: Optional[int] = None) -> List[DocumentData]:
        """Load documents from all available topics"""
        logger.info("Loading documents from all topics")
        
        if max_total is None:
            max_total = self.config.initial_test_questions
        
        topics = self.discover_topics()
        if not topics:
            logger.error("No topics found!")
            return []
        
        all_documents = []
        docs_per_topic = max(1, max_total // len(topics))
        
        for topic in topics:
            if len(all_documents) >= max_total:
                break
                
            topic_docs = self.load_documents_from_topic(topic, docs_per_topic)
            all_documents.extend(topic_docs)
            
            logger.info(f"Loaded {len(topic_docs)} documents from topic {topic}")
        
        # Limit to target count
        if len(all_documents) > max_total:
            all_documents = all_documents[:max_total]
        
        logger.info(f"Total documents loaded: {len(all_documents)}")
        self.loaded_documents = all_documents
        
        return all_documents
    
    def get_document_by_id(self, doc_id: str) -> Optional[DocumentData]:
        """Get a specific document by ID"""
        for doc in self.loaded_documents:
            if doc.doc_id == doc_id:
                return doc
        return None
    
    def get_documents_by_topic(self, topic: str) -> List[DocumentData]:
        """Get all documents from a specific topic"""
        return [doc for doc in self.loaded_documents if doc.topic == topic]
    
    def get_document_stats(self) -> Dict[str, any]:
        """Get statistics about loaded documents"""
        if not self.loaded_documents:
            return {}
        
        topics = list(set(doc.topic for doc in self.loaded_documents))
        topic_counts = {topic: len(self.get_documents_by_topic(topic)) for topic in topics}
        
        lengths = [doc.length for doc in self.loaded_documents]
        
        return {
            "total_documents": len(self.loaded_documents),
            "topics": topics,
            "topic_counts": topic_counts,
            "average_length": sum(lengths) / len(lengths) if lengths else 0,
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "total_characters": sum(lengths)
        }
    
    def validate_loaded_documents(self) -> Dict[str, any]:
        """Validate all loaded documents"""
        valid_docs = [doc for doc in self.loaded_documents if doc.is_valid()]
        invalid_docs = [doc for doc in self.loaded_documents if not doc.is_valid()]
        
        return {
            "total_loaded": len(self.loaded_documents),
            "valid_documents": len(valid_docs),
            "invalid_documents": len(invalid_docs),
            "validation_rate": len(valid_docs) / len(self.loaded_documents) if self.loaded_documents else 0,
            "invalid_reasons": [
                f"{doc.doc_id}: length={doc.length}" for doc in invalid_docs
            ]
        }

def test_document_loader():
    """Test function for the document loader"""
    loader = DocumentLoader()
    
    # Test topic discovery
    topics = loader.discover_topics()
    print(f"Found topics: {topics}")
    
    # Test loading documents
    if topics:
        documents = loader.load_all_documents(max_total=10)
        print(f"Loaded {len(documents)} documents")
        
        # Print stats
        stats = loader.get_document_stats()
        print(f"Document stats: {stats}")
        
        # Validate documents
        validation = loader.validate_loaded_documents()
        print(f"Validation results: {validation}")
        
        # Show first document
        if documents:
            first_doc = documents[0]
            print(f"\nFirst document sample:")
            print(f"ID: {first_doc.doc_id}")
            print(f"Topic: {first_doc.topic}")
            print(f"Length: {first_doc.length}")
            print(f"Content preview: {first_doc.content[:200]}...")

if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(level=logging.INFO)
    test_document_loader() 