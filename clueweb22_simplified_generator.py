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
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import requests
import pandas as pd

class ClueWeb22SimplifiedGenerator:
    """
    Simplified PROMPT-only system for ClueWeb22 and energy topics
    Generates domain reports and research questions without RAG
    """
    
    def __init__(self, clueweb_data_dir: str, claude_api_key: str):
        """
        Initialize the generator
        
        Args:
            clueweb_data_dir: Path to ClueWeb22 query results directory
            claude_api_key: Claude API key for generation
        """
        self.clueweb_data_dir = Path(clueweb_data_dir)
        self.claude_api_key = claude_api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
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
    
    def call_claude_api(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        """Call Claude API with error handling"""
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.claude_api_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API Call failed: {e}")
            return None
    
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
        """Identify domain characteristics using PROMPT approach"""
        
        # Prepare sample content
        sample_content = []
        for doc in sample_docs[:5]:
            content_preview = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
            sample_content.append(f"Document {doc['doc_id']}:\n{content_preview}\n")
        
        combined_sample = "\n".join(sample_content)
        
        # Add topic type context
        topic_context = ""
        if topic_data['type'] == 'clueweb22':
            topic_context = f"This is a ClueWeb22 web document collection (Topic ID: {topic_id})"
        elif topic_data['type'] == 'energy_literature':
            topic_context = f"This is an energy research literature collection (Subdomain: {topic_data['subdomain']})"
        
        messages = [
            {
                "role": "user",
                "content": f"""Analyze the following document collection and identify its domain characteristics:

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
            }
        ]
        
        response = self.call_claude_api(messages, max_tokens=1000)
        
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
    
    def generate_domain_report(self, topic_id: str, topic_data: Dict, documents: List[Dict], domain_info: Dict) -> str:
        """Generate domain report using PROMPT approach"""
        
        # Prepare document summaries
        doc_summaries = []
        total_words = sum(doc['word_count'] for doc in documents)
        
        # Use more documents for energy topics (they're shorter)
        max_docs_for_report = 30 if topic_data['type'] == 'energy_literature' else 20
        
        for i, doc in enumerate(documents[:max_docs_for_report]):
            if topic_data['type'] == 'energy_literature':
                # For papers, use title and abstract
                summary = f"Paper {i+1}: {doc.get('paper_title', 'Unknown Title')}\n{doc['content'][:400]}..."
            else:
                # For web documents, use content preview
                summary = f"Doc {i+1}: {doc['content'][:300]}..."
            
            doc_summaries.append(summary)
        
        combined_summaries = "\n\n".join(doc_summaries)
        
        # Add topic-specific context
        topic_context = ""
        if topic_data['type'] == 'energy_literature':
            topic_context = f"This collection focuses on {topic_data['subdomain'].replace('_', ' ')} research literature."
        else:
            topic_context = f"This is a ClueWeb22 web document collection."
        
        messages = [
            {
                "role": "user",
                "content": f"""Generate a comprehensive expert-level domain report based on the following document collection:

**Topic Information**:
- Topic ID: {topic_id}
- Topic Type: {topic_data['type']}
- Primary Domain: {domain_info.get('primary_domain', 'Unknown')}
- Key Themes: {', '.join(domain_info.get('key_themes', []))}
- Total Documents: {len(documents)}
- Total Words: {total_words:,}
- Content Type: {domain_info.get('content_type', 'Unknown')}
- Complexity Level: {domain_info.get('complexity_level', 'Unknown')}

**Context**: {topic_context}

**Document Collection Summary**:
{combined_summaries}

**Report Requirements**:
Generate a comprehensive expert-level report (1500-2000 words) that includes:

1. **Executive Summary** (200 words)
   - Overview of the domain and key findings
   - Main themes and trends identified

2. **Domain Analysis** (400-500 words)
   - Detailed analysis of the primary domain
   - Key concepts and terminology
   - Current state and developments

3. **Thematic Breakdown** (400-500 words)
   - Analysis of major themes identified
   - Relationships between different topics
   - Emerging patterns and trends

4. **Technical Insights** (300-400 words)
   - Technical aspects and methodologies
   - Tools, technologies, or approaches mentioned
   - Innovation and development areas

5. **Research Implications** (200-300 words)
   - Potential research directions
   - Knowledge gaps identified
   - Future research opportunities

6. **Conclusion** (100-200 words)
   - Summary of key insights
   - Overall assessment of the domain

**Writing Style**:
- Expert-level academic/professional tone
- Use domain-specific terminology appropriately
- Include specific examples from the documents
- Maintain objectivity and analytical depth
- Structure with clear headings and subheadings"""
            }
        ]
        
        report = self.call_claude_api(messages, max_tokens=3000)
        
        if not report:
            # Fallback report generation
            report = f"""# Domain Report: {domain_info.get('primary_domain', 'Unknown Domain')}

## Executive Summary
This report analyzes {len(documents)} documents from the {topic_id} collection, covering {domain_info.get('primary_domain', 'various topics')}. The collection represents {domain_info.get('content_type', 'content')} with a focus on {', '.join(domain_info.get('key_themes', ['general topics']))}.

## Key Findings
- Primary domain: {domain_info.get('primary_domain', 'Unknown')}
- Content complexity: {domain_info.get('complexity_level', 'Unknown')}
- Total documents analyzed: {len(documents)}
- Research potential: {domain_info.get('research_potential', 'General research opportunities')}

## Domain Characteristics
The document collection shows characteristics of {domain_info.get('scope', 'medium')} scope coverage with potential for {domain_info.get('research_potential', 'various research directions')}.

## Research Opportunities
Based on the document analysis, this domain offers opportunities for research in areas related to {', '.join(domain_info.get('key_themes', ['the identified themes']))}.
"""
        
        return report
    
    def generate_research_questions(self, topic_id: str, topic_data: Dict, domain_report: str, domain_info: Dict, num_questions: int = 50) -> List[Dict]:
        """Generate research questions using PROMPT approach"""
        
        # Adjust question count based on document availability
        if topic_data['document_count'] < 20:
            num_questions = min(25, num_questions)
        
        questions = []
        batch_size = 10
        num_batches = (num_questions + batch_size - 1) // batch_size
        
        difficulty_levels = ['Easy', 'Medium', 'Hard']
        question_types = [
            'Analytical', 'Comparative', 'Evaluative', 'Synthetic', 
            'Predictive', 'Critical', 'Exploratory', 'Applied'
        ]
        
        for batch_num in range(num_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, num_questions)
            current_batch_size = batch_end - batch_start
            
            # Distribute difficulty levels (30% Easy, 45% Medium, 25% Hard)
            difficulties = []
            for i in range(current_batch_size):
                if i < current_batch_size * 0.3:
                    difficulties.append('Easy')
                elif i < current_batch_size * 0.7:
                    difficulties.append('Medium')
                else:
                    difficulties.append('Hard')
            random.shuffle(difficulties)
            
            # Distribute question types
            types = random.choices(question_types, k=current_batch_size)
            
            messages = [
                {
                    "role": "user",
                    "content": f"""Based on the following domain report, generate {current_batch_size} high-quality deep research questions:

**Topic Information**:
- Topic ID: {topic_id}
- Topic Type: {topic_data['type']}
- Primary Domain: {domain_info.get('primary_domain', 'Unknown')}
- Key Themes: {', '.join(domain_info.get('key_themes', []))}

**Domain Report**:
{domain_report[:2000]}...

**Question Generation Requirements**:
Generate {current_batch_size} research questions with the following specifications:

**Difficulty Distribution**:
{dict(zip(range(current_batch_size), difficulties))}

**Question Type Distribution**:
{dict(zip(range(current_batch_size), types))}

**Quality Criteria**:
- **Deep Research Focus**: Questions should require substantial research and analysis
- **Domain Specificity**: Questions should be specific to the identified domain
- **Research Value**: Questions should address meaningful research gaps or challenges
- **Complexity Matching**: Questions should match their assigned difficulty level
- **Clarity**: Questions should be clear and well-formulated

**Difficulty Guidelines**:
- **Easy**: Fundamental concepts, basic comparisons, straightforward analysis
- **Medium**: Multi-factor analysis, moderate synthesis, comparative evaluation
- **Hard**: Complex system thinking, comprehensive frameworks, novel approaches

**Question Type Guidelines**:
- **Analytical**: Break down complex topics into components
- **Comparative**: Compare different approaches, methods, or systems
- **Evaluative**: Assess effectiveness, impact, or value
- **Synthetic**: Combine multiple concepts or create new frameworks
- **Predictive**: Forecast trends, outcomes, or developments
- **Critical**: Challenge assumptions or evaluate limitations
- **Exploratory**: Investigate new areas or emerging topics
- **Applied**: Focus on practical implementation or real-world application

**Output Format**:
Format as JSON array:
[
  {{
    "question_id": "Q{batch_start+1:03d}",
    "question_text": "question text here",
    "difficulty": "difficulty level",
    "question_type": "question type",
    "rationale": "brief explanation of research value"
  }},
  ...
]"""
                }
            ]
            
            response = self.call_claude_api(messages, max_tokens=2000)
            
            if response:
                try:
                    json_match = re.search(r'\[.*\]', response, re.DOTALL)
                    if json_match:
                        batch_questions = json.loads(json_match.group())
                        # Fix question IDs to be sequential across batches
                        for i, question in enumerate(batch_questions):
                            question['question_id'] = f'Q{len(questions)+i+1:03d}'
                        questions.extend(batch_questions)
                except json.JSONDecodeError:
                    # Fallback: create questions manually
                    for i in range(current_batch_size):
                        questions.append({
                            'question_id': f'Q{len(questions)+1:03d}',
                            'question_text': f"What are the key research challenges in {domain_info.get('primary_domain', 'this domain')}?",
                            'difficulty': difficulties[i],
                            'question_type': types[i],
                            'rationale': 'Generated research question for domain analysis'
                        })
            
            # Rate limiting
            time.sleep(2)
        
        return questions[:num_questions]
    
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
        domain_report = self.generate_domain_report(topic_id, topic_data, documents, domain_info)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # PROMPT Phase 3: Generate research questions
        print("❓ Generating research questions...")
        questions = self.generate_research_questions(topic_id, topic_data, domain_report, domain_info, num_questions)
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
                'api_model': 'claude-sonnet-4-20250514',
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
                'api_model': 'claude-sonnet-4-20250514',
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
    clueweb_data_dir = "task_file/clueweb22_query_results"
    claude_api_key = "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"
    
    try:
        # Initialize generator
        generator = ClueWeb22SimplifiedGenerator(clueweb_data_dir, claude_api_key)
        
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