#!/usr/bin/env python3
"""
Process Existing PDFs: Extract text and create FastText dataset
Use the 574 already downloaded PDFs to create training data
"""

import json
import os
import time
import glob
from pdf_text_extractor import PDFTextExtractor
from utils.logger import setup_logger
from config import OUTPUT_DIRS

class ProcessExistingPDFs:
    """
    处理现有PDF文件，创建FastText数据集
    """
    
    def __init__(self):
        self.logger = setup_logger("process_pdfs")
        self.text_extractor = PDFTextExtractor()
        self.extracted_texts = {}
    
    def extract_all_texts(self):
        """
        提取所有PDF的文本
        """
        # 获取所有PDF文件
        pdf_files = glob.glob(os.path.join(OUTPUT_DIRS['raw_papers'], '*.pdf'))
        self.logger.info(f"📄 Found {len(pdf_files)} PDF files to process")
        
        successful_extractions = 0
        failed_extractions = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            filename = os.path.basename(pdf_path)
            self.logger.info(f"📄 Processing {i}/{len(pdf_files)}: {filename}")
            
            try:
                text = self.text_extractor.extract_text_from_pdf(pdf_path)
                
                if text and len(text) > 500:  # 至少500字符
                    # 清理文本
                    cleaned_text = self.text_extractor.clean_extracted_text(text)
                    if len(cleaned_text) > 200:  # 清理后至少200字符
                        self.extracted_texts[filename] = cleaned_text
                        successful_extractions += 1
                        self.logger.info(f"  ✅ Extracted {len(cleaned_text)} characters")
                    else:
                        failed_extractions += 1
                        self.logger.warning(f"  ❌ Text too short after cleaning: {len(cleaned_text)} chars")
                else:
                    failed_extractions += 1
                    self.logger.warning(f"  ❌ Insufficient raw text: {len(text) if text else 0} chars")
                    
            except Exception as e:
                failed_extractions += 1
                self.logger.error(f"  ❌ Extraction failed: {e}")
            
            # 每50个文件报告进度
            if i % 50 == 0:
                self.logger.info(f"📊 Progress: {successful_extractions} successful, {failed_extractions} failed")
        
        self.logger.info(f"✅ Text extraction complete:")
        self.logger.info(f"  - Successful: {successful_extractions}")
        self.logger.info(f"  - Failed: {failed_extractions}")
        self.logger.info(f"  - Success rate: {successful_extractions/(successful_extractions+failed_extractions)*100:.1f}%")
        
        return successful_extractions
    
    def create_negative_samples(self, num_samples):
        """
        创建负样本（非能源内容）
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
            "The paper presents archaeological findings and historical analysis of ancient civilizations and cultural heritage preservation.",
            "This study focuses on marine biology and oceanographic research in deep-sea environments and ecosystem dynamics.",
            "We investigate advanced materials science for aerospace applications and structural engineering in extreme conditions.",
            "The research examines pharmaceutical drug development and clinical trial methodologies for therapeutic interventions.",
            "This paper discusses artificial intelligence applications in healthcare diagnostics and medical imaging analysis.",
            "We present computational fluid dynamics simulations for aerodynamic design and optimization in automotive engineering.",
            "The study analyzes social network theory and community detection algorithms in complex systems research.",
            "This research investigates cognitive neuroscience and brain imaging techniques for understanding neural mechanisms.",
            "We examine environmental monitoring and remote sensing technologies for ecological assessment and conservation.",
            "The paper presents statistical modeling approaches for epidemiological studies and public health research.",
            "This study explores molecular genetics and genomic sequencing technologies for personalized medicine applications."
        ]
        
        negative_samples = []
        for i in range(num_samples):
            text = negative_texts[i % len(negative_texts)]
            # 添加一些变化
            if i > 0 and i % len(negative_texts) == 0:
                text = f"Furthermore, {text.lower()}"
            elif i > 0 and i % (len(negative_texts) // 2) == 0:
                text = f"Additionally, {text}"
            negative_samples.append(f"__label__nonenergy\t{text}")
        
        return negative_samples
    
    def create_fasttext_dataset(self):
        """
        创建FastText训练数据集
        """
        self.logger.info("📝 Creating FastText dataset...")
        
        if not self.extracted_texts:
            self.logger.error("❌ No extracted texts available!")
            return None, None
        
        # 正样本（能源论文）
        positive_samples = []
        for filename, text in self.extracted_texts.items():
            # 截取前1000个词，避免文本过长
            words = text.split()
            if len(words) > 1000:
                text = ' '.join(words[:1000])
            positive_samples.append(f"__label__energy\t{text}")
        
        # 负样本（非能源内容）
        negative_samples = self.create_negative_samples(len(positive_samples))
        
        # 合并数据
        all_samples = positive_samples + negative_samples
        
        # 随机打乱
        import random
        random.shuffle(all_samples)
        
        # 分割训练集和验证集 (80/20)
        split_idx = int(len(all_samples) * 0.8)
        train_samples = all_samples[:split_idx]
        val_samples = all_samples[split_idx:]
        
        # 保存训练数据
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        train_path = os.path.join(OUTPUT_DIRS['processed_text'], f'energy_train_{timestamp}.txt')
        val_path = os.path.join(OUTPUT_DIRS['processed_text'], f'energy_val_{timestamp}.txt')
        
        with open(train_path, 'w', encoding='utf-8') as f:
            for sample in train_samples:
                f.write(sample + '\n')
        
        with open(val_path, 'w', encoding='utf-8') as f:
            for sample in val_samples:
                f.write(sample + '\n')
        
        # 保存统计信息
        stats = {
            'total_samples': len(all_samples),
            'train_samples': len(train_samples),
            'val_samples': len(val_samples),
            'positive_samples': len(positive_samples),
            'negative_samples': len(negative_samples),
            'pdfs_processed': len(self.extracted_texts),
            'avg_text_length': sum(len(text.split()) for text in self.extracted_texts.values()) / len(self.extracted_texts),
            'timestamp': timestamp
        }
        
        stats_path = os.path.join(OUTPUT_DIRS['processed_text'], f'dataset_stats_{timestamp}.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"✅ FastText dataset created:")
        self.logger.info(f"  - Total samples: {len(all_samples)}")
        self.logger.info(f"  - Training samples: {len(train_samples)}")
        self.logger.info(f"  - Validation samples: {len(val_samples)}")
        self.logger.info(f"  - Positive (energy): {len(positive_samples)}")
        self.logger.info(f"  - Negative (non-energy): {len(negative_samples)}")
        self.logger.info(f"  - Avg text length: {stats['avg_text_length']:.1f} words")
        self.logger.info(f"📁 Training data: {train_path}")
        self.logger.info(f"📁 Validation data: {val_path}")
        self.logger.info(f"📊 Statistics: {stats_path}")
        
        return train_path, val_path, stats_path
    
    def run_complete_process(self):
        """
        运行完整的处理流程
        """
        print("🚀 PROCESSING EXISTING PDFs")
        print("=" * 60)
        print("📄 Extracting text from downloaded PDFs")
        print("📝 Creating FastText training dataset")
        print("=" * 60)
        
        # Step 1: 提取所有PDF文本
        successful_extractions = self.extract_all_texts()
        
        if successful_extractions == 0:
            print("❌ No texts extracted successfully!")
            return None
        
        # Step 2: 创建FastText数据集
        train_path, val_path, stats_path = self.create_fasttext_dataset()
        
        print("\n" + "=" * 60)
        print("✅ PROCESSING COMPLETED!")
        print(f"📄 Texts extracted: {successful_extractions}")
        print(f"📁 Training data: {train_path}")
        print(f"📁 Validation data: {val_path}")
        print(f"📊 Statistics: {stats_path}")
        print("\n🎯 Ready for FastText training!")
        
        return train_path, val_path

def main():
    """
    主函数
    """
    processor = ProcessExistingPDFs()
    result = processor.run_complete_process()
    
    if result:
        train_path, val_path = result
        print(f"\n📋 Next steps:")
        print(f"1. Train FastText model:")
        print(f"   fasttext supervised -input {train_path} -output models/energy_classifier -epoch 10 -lr 0.5 -wordNgrams 2 -dim 100")
        print(f"2. Test on validation set:")
        print(f"   fasttext test models/energy_classifier.bin {val_path}")
        print(f"3. Apply to ClueWeb22 documents")

if __name__ == "__main__":
    main() 