#!/usr/bin/env python3
"""
ClueWeb22 PROMPT+RAG Generator
Applies energy domain PROMPT+RAG design to ClueWeb22 topics
Generates domain reports and literature-grounded QA pairs
"""

import os
import json
import re
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import requests
import pandas as pd

class ClueWeb22PromptRAGGenerator:
    """
    PROMPT+RAG system for ClueWeb22 topics
    Combines document summarization with literature-grounded QA generation
    """
    
    def __init__(self, data_dir: str, claude_api_key: str):
        """
        Initialize the generator
        
        Args:
            data_dir: Path to ClueWeb22 query results directory
            claude_api_key: Claude API key for generation
        """
        self.data_dir = Path(data_dir)
        self.claude_api_key = claude_api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Output directory
        self.output_dir = Path("clueweb22_prompt_rag_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Topic extraction and organization
        self.topics = self.extract_topics()
        print(f"✅ Identified {len(self.topics)} unique topics")
        
        # Load energy RAG corpus for answer generation
        self.rag_corpus = self.load_energy_rag_corpus()
        print(f"✅ Loaded energy RAG corpus with {len(self.rag_corpus)} papers")
        
    def extract_topics(self) -> Dict[str, List[Path]]:
        """Extract and organize topics from ClueWeb22 files"""
        topics = defaultdict(list)
        
        txt_files = list(self.data_dir.glob("*.txt"))
        
        for file_path in txt_files:
            filename = file_path.name
            match = re.match(r'(clueweb22-[^_]+(?:-[^_]+)*(?:-[^_]+)*(?:-[^_]+)*)_top\d+\.txt', filename)
            if match:
                topic_id = match.group(1)
                topics[topic_id].append(file_path)
        
        # Sort files by top number for each topic
        for topic_id in topics:
            topics[topic_id].sort(key=lambda x: int(re.search(r'_top(\d+)\.txt', x.name).group(1)))
        
        return dict(topics)
    
    def load_energy_rag_corpus(self) -> List[Dict]:
        """Load energy literature corpus for RAG"""
        possible_files = [
            "RAG/data/metadata/papers_20250526_182607.json",
            "RAG/data/processed/energy_rag_corpus.json"
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                print(f"📚 Loading energy RAG corpus: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    papers = json.load(f)
                
                corpus = []
                for paper in papers:
                    if isinstance(paper, dict):
                        title = paper.get('title', '')
                        abstract = paper.get('abstract', '')
                        
                        if title and abstract and len(abstract) > 50:
                            corpus.append({
                                'id': paper.get('id', ''),
                                'title': title,
                                'abstract': abstract,
                                'authors': paper.get('authors', []),
                                'source': paper.get('source', ''),
                                'full_text': f"{title} {abstract}"
                            })
                return corpus
        
        print("⚠️ Energy RAG corpus not found, using fallback")
        return []
    
    def call_claude_api(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        """Call Claude API with error handling"""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
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
    
    def load_topic_documents(self, topic_id: str, max_docs: int = 100) -> List[Dict[str, str]]:
        """Load and process documents for a specific topic"""
        documents = []
        file_paths = self.topics.get(topic_id, [])[:max_docs]
        
        for i, file_path in enumerate(file_paths):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                
                if content and len(content) > 50:
                    documents.append({
                        'doc_id': f"{topic_id}_doc_{i:03d}",
                        'file_name': file_path.name,
                        'content': content,
                        'word_count': len(content.split()),
                        'char_count': len(content)
                    })
            except Exception as e:
                print(f"⚠️ Error loading {file_path}: {e}")
                continue
        
        return documents
    
    def identify_topic_domain(self, topic_id: str, sample_docs: List[Dict]) -> Dict[str, Any]:
        """Identify domain characteristics using PROMPT approach"""
        sample_content = []
        for doc in sample_docs[:5]:
            content_preview = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
            sample_content.append(f"Document {doc['doc_id']}:\n{content_preview}\n")
        
        combined_sample = "\n".join(sample_content)
        
        messages = [
            {
                "role": "user",
                "content": f"""Analyze the following document collection and identify its domain characteristics:

**Topic ID**: {topic_id}
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
        
        # Fallback analysis
        return {
            "primary_domain": "General",
            "key_themes": ["Mixed Topics"],
            "content_type": "Web Content",
            "language": "en" if "en" in topic_id else "ja",
            "scope": "medium",
            "research_potential": "General research questions",
            "domain_keywords": [],
            "complexity_level": "intermediate"
        }
    
    def generate_domain_report_prompt(self, topic_id: str, documents: List[Dict], domain_info: Dict) -> str:
        """Generate domain report using PROMPT approach"""
        doc_summaries = []
        total_words = sum(doc['word_count'] for doc in documents)
        
        for i, doc in enumerate(documents[:20]):  # Use first 20 docs for report
            summary = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
            doc_summaries.append(f"Doc {i+1}: {summary}")
        
        combined_summaries = "\n\n".join(doc_summaries)
        
        messages = [
            {
                "role": "user",
                "content": f"""Generate a comprehensive expert-level domain report based on the following document collection:

**Topic Information**:
- Topic ID: {topic_id}
- Primary Domain: {domain_info.get('primary_domain', 'Unknown')}
- Key Themes: {', '.join(domain_info.get('key_themes', []))}
- Total Documents: {len(documents)}
- Total Words: {total_words:,}
- Content Type: {domain_info.get('content_type', 'Unknown')}
- Complexity Level: {domain_info.get('complexity_level', 'Unknown')}

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
This report analyzes {len(documents)} documents from the {topic_id} topic collection, covering {domain_info.get('primary_domain', 'various topics')}. The collection represents {domain_info.get('content_type', 'web content')} with a focus on {', '.join(domain_info.get('key_themes', ['general topics']))}.

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
    
    def generate_research_questions_prompt(self, topic_id: str, domain_report: str, domain_info: Dict, num_questions: int = 50) -> List[Dict]:
        """Generate research questions using PROMPT approach"""
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

**Domain Information**:
- Topic: {topic_id}
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
    
    def retrieve_relevant_papers_rag(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant papers using RAG approach"""
        if not self.rag_corpus:
            return []
        
        scores = []
        query_words = set(query.lower().split())
        
        for paper in self.rag_corpus:
            title_words = set(paper['title'].lower().split())
            abstract_words = set(paper['abstract'].lower().split())
            
            # Calculate similarity scores
            title_sim = len(query_words.intersection(title_words)) / len(query_words.union(title_words)) if query_words.union(title_words) else 0
            abstract_sim = len(query_words.intersection(abstract_words)) / len(query_words.union(abstract_words)) if query_words.union(abstract_words) else 0
            
            # Combined score with higher weight for title
            combined_score = title_sim * 0.6 + abstract_sim * 0.4
            
            if combined_score > 0.05:  # Minimum threshold
                scores.append((combined_score, paper))
        
        # Sort and return top papers
        scores.sort(key=lambda x: x[0], reverse=True)
        return [paper for score, paper in scores[:top_k]]
    
    def generate_rag_answer(self, question: str, relevant_papers: List[Dict], domain_info: Dict) -> Dict[str, Any]:
        """Generate answer using RAG approach with energy literature"""
        
        if not relevant_papers:
            # Fallback answer without literature
            return {
                'answer': f"This question about {domain_info.get('primary_domain', 'the domain')} requires comprehensive analysis. While specific literature may not be directly available, this represents an important research direction that could benefit from interdisciplinary approaches and empirical investigation.",
                'sources': [],
                'confidence': 0.3,
                'method': 'no_literature'
            }
        
        # Prepare literature context
        literature_context = []
        sources = []
        
        for i, paper in enumerate(relevant_papers, 1):
            context_entry = f"""
Paper {i}: {paper['title']}
Authors: {', '.join(paper.get('authors', [])[:3])}
Abstract: {paper['abstract'][:500]}...
"""
            literature_context.append(context_entry)
            
            sources.append({
                'title': paper['title'],
                'authors': paper.get('authors', []),
                'source': paper.get('source', ''),
                'id': paper.get('id', '')
            })
        
        # Generate RAG-fused answer
        messages = [
            {
                "role": "user",
                "content": f"""You are an expert researcher. Based on the following research literature, provide a comprehensive answer to the question.

**Question**: {question}
**Domain Context**: {domain_info.get('primary_domain', 'Unknown')}

**Relevant Literature**:
{''.join(literature_context)}

**Instructions**:
1. Synthesize information from the provided literature
2. Provide a structured, research-grade answer
3. Cite specific findings from the papers when relevant
4. Connect the literature to the question domain
5. Identify research gaps or areas needing further investigation

**Answer Structure**:
- **Overview**: Brief summary of the topic
- **Literature Insights**: Key findings from the papers (cite papers)
- **Domain Analysis**: How this applies to the question domain
- **Research Implications**: Future research directions
- **Conclusion**: Summary and key takeaways

Provide a comprehensive answer (800-1200 words) that demonstrates deep understanding while staying grounded in the literature."""
            }
        ]
        
        answer_text = self.call_claude_api(messages, max_tokens=2000)
        
        if answer_text:
            return {
                'answer': answer_text,
                'sources': sources,
                'confidence': min(len(relevant_papers) / 5.0, 1.0),
                'method': 'rag_literature',
                'literature_count': len(relevant_papers)
            }
        else:
            # Fallback to literature summary
            key_findings = []
            for paper in relevant_papers:
                sentences = paper['abstract'].split('.')
                for sentence in sentences[:2]:
                    if any(word in sentence.lower() for word in question.lower().split()):
                        key_findings.append(sentence.strip())
            
            fallback_answer = "Based on relevant research literature: " + " ".join(key_findings[:3])
            
            return {
                'answer': fallback_answer,
                'sources': sources,
                'confidence': 0.6,
                'method': 'literature_summary',
                'literature_count': len(relevant_papers)
            }
    
    def process_single_topic(self, topic_id: str) -> Dict[str, Any]:
        """Process a single topic: PROMPT for report/questions + RAG for answers"""
        print(f"\n🔍 Processing Topic: {topic_id}")
        print("=" * 60)
        
        # Load documents
        print("📚 Loading documents...")
        documents = self.load_topic_documents(topic_id, max_docs=100)
        print(f"   Loaded {len(documents)} documents")
        
        if not documents:
            print("❌ No valid documents found for this topic")
            return None
        
        # Adjust question count based on document availability
        if len(documents) < 20:
            num_questions = 25  # Reduce questions for topics with fewer documents
            print(f"   ⚠️ Limited documents ({len(documents)}), reducing questions to {num_questions}")
        else:
            num_questions = 50
        
        # PROMPT Phase 1: Identify domain
        print("🔬 Analyzing domain characteristics (PROMPT)...")
        domain_info = self.identify_topic_domain(topic_id, documents[:min(10, len(documents))])
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Themes: {', '.join(domain_info.get('key_themes', []))}")
        
        # PROMPT Phase 2: Generate domain report
        print("📝 Generating domain report (PROMPT)...")
        domain_report = self.generate_domain_report_prompt(topic_id, documents, domain_info)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # PROMPT Phase 3: Generate research questions
        print("❓ Generating research questions (PROMPT)...")
        questions = self.generate_research_questions_prompt(topic_id, domain_report, domain_info, num_questions=num_questions)
        print(f"   Generated {len(questions)} questions")
        
        # RAG Phase: Generate answers using energy literature
        print("💡 Generating answers using energy literature (RAG)...")
        qa_pairs = []
        
        for i, question in enumerate(questions):
            print(f"  Generating answer {i+1}/{len(questions)}: {question['question_text'][:60]}...")
            
            # Retrieve relevant papers
            relevant_papers = self.retrieve_relevant_papers_rag(question['question_text'], top_k=5)
            
            # Generate RAG answer
            rag_result = self.generate_rag_answer(question['question_text'], relevant_papers, domain_info)
            
            qa_pair = {
                **question,
                'answer': rag_result['answer'],
                'answer_method': rag_result['method'],
                'literature_sources': rag_result['sources'],
                'rag_confidence': rag_result['confidence'],
                'literature_count': rag_result.get('literature_count', 0),
                'domain': domain_info.get('primary_domain', 'Unknown'),
                'themes': domain_info.get('key_themes', []),
                'generation_timestamp': datetime.now().isoformat()
            }
            
            qa_pairs.append(qa_pair)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"   Generated {len(qa_pairs)} QA pairs")
        
        # Compile results
        results = {
            'topic_id': topic_id,
            'domain_info': domain_info,
            'document_stats': {
                'total_documents': len(documents),
                'total_words': sum(doc['word_count'] for doc in documents),
                'avg_doc_length': sum(doc['word_count'] for doc in documents) / len(documents)
            },
            'domain_report': domain_report,
            'qa_pairs': qa_pairs,
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'api_model': 'claude-3-5-sonnet-20241022',
                'prompt_method': 'domain_report_and_questions',
                'rag_method': 'energy_literature_grounded',
                'num_questions_requested': num_questions,
                'num_questions_generated': len(qa_pairs)
            }
        }
        
        print(f"✅ Topic {topic_id} processing completed")
        return results
    
    def process_all_topics(self) -> Dict[str, Any]:
        """Process all topics using PROMPT+RAG approach"""
        print("🚀 Starting ClueWeb22 PROMPT+RAG Generation")
        print("=" * 70)
        print(f"Topics to process: {len(self.topics)}")
        print(f"Topics: {list(self.topics.keys())}")
        print("=" * 70)
        
        all_results = {}
        failed_topics = []
        
        for i, topic_id in enumerate(self.topics.keys(), 1):
            print(f"\n📊 Progress: {i}/{len(self.topics)}")
            
            try:
                topic_results = self.process_single_topic(topic_id)
                if topic_results:
                    all_results[topic_id] = topic_results
                    
                    # Save individual topic results
                    topic_file = self.output_dir / f"{topic_id}_prompt_rag_results.json"
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
                'total_topics': len(self.topics),
                'successful_topics': len(all_results),
                'failed_topics': failed_topics,
                'api_model': 'claude-3-5-sonnet-20241022',
                'methodology': 'PROMPT+RAG',
                'prompt_phase': 'domain_report_and_question_generation',
                'rag_phase': 'energy_literature_grounded_answers'
            },
            'summary_statistics': summary_stats,
            'topic_results': all_results
        }
        
        print(f"\n✅ Processing completed!")
        print(f"   Successful: {len(all_results)}/{len(self.topics)} topics")
        print(f"   Failed: {len(failed_topics)} topics")
        if failed_topics:
            print(f"   Failed topics: {', '.join(failed_topics)}")
        
        return final_results
    
    def generate_summary_statistics(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics"""
        if not all_results:
            return {}
        
        total_documents = sum(r['document_stats']['total_documents'] for r in all_results.values())
        total_words = sum(r['document_stats']['total_words'] for r in all_results.values())
        total_qa_pairs = sum(len(r['qa_pairs']) for r in all_results.values())
        
        # Domain distribution
        domains = [r['domain_info'].get('primary_domain', 'Unknown') for r in all_results.values()]
        domain_counts = {domain: domains.count(domain) for domain in set(domains)}
        
        # Difficulty distribution
        all_difficulties = []
        for result in all_results.values():
            all_difficulties.extend([qa['difficulty'] for qa in result['qa_pairs']])
        difficulty_counts = {diff: all_difficulties.count(diff) for diff in set(all_difficulties)}
        
        # Question type distribution
        all_types = []
        for result in all_results.values():
            all_types.extend([qa['question_type'] for qa in result['qa_pairs']])
        type_counts = {qtype: all_types.count(qtype) for qtype in set(all_types)}
        
        # RAG performance
        all_methods = []
        all_confidences = []
        all_literature_counts = []
        for result in all_results.values():
            for qa in result['qa_pairs']:
                all_methods.append(qa.get('answer_method', 'unknown'))
                all_confidences.append(qa.get('rag_confidence', 0.0))
                all_literature_counts.append(qa.get('literature_count', 0))
        
        method_counts = {method: all_methods.count(method) for method in set(all_methods)}
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        avg_literature_count = sum(all_literature_counts) / len(all_literature_counts) if all_literature_counts else 0
        
        return {
            'total_topics_processed': len(all_results),
            'total_documents_analyzed': total_documents,
            'total_words_processed': total_words,
            'total_qa_pairs_generated': total_qa_pairs,
            'average_qa_pairs_per_topic': total_qa_pairs / len(all_results),
            'domain_distribution': domain_counts,
            'difficulty_distribution': difficulty_counts,
            'question_type_distribution': type_counts,
            'rag_performance': {
                'answer_methods': method_counts,
                'average_confidence': avg_confidence,
                'average_literature_count': avg_literature_count,
                'literature_coverage': sum(1 for c in all_literature_counts if c > 0) / len(all_literature_counts) * 100 if all_literature_counts else 0
            },
            'average_documents_per_topic': total_documents / len(all_results),
            'average_words_per_topic': total_words / len(all_results)
        }
    
    def save_results(self, results: Dict[str, Any]) -> Tuple[str, str]:
        """Save results in JSON and Excel formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete results as JSON
        json_file = self.output_dir / f"clueweb22_prompt_rag_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate Excel format
        excel_file = self.output_dir / f"clueweb22_prompt_rag_results_{timestamp}.xlsx"
        
        try:
            excel_data = []
            for topic_id, topic_data in results.get('topic_results', {}).items():
                # Topic summary row
                topic_summary = {
                    'Topic_ID': topic_id,
                    'Type': 'TOPIC_SUMMARY',
                    'Domain': topic_data['domain_info'].get('primary_domain', 'Unknown'),
                    'Documents': topic_data['document_stats']['total_documents'],
                    'Total_Words': topic_data['document_stats']['total_words'],
                    'Key_Themes': ', '.join(topic_data['domain_info'].get('key_themes', [])),
                    'Report_Words': len(topic_data['domain_report'].split()),
                    'QA_Pairs': len(topic_data['qa_pairs']),
                    'Content': topic_data['domain_report'][:500] + "..." if len(topic_data['domain_report']) > 500 else topic_data['domain_report']
                }
                excel_data.append(topic_summary)
                
                # QA pairs
                for qa in topic_data['qa_pairs']:
                    qa_row = {
                        'Topic_ID': topic_id,
                        'Type': 'QA_PAIR',
                        'Question_ID': qa['question_id'],
                        'Question': qa['question_text'],
                        'Difficulty': qa['difficulty'],
                        'Question_Type': qa['question_type'],
                        'Answer': qa['answer'],
                        'Answer_Method': qa.get('answer_method', 'unknown'),
                        'RAG_Confidence': f"{qa.get('rag_confidence', 0):.3f}",
                        'Literature_Count': qa.get('literature_count', 0),
                        'Literature_Sources': '; '.join([src['title'] for src in qa.get('literature_sources', [])[:3]])
                    }
                    excel_data.append(qa_row)
            
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
    print("🌐 ClueWeb22 PROMPT+RAG Generation System")
    print("=" * 70)
    print("Applies energy domain PROMPT+RAG design to ClueWeb22 topics")
    print("PROMPT: Domain reports and question generation")
    print("RAG: Literature-grounded answer generation")
    print("=" * 70)
    
    # Configuration
    data_dir = "task_file/clueweb22_query_results"
    claude_api_key = "xxxxx"
    
    try:
        # Initialize generator
        generator = ClueWeb22PromptRAGGenerator(data_dir, claude_api_key)
        
        # Process all topics
        results = generator.process_all_topics()
        
        # Save results
        json_file, excel_file = generator.save_results(results)
        
        print(f"\n🎉 ClueWeb22 PROMPT+RAG Generation Completed!")
        print(f"📊 Generated {results['summary_statistics'].get('total_qa_pairs_generated', 0)} QA pairs")
        print(f"📁 JSON results: {json_file}")
        if excel_file:
            print(f"📊 Excel results: {excel_file}")
        
        # Print summary statistics
        stats = results.get('summary_statistics', {})
        print(f"\n📈 Summary Statistics:")
        print(f"   Topics processed: {stats.get('total_topics_processed', 0)}")
        print(f"   Documents analyzed: {stats.get('total_documents_analyzed', 0):,}")
        print(f"   Average QA pairs per topic: {stats.get('average_qa_pairs_per_topic', 0):.1f}")
        
        rag_perf = stats.get('rag_performance', {})
        print(f"   RAG literature coverage: {rag_perf.get('literature_coverage', 0):.1f}%")
        print(f"   Average RAG confidence: {rag_perf.get('average_confidence', 0):.3f}")
        
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 