#!/usr/bin/env python3
"""
PDF Text Extraction Module
Extracts full text content from downloaded PDF files for FastText training
"""

import os
import re
import json
from typing import List, Dict, Optional
import PyPDF2
from utils.logger import setup_logger
from config import OUTPUT_DIRS

class PDFTextExtractor:
    """
    Extract full text from PDF files
    """
    
    def __init__(self):
        self.logger = setup_logger("pdf_extractor")
        
        # Create output directory for extracted text
        self.extracted_text_dir = os.path.join(OUTPUT_DIRS['processed_text'], 'full_text')
        os.makedirs(self.extracted_text_dir, exist_ok=True)
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """
        Extract text using PyPDF2
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            self.logger.warning(f"PyPDF2 failed for {pdf_path}: {e}")
            return ""
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
        
        # Remove very short lines (likely headers/footers)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 10]
        
        # Join back
        text = ' '.join(cleaned_lines)
        
        # Remove excessive spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract and clean text from a PDF file
        """
        self.logger.info(f"Extracting text from: {os.path.basename(pdf_path)}")
        
        # Use PyPDF2
        text = self.extract_text_pypdf2(pdf_path)
        
        # Clean the text
        cleaned_text = self.clean_extracted_text(text)
        
        if len(cleaned_text) < 100:
            self.logger.warning(f"Very short text extracted from {pdf_path}: {len(cleaned_text)} chars")
        
        return cleaned_text
    
    def process_all_pdfs(self, pdf_directory: str = None) -> Dict[str, str]:
        """
        Process all PDF files in the directory
        """
        if pdf_directory is None:
            pdf_directory = OUTPUT_DIRS['raw_papers']
        
        if not os.path.exists(pdf_directory):
            self.logger.error(f"PDF directory not found: {pdf_directory}")
            return {}
        
        # Find all PDF files
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {pdf_directory}")
            return {}
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        extracted_texts = {}
        successful_extractions = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            pdf_path = os.path.join(pdf_directory, pdf_file)
            
            self.logger.info(f"Processing {i}/{len(pdf_files)}: {pdf_file}")
            
            try:
                # Extract text
                text = self.extract_text_from_pdf(pdf_path)
                
                if text and len(text) > 100:
                    extracted_texts[pdf_file] = text
                    successful_extractions += 1
                    
                    # Save individual text file
                    text_filename = pdf_file.replace('.pdf', '.txt')
                    text_path = os.path.join(self.extracted_text_dir, text_filename)
                    
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    self.logger.info(f"Extracted {len(text)} characters from {pdf_file}")
                else:
                    self.logger.warning(f"Failed to extract meaningful text from {pdf_file}")
                
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file}: {e}")
        
        self.logger.info(f"Successfully extracted text from {successful_extractions}/{len(pdf_files)} PDFs")
        
        # Save extraction summary
        summary = {
            'total_pdfs': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': len(pdf_files) - successful_extractions,
            'extracted_files': list(extracted_texts.keys()),
            'average_text_length': sum(len(text) for text in extracted_texts.values()) / len(extracted_texts) if extracted_texts else 0
        }
        
        summary_path = os.path.join(self.extracted_text_dir, 'extraction_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return extracted_texts
    
    def create_fasttext_dataset_from_pdfs(self, extracted_texts: Dict[str, str]) -> List[str]:
        """
        Create FastText training data from extracted PDF texts
        """
        fasttext_lines = []
        
        for pdf_file, text in extracted_texts.items():
            if text and len(text) > 200:  # Ensure minimum text length
                # Clean text for FastText
                cleaned_text = self.clean_extracted_text(text)
                
                # Create FastText format line
                fasttext_line = f"__label__energy\t{cleaned_text}"
                fasttext_lines.append(fasttext_line)
        
        self.logger.info(f"Created {len(fasttext_lines)} FastText training samples from PDFs")
        return fasttext_lines

def main():
    """
    Main function to extract text from all PDFs
    """
    extractor = PDFTextExtractor()
    
    print("🔄 Extracting text from downloaded PDFs...")
    print("=" * 50)
    
    # Process all PDFs
    extracted_texts = extractor.process_all_pdfs()
    
    if extracted_texts:
        # Create FastText training data
        fasttext_lines = extractor.create_fasttext_dataset_from_pdfs(extracted_texts)
        
        # Save FastText format file
        output_path = os.path.join(OUTPUT_DIRS['processed_text'], 'full_text_train.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in fasttext_lines:
                f.write(line + '\n')
        
        print(f"\n✅ Text extraction completed!")
        print(f"📁 Extracted texts saved in: {extractor.extracted_text_dir}")
        print(f"📁 FastText training data: {output_path}")
        print(f"📊 Successfully processed: {len(extracted_texts)} PDFs")
        print(f"📊 Total training samples: {len(fasttext_lines)}")
    else:
        print("❌ No PDFs found or no text extracted")

if __name__ == "__main__":
    main() 