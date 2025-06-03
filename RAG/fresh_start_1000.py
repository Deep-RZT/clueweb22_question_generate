#!/usr/bin/env python3
"""
Fresh Start: Collect 1000 Energy Papers for FastText Training
Complete pipeline from scratch to get 1000 full-text energy papers
"""

import json
import os
import time
import glob
from typing import List, Dict
from crawlers.arxiv_crawler import ArxivCrawler
from crawlers.openalex_crawler import OpenAlexCrawler
from crawlers.crossref_crawler import CrossRefCrawler
from pdf_text_extractor import PDFTextExtractor
from utils.logger import setup_logger
from config import ENERGY_KEYWORDS, OUTPUT_DIRS

class FreshStart1000:
    """
    Fresh start to collect exactly 1000 energy papers with full text
    """
    
    def __init__(self):
        self.logger = setup_logger("fresh_start_1000")
        self.arxiv_crawler = ArxivCrawler()
        self.openalex_crawler = OpenAlexCrawler()
        self.crossref_crawler = CrossRefCrawler()
        self.text_extractor = PDFTextExtractor()
        
        self.all_papers = []
        self.downloaded_pdfs = []
        self.extracted_texts = {}
    
    def load_existing_papers(self):
        """
        加载已有的论文数据（如果存在）
        """
        metadata_files = glob.glob(os.path.join(OUTPUT_DIRS['metadata'], 'papers_*.json'))
        if metadata_files:
            # 找到最新的文件
            latest_file = max(metadata_files, key=os.path.getctime)
            self.logger.info(f"📂 Loading existing papers from: {latest_file}")
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    self.all_papers = json.load(f)
                self.logger.info(f"✅ Loaded {len(self.all_papers)} existing papers")
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to load existing papers: {e}")
                return False
        return False
    
    def save_papers_checkpoint(self):
        """
        保存论文数据检查点
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        checkpoint_path = os.path.join(OUTPUT_DIRS['metadata'], f'papers_{timestamp}.json')
        
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(self.all_papers, f, indent=2, ensure_ascii=False)
            self.logger.info(f"💾 Saved checkpoint: {len(self.all_papers)} papers to {checkpoint_path}")
            return checkpoint_path
        except Exception as e:
            self.logger.error(f"❌ Failed to save checkpoint: {e}")
            return None
    
    def get_already_downloaded_files(self):
        """
        获取已下载的文件列表
        """
        pdf_files = glob.glob(os.path.join(OUTPUT_DIRS['raw_papers'], '*.pdf'))
        downloaded_ids = set()
        
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file)
            # 提取论文ID
            if filename.startswith('arxiv_'):
                paper_id = filename.split('_')[1]
                downloaded_ids.add(paper_id)
        
        self.logger.info(f"📁 Found {len(downloaded_ids)} already downloaded papers")
        return downloaded_ids
    
    def collect_1000_papers(self):
        """
        收集1000篇论文元数据
        """
        # 先尝试加载已有数据
        if self.load_existing_papers():
            if len(self.all_papers) >= 1000:
                self.logger.info(f"✅ Already have {len(self.all_papers)} papers, skipping collection")
                return
            else:
                self.logger.info(f"📊 Have {len(self.all_papers)} papers, need {1000 - len(self.all_papers)} more")
        
        self.logger.info("🎯 Target: Collect 1000 energy papers")
        self.logger.info(f"📋 Using {len(ENERGY_KEYWORDS)} keywords")
        
        target_papers = 1000
        papers_per_keyword = max(15, target_papers // len(ENERGY_KEYWORDS))
        
        for i, keyword in enumerate(ENERGY_KEYWORDS, 1):
            if len(self.all_papers) >= target_papers:
                break
                
            self.logger.info(f"🔍 Keyword {i}/{len(ENERGY_KEYWORDS)}: '{keyword}'")
            
            # arXiv - 主要来源
            try:
                arxiv_papers = self.arxiv_crawler.search_papers([keyword])
                if arxiv_papers:
                    # 取前papers_per_keyword篇
                    new_papers = arxiv_papers[:papers_per_keyword]
                    self.all_papers.extend(new_papers)
                    self.logger.info(f"  ✅ arXiv: +{len(new_papers)} papers (total: {len(self.all_papers)})")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"  ❌ arXiv failed: {e}")
            
            # OpenAlex - 补充来源
            if len(self.all_papers) < target_papers:
                try:
                    openalex_papers = self.openalex_crawler.search_papers([keyword])
                    if openalex_papers:
                        needed = target_papers - len(self.all_papers)
                        new_papers = openalex_papers[:min(10, needed)]
                        self.all_papers.extend(new_papers)
                        self.logger.info(f"  ✅ OpenAlex: +{len(new_papers)} papers (total: {len(self.all_papers)})")
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"  ❌ OpenAlex failed: {e}")
            
            # 每10个关键词保存一次检查点
            if i % 10 == 0:
                self.save_papers_checkpoint()
                self.logger.info(f"📊 Progress: {i}/{len(ENERGY_KEYWORDS)} keywords, {len(self.all_papers)} papers collected")
        
        # 去重
        self.deduplicate_papers()
        
        # 如果不够1000篇，继续收集
        if len(self.all_papers) < target_papers:
            self.logger.warning(f"Only collected {len(self.all_papers)} papers, need {target_papers}")
            self.collect_more_papers(target_papers - len(self.all_papers))
        
        # 保存最终结果
        self.save_papers_checkpoint()
        self.logger.info(f"✅ Collection complete: {len(self.all_papers)} papers")
    
    def collect_more_papers(self, needed):
        """
        如果不够1000篇，继续收集
        """
        self.logger.info(f"🔄 Collecting {needed} more papers...")
        
        # 使用更多关键词组合
        additional_keywords = [
            "renewable energy systems", "smart energy", "energy efficiency",
            "clean energy", "energy management", "power generation",
            "energy optimization", "sustainable power", "green energy",
            "energy networks", "power systems analysis", "energy modeling"
        ]
        
        for keyword in additional_keywords:
            if len(self.all_papers) >= 1000:
                break
                
            try:
                papers = self.arxiv_crawler.search_papers([keyword])
                if papers:
                    new_papers = papers[:min(20, needed)]
                    self.all_papers.extend(new_papers)
                    needed -= len(new_papers)
                    self.logger.info(f"  ✅ '{keyword}': +{len(new_papers)} papers")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"  ❌ '{keyword}' failed: {e}")
    
    def download_1000_pdfs(self, resume_from=0):
        """
        下载1000篇PDF，支持断点续传
        """
        self.logger.info(f"📥 Starting PDF downloads for {len(self.all_papers)} papers")
        
        # 获取已下载的文件
        already_downloaded = self.get_already_downloaded_files()
        
        # 优先下载arXiv论文（最容易成功）
        arxiv_papers = [p for p in self.all_papers if p.get('source') == 'arxiv']
        other_papers = [p for p in self.all_papers if p.get('source') != 'arxiv']
        
        # 按优先级排序
        papers_to_download = arxiv_papers + other_papers
        
        downloaded_count = len(already_downloaded)
        target_downloads = min(1000, len(papers_to_download))
        
        # 从指定位置开始下载
        start_index = max(resume_from, downloaded_count)
        self.logger.info(f"📍 Resuming from paper {start_index + 1}/{target_downloads}")
        
        for i, paper in enumerate(papers_to_download[start_index:target_downloads], start_index):
            # 检查是否已下载
            paper_id = paper.get('id', '').replace('/', '_')
            if paper_id in already_downloaded:
                self.logger.info(f"⏭️  Skipping {i+1}/{target_downloads}: Already downloaded")
                continue
            
            self.logger.info(f"📥 Downloading {i+1}/{target_downloads}: {paper['title'][:50]}...")
            
            try:
                if paper.get('source') == 'arxiv':
                    filepath = self.arxiv_crawler.download_paper(paper)
                else:
                    # 其他来源的下载逻辑
                    filepath = None
                
                if filepath and os.path.exists(filepath):
                    self.downloaded_pdfs.append(filepath)
                    downloaded_count += 1
                    self.logger.info(f"  ✅ Downloaded: {os.path.basename(filepath)}")
                    # 成功下载后短延迟
                    time.sleep(2)
                else:
                    self.logger.warning(f"  ❌ Failed to download")
                    # 失败后长延迟，可能是限流
                    time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"  ❌ Error: {e}")
                # 错误后更长延迟
                time.sleep(15)
            
            # 每50篇报告进度
            if (i + 1) % 50 == 0:
                self.logger.info(f"📊 Progress: {downloaded_count}/{i+1} successful downloads")
                
            # 如果连续失败太多，暂停一段时间
            if i > start_index + 20:  # 至少尝试20篇后再检查
                recent_failures = sum(1 for j in range(max(0, i-19), i+1) 
                                    if j < len(papers_to_download) and 
                                    papers_to_download[j].get('id', '').replace('/', '_') not in already_downloaded)
                if recent_failures >= 15:  # 最近20篇中有15篇失败
                    self.logger.warning("🚫 Too many failures, might be rate limited. Pausing for 5 minutes...")
                    time.sleep(300)  # 暂停5分钟
        
        self.logger.info(f"✅ Download complete: {downloaded_count} PDFs downloaded")
        return downloaded_count
    
    def extract_1000_texts(self):
        """
        提取1000篇论文的完整文本
        """
        # 获取所有PDF文件
        pdf_files = glob.glob(os.path.join(OUTPUT_DIRS['raw_papers'], '*.pdf'))
        self.logger.info(f"📄 Extracting text from {len(pdf_files)} PDFs")
        
        successful_extractions = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            self.logger.info(f"📄 Extracting {i}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
            
            try:
                text = self.text_extractor.extract_text_from_pdf(pdf_path)
                
                if text and len(text) > 1000:  # 至少1000字符
                    self.extracted_texts[os.path.basename(pdf_path)] = text
                    successful_extractions += 1
                    self.logger.info(f"  ✅ Extracted {len(text)} characters")
                else:
                    self.logger.warning(f"  ❌ Insufficient text: {len(text) if text else 0} chars")
                    
            except Exception as e:
                self.logger.error(f"  ❌ Extraction failed: {e}")
        
        self.logger.info(f"✅ Text extraction complete: {successful_extractions} successful extractions")
    
    def create_fasttext_dataset(self):
        """
        创建FastText训练数据集
        """
        self.logger.info("📝 Creating FastText dataset...")
        
        # 正样本（能源论文）
        positive_samples = []
        for filename, text in self.extracted_texts.items():
            if text and len(text) > 1000:
                cleaned_text = self.text_extractor.clean_extracted_text(text)
                if len(cleaned_text) > 500:
                    positive_samples.append(f"__label__energy\t{cleaned_text}")
        
        # 负样本（非能源内容）
        negative_samples = self.create_negative_samples(len(positive_samples))
        
        # 合并数据
        all_samples = positive_samples + negative_samples
        
        # 保存训练数据
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        train_path = os.path.join(OUTPUT_DIRS['processed_text'], f'energy_fasttext_1000_{timestamp}.txt')
        
        with open(train_path, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(sample + '\n')
        
        # 保存统计信息
        stats = {
            'total_samples': len(all_samples),
            'positive_samples': len(positive_samples),
            'negative_samples': len(negative_samples),
            'papers_collected': len(self.all_papers),
            'pdfs_downloaded': len(glob.glob(os.path.join(OUTPUT_DIRS['raw_papers'], '*.pdf'))),
            'texts_extracted': len(self.extracted_texts),
            'timestamp': timestamp
        }
        
        stats_path = os.path.join(OUTPUT_DIRS['processed_text'], f'dataset_stats_{timestamp}.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"✅ FastText dataset created: {len(all_samples)} samples")
        self.logger.info(f"  - Positive (energy): {len(positive_samples)}")
        self.logger.info(f"  - Negative (non-energy): {len(negative_samples)}")
        self.logger.info(f"📁 Dataset saved: {train_path}")
        self.logger.info(f"📊 Statistics saved: {stats_path}")
        
        return train_path, stats_path
    
    def create_negative_samples(self, num_samples):
        """
        创建负样本
        """
        negative_texts = [
            "This paper discusses machine learning algorithms for image recognition and computer vision applications in autonomous vehicles and robotics systems.",
            "We present a novel approach to natural language processing using transformer architectures for sentiment analysis and text classification tasks.",
            "The study examines the effects of social media on adolescent behavior and mental health outcomes in digital communication environments.",
            "This research investigates quantum computing algorithms for cryptographic applications and security protocols in distributed systems.",
            "We analyze the impact of climate change on biodiversity in tropical rainforest ecosystems and conservation strategies.",
            "The paper presents advances in robotics and automation for manufacturing and industrial applications using artificial intelligence.",
            "This study explores the relationship between nutrition and cognitive performance in elderly populations and aging research.",
            "We investigate novel materials for biomedical applications including drug delivery and tissue engineering in medical devices.",
            "The research examines financial market dynamics and algorithmic trading strategies in volatile economic conditions.",
            "This paper discusses advances in telecommunications and 5G network infrastructure development for mobile communications.",
            "We present computational methods for protein folding prediction and molecular dynamics simulations in biochemistry.",
            "The study analyzes urban planning strategies for sustainable city development and transportation infrastructure.",
            "This research investigates educational technology and online learning platforms for distance education systems.",
            "We examine psychological factors in human-computer interaction and user experience design for digital interfaces.",
            "The paper presents archaeological findings and historical analysis of ancient civilizations and cultural heritage preservation."
        ]
        
        negative_samples = []
        for i in range(num_samples):
            text = negative_texts[i % len(negative_texts)]
            # 添加一些变化
            if i > 0 and i % len(negative_texts) == 0:
                text = f"Furthermore, {text.lower()}"
            negative_samples.append(f"__label__nonenergy\t{text}")
        
        return negative_samples
    
    def deduplicate_papers(self):
        """
        去重
        """
        unique_papers = []
        seen_titles = set()
        seen_dois = set()
        
        for paper in self.all_papers:
            # 安全处理None值
            title = paper.get('title') if paper.get('title') else ''
            title = title.lower().strip() if title else ''
            
            doi = paper.get('doi') if paper.get('doi') else ''
            doi = doi.lower().strip() if doi else ''
            
            # 检查重复
            if title and title in seen_titles:
                continue
            if doi and doi in seen_dois:
                continue
            
            unique_papers.append(paper)
            if title:
                seen_titles.add(title)
            if doi:
                seen_dois.add(doi)
        
        removed = len(self.all_papers) - len(unique_papers)
        self.logger.info(f"🔄 Removed {removed} duplicates, {len(unique_papers)} unique papers remain")
        self.all_papers = unique_papers
    
    def run_complete_pipeline(self, resume_download_from=0):
        """
        运行完整的1000篇论文收集流程
        """
        print("🚀 FRESH START: Collecting 1000 Energy Papers")
        print("=" * 60)
        print("🎯 Target: 1000 energy papers with full text")
        print(f"📋 Keywords: {len(ENERGY_KEYWORDS)} energy-related terms")
        print("=" * 60)
        
        # Step 1: 收集1000篇论文元数据
        self.collect_1000_papers()
        
        # Step 2: 下载PDF（支持断点续传）
        downloaded_count = self.download_1000_pdfs(resume_from=resume_download_from)
        
        # Step 3: 提取文本
        self.extract_1000_texts()
        
        # Step 4: 创建FastText数据集
        train_path, stats_path = self.create_fasttext_dataset()
        
        print("\n" + "=" * 60)
        print("✅ FRESH START COMPLETED!")
        print(f"📊 Papers collected: {len(self.all_papers)}")
        print(f"📥 PDFs downloaded: {downloaded_count}")
        print(f"📄 Texts extracted: {len(self.extracted_texts)}")
        print(f"📁 FastText dataset: {train_path}")
        print(f"📊 Statistics: {stats_path}")
        print("\n🎯 Ready for FastText training!")
        
        return train_path

def main():
    """
    主函数
    """
    pipeline = FreshStart1000()
    
    # 如果需要从特定位置恢复下载，修改这个数字
    resume_from = 591  # 从第592篇开始（0-based index）
    
    train_path = pipeline.run_complete_pipeline(resume_download_from=resume_from)
    
    print(f"\n📋 Next steps:")
    print(f"1. Train FastText model: fasttext supervised -input {train_path} -output model_energy")
    print(f"2. Test the classifier")
    print(f"3. Apply to ClueWeb22 documents")

if __name__ == "__main__":
    main() 