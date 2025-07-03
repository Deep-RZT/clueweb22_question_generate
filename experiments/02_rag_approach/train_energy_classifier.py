#!/usr/bin/env python3
"""
Train Energy Classifier using FastText
Use the processed PDF data to train the classifier
"""

import fasttext
import os
import json
import time
from utils.logger import setup_logger
from config import OUTPUT_DIRS

class EnergyClassifierTrainer:
    """
    能源分类器训练器
    """
    
    def __init__(self):
        self.logger = setup_logger("energy_trainer")
        self.model = None
    
    def train_model(self, train_path, val_path):
        """
        训练FastText模型
        """
        self.logger.info("🚀 Starting FastText model training...")
        self.logger.info(f"📁 Training data: {train_path}")
        self.logger.info(f"📁 Validation data: {val_path}")
        
        # 检查文件是否存在
        if not os.path.exists(train_path):
            self.logger.error(f"❌ Training file not found: {train_path}")
            return None
        
        if not os.path.exists(val_path):
            self.logger.error(f"❌ Validation file not found: {val_path}")
            return None
        
        try:
            # 训练模型
            self.logger.info("🔧 Training FastText model with parameters:")
            self.logger.info("  - Epochs: 10")
            self.logger.info("  - Learning rate: 0.5")
            self.logger.info("  - Word n-grams: 2")
            self.logger.info("  - Dimensions: 100")
            
            start_time = time.time()
            
            self.model = fasttext.train_supervised(
                input=train_path,
                epoch=10,
                lr=0.5,
                wordNgrams=2,
                dim=100,
                verbose=2
            )
            
            training_time = time.time() - start_time
            self.logger.info(f"✅ Training completed in {training_time:.2f} seconds")
            
            # 保存模型
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            model_path = os.path.join('models', f'energy_classifier_{timestamp}.bin')
            
            self.model.save_model(model_path)
            self.logger.info(f"💾 Model saved: {model_path}")
            
            return model_path
            
        except Exception as e:
            self.logger.error(f"❌ Training failed: {e}")
            return None
    
    def evaluate_model(self, val_path):
        """
        评估模型性能
        """
        if not self.model:
            self.logger.error("❌ No model available for evaluation")
            return None
        
        self.logger.info("📊 Evaluating model performance...")
        
        try:
            # 在验证集上评估
            result = self.model.test(val_path)
            
            # 提取结果
            num_samples = result[0]
            precision = result[1]
            recall = result[2]
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            self.logger.info("✅ Evaluation results:")
            self.logger.info(f"  - Samples: {num_samples}")
            self.logger.info(f"  - Precision: {precision:.4f}")
            self.logger.info(f"  - Recall: {recall:.4f}")
            self.logger.info(f"  - F1-Score: {f1_score:.4f}")
            
            return {
                'samples': num_samples,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score
            }
            
        except Exception as e:
            self.logger.error(f"❌ Evaluation failed: {e}")
            return None
    
    def test_predictions(self):
        """
        测试一些样本预测
        """
        if not self.model:
            self.logger.error("❌ No model available for testing")
            return
        
        self.logger.info("🧪 Testing sample predictions...")
        
        # 测试样本
        test_samples = [
            "Solar energy systems for renewable power generation and grid integration",
            "Wind turbine optimization for offshore energy production",
            "Battery storage technology for electric vehicle applications",
            "Smart grid infrastructure and demand response management",
            "Natural gas pipeline transportation and distribution networks",
            "Machine learning algorithms for computer vision applications",
            "Social media impact on adolescent mental health outcomes",
            "Quantum computing cryptographic security protocols",
            "Biodiversity conservation in tropical rainforest ecosystems",
            "Pharmaceutical drug development clinical trial methodologies"
        ]
        
        for i, sample in enumerate(test_samples, 1):
            try:
                prediction = self.model.predict(sample, k=2)
                labels = prediction[0]
                scores = prediction[1]
                
                self.logger.info(f"Sample {i}: {sample[:50]}...")
                self.logger.info(f"  Prediction: {labels[0]} (confidence: {scores[0]:.4f})")
                
            except Exception as e:
                self.logger.error(f"  ❌ Prediction failed: {e}")
    
    def run_complete_training(self, train_path, val_path):
        """
        运行完整的训练流程
        """
        print("🚀 ENERGY CLASSIFIER TRAINING")
        print("=" * 60)
        print("🤖 Training FastText binary classifier")
        print("🎯 Task: Energy vs Non-Energy document classification")
        print("=" * 60)
        
        # Step 1: 训练模型
        model_path = self.train_model(train_path, val_path)
        
        if not model_path:
            print("❌ Training failed!")
            return None
        
        # Step 2: 评估模型
        eval_results = self.evaluate_model(val_path)
        
        # Step 3: 测试预测
        self.test_predictions()
        
        print("\n" + "=" * 60)
        print("✅ TRAINING COMPLETED!")
        print(f"💾 Model saved: {model_path}")
        if eval_results:
            print(f"📊 F1-Score: {eval_results['f1_score']:.4f}")
            print(f"📊 Precision: {eval_results['precision']:.4f}")
            print(f"📊 Recall: {eval_results['recall']:.4f}")
        print("\n🎯 Ready for ClueWeb22 application!")
        
        return model_path

def main():
    """
    主函数
    """
    # 使用最新生成的数据文件
    train_path = "data/processed_text/energy_train_20250526_183431.txt"
    val_path = "data/processed_text/energy_val_20250526_183431.txt"
    
    trainer = EnergyClassifierTrainer()
    model_path = trainer.run_complete_training(train_path, val_path)
    
    if model_path:
        print(f"\n📋 Next steps:")
        print(f"1. Apply classifier to ClueWeb22 documents")
        print(f"2. Filter energy-related content")
        print(f"3. Analyze results and performance")

if __name__ == "__main__":
    main() 