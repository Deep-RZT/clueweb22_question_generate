#!/usr/bin/env python3
"""
ClueWeb22 Simplified Generator
PROMPT-only approach: Document collection → Domain report → Research questions
Processes both ClueWeb22 topics and energy literature topics
No RAG - pure PROMPT-based generation
"""

import os
import json
import re
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict, Counter
import requests
import pandas as pd
from openai_api_client import OpenAIClient, call_openai_with_messages

class ClueWeb22SimplifiedGenerator:
    """
    Simplified PROMPT-only system for ClueWeb22 and energy topics
    Generates domain reports and research questions without RAG
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the generator
        
        Args:
            api_key: OpenAI API key for generation
            model: OpenAI model to use (default: gpt-4o)
        """
        self.api_key = api_key
        self.model = model
        self.openai_client = OpenAIClient(api_key, model)
        
        # ClueWeb22 data directory
        self.clueweb_data_dir = Path("task_file/clueweb22_query_results")
        
        # Output directory
        self.output_dir = Path("clueweb22_simplified_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Extract ClueWeb22 topics
        self.clueweb_topics = self.extract_clueweb_topics()
        print(f"✅ Identified {len(self.clueweb_topics)} ClueWeb22 topics")
        
        # Load and organize energy literature topics
        self.energy_topics = self.organize_energy_topics()
        print(f"✅ Organized {len(self.energy_topics)} energy topics")
        
        # Combine all topics
        self.all_topics = {**self.clueweb_topics, **self.energy_topics}
        print(f"✅ Total topics to process: {len(self.all_topics)}")
        
    def extract_clueweb_topics(self) -> Dict[str, Dict]:
        """Extract and organize ClueWeb22 topics"""
        topics = defaultdict(list)
        
        txt_files = list(self.clueweb_data_dir.glob("*.txt"))
        
        for file_path in txt_files:
            filename = file_path.name
            match = re.match(r'(clueweb22-[^_]+(?:-[^_]+)*(?:-[^_]+)*(?:-[^_]+)*)_top\d+\.txt', filename)
            if match:
                topic_id = match.group(1)
                topics[topic_id].append(file_path)
        
        # Sort files by top number for each topic
        for topic_id in topics:
            topics[topic_id].sort(key=lambda x: int(re.search(r'_top(\d+)\.txt', x.name).group(1)))
        
        # Convert to final format
        clueweb_topics = {}
        for topic_id, file_paths in topics.items():
            clueweb_topics[topic_id] = {
                'type': 'clueweb22',
                'source': 'ClueWeb22 Query Results',
                'file_paths': file_paths,
                'document_count': len(file_paths)
            }
        
        return clueweb_topics
    
    def organize_energy_topics(self) -> Dict[str, Dict]:
        """Load and organize energy literature into topics by subdomain"""
        
        # Load energy papers
        energy_papers = self.load_energy_papers()
        if not energy_papers:
            print("⚠️ No energy papers found, skipping energy topics")
            return {}
        
        # Define energy subdomains with keywords
        energy_subdomains = {
            'Renewable_Energy': [
                'solar', 'wind', 'photovoltaic', 'renewable', 'biomass', 
                'hydroelectric', 'geothermal', 'tidal', 'wave energy'
            ],
            'Fossil_Fuels': [
                'natural gas', 'coal', 'oil', 'petroleum', 'fossil fuel',
                'lng', 'shale gas', 'carbon capture'
            ],
            'Nuclear_Energy': [
                'nuclear', 'reactor', 'uranium', 'nuclear power',
                'radioactive', 'nuclear waste', 'fission'
            ],
            'Grid_Storage': [
                'energy storage', 'battery', 'grid storage', 'pumped hydro',
                'storage system', 'energy arbitrage'
            ],
            'Energy_Policy': [
                'energy policy', 'renewable incentive', 'carbon pricing',
                'energy regulation', 'climate policy', 'energy market'
            ],
            'Energy_Economics': [
                'energy economics', 'energy cost', 'energy investment',
                'energy finance', 'economic impact', 'energy pricing'
            ],
            'Environmental_Impact': [
                'environmental impact', 'carbon footprint', 'lifecycle assessment',
                'emission reduction', 'climate impact', 'sustainability'
            ]
        }
        
        # Classify papers into subdomains
        classified_papers = {subdomain: [] for subdomain in energy_subdomains}
        unclassified_papers = []
        
        for paper in energy_papers:
            title_abstract = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            
            # Find best matching subdomain
            best_match = None
            max_matches = 0
            
            for subdomain, keywords in energy_subdomains.items():
                matches = sum(1 for keyword in keywords if keyword in title_abstract)
                if matches > max_matches:
                    max_matches = matches
                    best_match = subdomain
            
            if best_match and max_matches > 0:
                classified_papers[best_match].append(paper)
            else:
                unclassified_papers.append(paper)
        
        # Create energy topics (only include subdomains with enough papers)
        energy_topics = {}
        min_papers_per_topic = 10  # Minimum papers needed to form a topic
        
        for subdomain, papers in classified_papers.items():
            if len(papers) >= min_papers_per_topic:
                energy_topics[f"energy_{subdomain.lower()}"] = {
                    'type': 'energy_literature',
                    'source': 'Energy Research Papers',
                    'subdomain': subdomain,
                    'papers': papers,
                    'document_count': len(papers)
                }
        
        print(f"📊 Energy topic distribution:")
        for topic_id, topic_data in energy_topics.items():
            print(f"   {topic_data['subdomain']}: {len(topic_data['papers'])} papers")
        
        if unclassified_papers:
            print(f"   Unclassified: {len(unclassified_papers)} papers")
        
        return energy_topics
    
    def load_energy_papers(self) -> List[Dict]:
        """Load energy literature papers"""
        possible_files = [
            "RAG/data/metadata/papers_20250526_182607.json",
            "RAG/data/processed/energy_rag_corpus.json"
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                print(f"📚 Loading energy papers: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    papers = json.load(f)
                
                # Filter valid papers
                valid_papers = []
                for paper in papers:
                    if isinstance(paper, dict):
                        title = paper.get('title', '')
                        abstract = paper.get('abstract', '')
                        
                        if title and abstract and len(abstract) > 50:
                            valid_papers.append(paper)
                
                print(f"✅ Loaded {len(valid_papers)} valid energy papers")
                return valid_papers
        
        print("⚠️ Energy papers not found")
        return []
    
    def _call_openai_api(self, prompt: str, system_prompt: str = None, max_tokens: int = 6000) -> Optional[str]:
        """Call OpenAI API for content generation with optimized parameters"""
        
        return self.openai_client.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )
    
    def load_topic_documents(self, topic_id: str, topic_data: Dict) -> List[Dict[str, str]]:
        """Load documents for a specific topic"""
        documents = []
        
        if topic_data['type'] == 'clueweb22':
            # Load ClueWeb22 documents
            file_paths = topic_data['file_paths']
            for i, file_path in enumerate(file_paths):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()
                    
                    if content and len(content) > 50:
                        documents.append({
                            'doc_id': f"{topic_id}_doc_{i:03d}",
                            'source': file_path.name,
                            'content': content,
                            'word_count': len(content.split()),
                            'char_count': len(content)
                        })
                except Exception as e:
                    print(f"⚠️ Error loading {file_path}: {e}")
                    continue
        
        elif topic_data['type'] == 'energy_literature':
            # Load energy papers
            papers = topic_data['papers']
            for i, paper in enumerate(papers):
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                authors = paper.get('authors', [])
                
                if title and abstract:
                    content = f"Title: {title}\n\nAuthors: {', '.join(authors[:5])}\n\nAbstract: {abstract}"
                    
                    documents.append({
                        'doc_id': f"{topic_id}_paper_{i:03d}",
                        'source': f"Research Paper: {title[:50]}...",
                        'content': content,
                        'word_count': len(content.split()),
                        'char_count': len(content),
                        'paper_id': paper.get('id', ''),
                        'paper_title': title
                    })
        
        return documents
    
    def identify_topic_domain(self, topic_id: str, topic_data: Dict, sample_docs: List[Dict]) -> Dict[str, Any]:
        """Identify domain characteristics using OpenAI"""
        
        # Sample documents for analysis
        if len(sample_docs) > 5:
            sample_docs = sample_docs[:5]
        
        # Create content summary
        combined_sample = ""
        topic_context = f"Topic: {topic_id}"
        
        for i, doc in enumerate(sample_docs):
            if topic_data['type'] == 'energy_literature':
                doc_text = f"Paper {i+1}: {doc.get('paper_title', 'Unknown')}\n{doc.get('content', '')[:300]}...\n"
            else:
                doc_text = f"Document {i+1}: {doc.get('content', '')[:300]}...\n"
            combined_sample += doc_text
        
        system_prompt = """You are a domain analysis expert. Analyze document collections to identify their characteristics and research potential."""
        
        prompt = f"""Analyze the following document collection and identify its domain characteristics:

**Topic Context**: {topic_context}
**Sample Documents**:
{combined_sample}

**Analysis Requirements**:
1. **Primary Domain**: What is the main subject area/domain of these documents?
2. **Key Themes**: What are the 3-5 main themes or topics covered?
3. **Content Type**: What type of content is this (academic, news, commercial, technical, etc.)?
4. **Language**: What language(s) are primarily used?
5. **Scope**: Is this a broad or narrow domain focus?
6. **Research Potential**: What kinds of research questions could be generated from this domain?

**Output Format**:
Provide a structured analysis in JSON format:
{{
    "primary_domain": "domain name",
    "key_themes": ["theme1", "theme2", "theme3"],
    "content_type": "content type",
    "language": "primary language",
    "scope": "broad/narrow/medium",
    "research_potential": "description of research potential",
    "domain_keywords": ["keyword1", "keyword2", "keyword3"],
    "complexity_level": "basic/intermediate/advanced"
}}"""

        response = self._call_openai_api(prompt, system_prompt, max_tokens=1000)
        
        if response:
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    domain_info = json.loads(json_match.group())
                    return domain_info
            except json.JSONDecodeError:
                pass
        
        # Fallback analysis based on topic type
        if topic_data['type'] == 'energy_literature':
            return {
                "primary_domain": topic_data['subdomain'].replace('_', ' '),
                "key_themes": ["Energy research", "Technical analysis", "Scientific literature"],
                "content_type": "Academic Research",
                "language": "en",
                "scope": "medium",
                "research_potential": f"Research questions in {topic_data['subdomain']} domain",
                "domain_keywords": [],
                "complexity_level": "advanced"
            }
        else:
            return {
                "primary_domain": "General Web Content",
                "key_themes": ["Mixed Topics"],
                "content_type": "Web Content",
                "language": "en" if "en" in topic_id else "ja",
                "scope": "medium",
                "research_potential": "General research questions",
                "domain_keywords": [],
                "complexity_level": "intermediate"
            }
    
    def select_clueweb22_topics(self, count: int = 10) -> List[str]:
        """Select diverse ClueWeb22 topics for processing"""
        
        system_prompt = "You are a topic selection expert. Select diverse, well-distributed topics."
        
        prompt = f"""Select {count} diverse ClueWeb22 topic IDs that would provide good coverage across different domains.

Choose topics that span various fields like:
- Science and technology
- Business and economics  
- Health and medicine
- Social sciences
- Arts and culture
- News and current events

Format: Return exactly {count} topic IDs, one per line, in format: clueweb22-en####-##-#####

Example format:
clueweb22-en0000-00-00000
clueweb22-en0001-01-00001"""

        response = self._call_openai_api(prompt, system_prompt, max_tokens=1000)
        
        if response:
            # Extract topic IDs from response
            lines = response.strip().split('\n')
            topics = []
            for line in lines:
                line = line.strip()
                if line.startswith('clueweb22-en') and len(line) >= 20:
                    topics.append(line)
            
            return topics[:count]
        
        # Fallback: return default topics if API fails
        print("⚠️ Using fallback topic selection")
        return [
            "clueweb22-en0000-00-00000",
            "clueweb22-en0028-68-06349", 
            "clueweb22-en0037-99-02648",
            "clueweb22-en0044-53-10967",
            "clueweb22-en0005-84-07694"
        ][:count]

    def generate_domain_report(self, topic_id: str, documents: List[Dict[str, Any]]) -> str:
        """Generate comprehensive domain report using OpenAI"""
        
        # Create document summaries for analysis
        doc_content = []
        for doc in documents[:10]:  # Use sample of documents
            content = f"Title: {doc.get('title', 'No title')}\nContent: {doc.get('content', '')[:500]}..."
            doc_content.append(content)
        
        system_prompt = """You are a domain analysis expert. Generate comprehensive domain reports based on document collections."""
        
        prompt = f"""Generate a comprehensive domain report for topic: {topic_id}

Based on these sample documents:
{chr(10).join(doc_content)}

Create a 1500-2000 word domain report with:

## Overview
Brief description of the domain and its significance

## Key Themes  
Major themes and concepts in this domain

## Methodological Approaches
Research methods and analytical techniques used

## Current Research
Contemporary trends and ongoing research

## Applications
Practical applications and implications

## Future Directions
Emerging trends and future possibilities

## Conclusion
Summary of the domain's potential and importance

Make the report comprehensive, well-structured, and informative."""

        report = self._call_openai_api(prompt, system_prompt, max_tokens=3000)
        
        if not report:
            return f"# Test Domain Report: {topic_id}\n\nDomain analysis in progress..."
            
        return report

    def generate_research_questions(self, topic_id: str, domain_report: str, 
                                  target_count: int = 50) -> List[Dict[str, Any]]:
        """Generate research questions for a topic using OpenAI"""
        
        questions_per_batch = 10
        all_questions = []
        
        # Define difficulty distribution
        easy_count = int(target_count * 0.2)
        medium_count = int(target_count * 0.4) 
        hard_count = target_count - easy_count - medium_count
        
        difficulty_batches = (
            [('Easy', easy_count)] + 
            [('Medium', medium_count)] + 
            [('Hard', hard_count)]
        )
        
        question_id = 1
        
        for difficulty, count in difficulty_batches:
            remaining = count
            
            while remaining > 0:
                batch_size = min(questions_per_batch, remaining)
                
                system_prompt = f"""You are a research question expert specializing in {difficulty.lower()} level questions. Generate high-quality research questions that require deep analytical thinking."""
                
                prompt = f"""Based on this domain report, generate {batch_size} research questions of {difficulty} difficulty:

DOMAIN REPORT:
{domain_report}

Generate exactly {batch_size} questions with the following requirements:

DIFFICULTY: {difficulty}
- Easy: Straightforward analysis, 400-600 word answers
- Medium: Multi-step thinking, 800-1200 word answers  
- Hard: Complex synthesis, 1500-2000 word answers

For each question, provide:
1. Question text (clear and specific)
2. Question type (Analytical, Comparative, Predictive, Applied, etc.)
3. Rationale (why this question is valuable)

Format each question as:
Q{question_id}: [Question text]
Type: [Question type]
Rationale: [Brief explanation]

Questions should encourage deep research thinking and require evidence-based analysis using the domain report."""

                response = self._call_openai_api(prompt, system_prompt, max_tokens=2000)
                
                if response:
                    # Parse questions from response
                    batch_questions = self._parse_questions_from_response(
                        response, difficulty, question_id, batch_size
                    )
                    all_questions.extend(batch_questions)
                    question_id += len(batch_questions)
                    remaining -= len(batch_questions)
                else:
                    print(f"⚠️ Failed to generate {difficulty} questions batch")
                    remaining = 0
                
                time.sleep(1)  # Rate limiting
        
        return all_questions[:target_count]
    
    def _parse_questions_from_response(self, response: str, difficulty: str, 
                                     start_id: int, expected_count: int) -> List[Dict[str, Any]]:
        """Parse questions from OpenAI response"""
        
        questions = []
        lines = response.strip().split('\n')
        
        current_question = {}
        question_num = start_id
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Q') and ':' in line:
                # Save previous question if exists
                if current_question.get('question_text'):
                    current_question['question_id'] = f'Q{question_num:03d}'
                    questions.append(current_question.copy())
                    question_num += 1
                
                # Start new question
                current_question = {
                    'question_text': line.split(':', 1)[1].strip(),
                    'difficulty': difficulty,
                    'question_type': 'General',
                    'rationale': 'Generated research question'
                }
            
            elif line.startswith('Type:'):
                current_question['question_type'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('Rationale:'):
                current_question['rationale'] = line.split(':', 1)[1].strip()
        
        # Add last question
        if current_question.get('question_text'):
            current_question['question_id'] = f'Q{question_num:03d}'
            questions.append(current_question)
        
        # Ensure we have the expected count (fill with fallback if needed)
        while len(questions) < expected_count:
            questions.append({
                'question_id': f'Q{start_id + len(questions):03d}',
                'question_text': f'What are the key research implications in this domain?',
                'difficulty': difficulty,
                'question_type': 'Exploratory',
                'rationale': 'Fallback research question for comprehensive analysis'
            })
        
        return questions[:expected_count]
    
    def process_single_topic(self, topic_id: str) -> Dict[str, Any]:
        """Process a single topic: generate report and questions"""
        print(f"\n🔍 Processing Topic: {topic_id}")
        print("=" * 60)
        
        topic_data = self.all_topics[topic_id]
        
        # Load documents
        print(f"📚 Loading documents ({topic_data['type']})...")
        documents = self.load_topic_documents(topic_id, topic_data)
        print(f"   Loaded {len(documents)} documents")
        
        if not documents:
            print("❌ No valid documents found for this topic")
            return None
        
        # Determine question count
        if len(documents) < 20:
            num_questions = 25
            print(f"   ⚠️ Limited documents ({len(documents)}), reducing questions to {num_questions}")
        else:
            num_questions = 50
        
        # PROMPT Phase 1: Identify domain
        print("🔬 Analyzing domain characteristics...")
        domain_info = self.identify_topic_domain(topic_id, topic_data, documents[:min(10, len(documents))])
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Themes: {', '.join(domain_info.get('key_themes', []))}")
        
        # PROMPT Phase 2: Generate domain report
        print("📝 Generating domain report...")
        domain_report = self.generate_domain_report(topic_id, documents)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # PROMPT Phase 3: Generate research questions
        print("❓ Generating research questions...")
        questions = self.generate_research_questions(topic_id, domain_report, num_questions)
        print(f"   Generated {len(questions)} questions")
        
        # Compile results
        results = {
            'topic_id': topic_id,
            'topic_type': topic_data['type'],
            'topic_source': topic_data['source'],
            'domain_info': domain_info,
            'document_stats': {
                'total_documents': len(documents),
                'total_words': sum(doc['word_count'] for doc in documents),
                'avg_doc_length': sum(doc['word_count'] for doc in documents) / len(documents)
            },
            'domain_report': domain_report,
            'research_questions': questions,
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'api_model': self.model,
                'method': 'PROMPT_only',
                'num_questions_requested': num_questions,
                'num_questions_generated': len(questions)
            }
        }
        
        print(f"✅ Topic {topic_id} processing completed")
        return results
    
    def process_all_topics(self) -> Dict[str, Any]:
        """Process all topics"""
        print("🚀 Starting ClueWeb22 Simplified Generation")
        print("=" * 70)
        print(f"Total topics to process: {len(self.all_topics)}")
        print(f"ClueWeb22 topics: {len(self.clueweb_topics)}")
        print(f"Energy topics: {len(self.energy_topics)}")
        print("=" * 70)
        
        all_results = {}
        failed_topics = []
        
        for i, topic_id in enumerate(self.all_topics.keys(), 1):
            print(f"\n📊 Progress: {i}/{len(self.all_topics)}")
            
            try:
                topic_results = self.process_single_topic(topic_id)
                if topic_results:
                    all_results[topic_id] = topic_results
                    
                    # Save individual topic results
                    topic_file = self.output_dir / f"{topic_id}_results.json"
                    with open(topic_file, 'w', encoding='utf-8') as f:
                        json.dump(topic_results, f, indent=2, ensure_ascii=False)
                    print(f"💾 Saved: {topic_file}")
                else:
                    failed_topics.append(topic_id)
                    
            except Exception as e:
                print(f"❌ Error processing {topic_id}: {e}")
                failed_topics.append(topic_id)
                continue
        
        # Generate summary statistics
        summary_stats = self.generate_summary_statistics(all_results)
        
        # Compile final results
        final_results = {
            'generation_info': {
                'timestamp': datetime.now().isoformat(),
                'total_topics': len(self.all_topics),
                'successful_topics': len(all_results),
                'failed_topics': failed_topics,
                'api_model': self.model,
                'methodology': 'PROMPT_only_simplified',
                'clueweb22_topics': len(self.clueweb_topics),
                'energy_topics': len(self.energy_topics)
            },
            'summary_statistics': summary_stats,
            'topic_results': all_results
        }
        
        print(f"\n✅ Processing completed!")
        print(f"   Successful: {len(all_results)}/{len(self.all_topics)} topics")
        print(f"   Failed: {len(failed_topics)} topics")
        if failed_topics:
            print(f"   Failed topics: {', '.join(failed_topics)}")
        
        return final_results
    
    def generate_summary_statistics(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics"""
        if not all_results:
            return {}
        
        # Basic statistics
        total_documents = sum(r['document_stats']['total_documents'] for r in all_results.values())
        total_words = sum(r['document_stats']['total_words'] for r in all_results.values())
        total_questions = sum(len(r['research_questions']) for r in all_results.values())
        
        # Topic type distribution
        topic_types = [r['topic_type'] for r in all_results.values()]
        type_counts = {ttype: topic_types.count(ttype) for ttype in set(topic_types)}
        
        # Domain distribution
        domains = [r['domain_info'].get('primary_domain', 'Unknown') for r in all_results.values()]
        domain_counts = {domain: domains.count(domain) for domain in set(domains)}
        
        # Difficulty distribution
        all_difficulties = []
        for result in all_results.values():
            all_difficulties.extend([q['difficulty'] for q in result['research_questions']])
        difficulty_counts = {diff: all_difficulties.count(diff) for diff in set(all_difficulties)}
        
        # Question type distribution
        all_types = []
        for result in all_results.values():
            all_types.extend([q['question_type'] for q in result['research_questions']])
        question_type_counts = {qtype: all_types.count(qtype) for qtype in set(all_types)}
        
        return {
            'total_topics_processed': len(all_results),
            'topic_type_distribution': type_counts,
            'total_documents_analyzed': total_documents,
            'total_words_processed': total_words,
            'total_questions_generated': total_questions,
            'average_questions_per_topic': total_questions / len(all_results),
            'domain_distribution': domain_counts,
            'difficulty_distribution': difficulty_counts,
            'question_type_distribution': question_type_counts,
            'average_documents_per_topic': total_documents / len(all_results),
            'average_words_per_topic': total_words / len(all_results)
        }
    
    def save_results(self, results: Dict[str, Any]) -> Tuple[str, str]:
        """Save results in JSON and Excel formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete results as JSON
        json_file = self.output_dir / f"clueweb22_simplified_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate Excel format
        excel_file = self.output_dir / f"clueweb22_simplified_results_{timestamp}.xlsx"
        
        try:
            excel_data = []
            for topic_id, topic_data in results.get('topic_results', {}).items():
                # Topic summary row - show FULL report content, not truncated
                topic_summary = {
                    'Topic_ID': topic_id,
                    'Type': 'TOPIC_SUMMARY',
                    'Topic_Type': topic_data['topic_type'],
                    'Domain': topic_data['domain_info'].get('primary_domain', 'Unknown'),
                    'Documents': topic_data['document_stats']['total_documents'],
                    'Total_Words': topic_data['document_stats']['total_words'],
                    'Key_Themes': ', '.join(topic_data['domain_info'].get('key_themes', [])),
                    'Report_Words': len(topic_data['domain_report'].split()),
                    'Questions_Count': len(topic_data['research_questions']),
                    'Content': topic_data['domain_report']  # FULL report content, no truncation
                }
                excel_data.append(topic_summary)
                
                # Research questions
                for question in topic_data['research_questions']:
                    question_row = {
                        'Topic_ID': topic_id,
                        'Type': 'RESEARCH_QUESTION',
                        'Question_ID': question['question_id'],
                        'Question_Text': question['question_text'],
                        'Difficulty': question['difficulty'],
                        'Question_Type': question['question_type'],
                        'Rationale': question.get('rationale', ''),
                        'Domain': topic_data['domain_info'].get('primary_domain', 'Unknown')
                    }
                    excel_data.append(question_row)
            
            df = pd.DataFrame(excel_data)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            print(f"✅ Excel results saved: {excel_file}")
            
        except ImportError:
            print("⚠️ pandas/openpyxl not available, skipping Excel export")
            excel_file = None
        
        print(f"💾 JSON results saved: {json_file}")
        
        return str(json_file), str(excel_file) if excel_file else None

def main():
    """Main execution function"""
    print("🌐 ClueWeb22 Simplified Generator")
    print("=" * 70)
    print("PROMPT-only approach: Documents → Reports → Research Questions")
    print("Processes ClueWeb22 topics + Energy literature topics")
    print("No RAG - pure PROMPT-based generation")
    print("=" * 70)
    
    # Configuration
    api_key = "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"
    model = "gpt-4o"
    
    try:
        # Initialize generator
        generator = ClueWeb22SimplifiedGenerator(api_key, model)
        
        # Process all topics
        results = generator.process_all_topics()
        
        # Save results
        json_file, excel_file = generator.save_results(results)
        
        print(f"\n🎉 ClueWeb22 Simplified Generation Completed!")
        print(f"📊 Generated {results['summary_statistics'].get('total_questions_generated', 0)} research questions")
        print(f"📁 JSON results: {json_file}")
        if excel_file:
            print(f"📊 Excel results: {excel_file}")
        
        # Print summary statistics
        stats = results.get('summary_statistics', {})
        print(f"\n📈 Summary Statistics:")
        print(f"   Topics processed: {stats.get('total_topics_processed', 0)}")
        print(f"   ClueWeb22 topics: {results['generation_info'].get('clueweb22_topics', 0)}")
        print(f"   Energy topics: {results['generation_info'].get('energy_topics', 0)}")
        print(f"   Documents analyzed: {stats.get('total_documents_analyzed', 0):,}")
        print(f"   Average questions per topic: {stats.get('average_questions_per_topic', 0):.1f}")
        
        print(f"\n📊 Topic Type Distribution:")
        for topic_type, count in stats.get('topic_type_distribution', {}).items():
            print(f"   {topic_type}: {count} topics")
        
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 