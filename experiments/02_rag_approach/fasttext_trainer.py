#!/usr/bin/env python3
"""
FastText Training Module for Energy Document Classification
Trains and evaluates a binary classifier for energy vs non-energy documents
"""

import os
import json
import fasttext
from typing import Dict, Tuple
from utils.logger import setup_logger
from config import OUTPUT_DIRS

class FastTextTrainer:
    """
    Train and evaluate FastText classifier for energy document classification
    """
    
    def __init__(self):
        self.logger = setup_logger("fasttext_trainer")
        self.model = None
        
        # Create models directory
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
    
    def train_model(self, train_file: str, **kwargs) -> fasttext.FastText._FastText:
        """
        Train FastText supervised model
        """
        # Default hyperparameters optimized for text classification
        default_params = {
            'lr': 0.5,              # Learning rate
            'epoch': 10,            # Number of epochs
            'wordNgrams': 2,        # Use bigrams
            'dim': 100,             # Vector dimensions
            'ws': 5,                # Context window size
            'minCount': 1,          # Minimum word count
            'minn': 3,              # Min char ngram
            'maxn': 6,              # Max char ngram
            'neg': 5,               # Number of negatives sampled
            'loss': 'softmax',      # Loss function
            'bucket': 2000000,      # Number of buckets
            'thread': 4,            # Number of threads
            'lrUpdateRate': 100,    # Learning rate update rate
            't': 1e-4,              # Sampling threshold
            'verbose': 2            # Verbose level
        }
        
        # Update with any provided parameters
        params = {**default_params, **kwargs}
        
        self.logger.info("Training FastText model with parameters:")
        for key, value in params.items():
            self.logger.info(f"  {key}: {value}")
        
        try:
            # Train the model
            self.model = fasttext.train_supervised(
                input=train_file,
                **params
            )
            
            self.logger.info("✅ Model training completed successfully!")
            return self.model
            
        except Exception as e:
            self.logger.error(f"❌ Error training model: {e}")
            raise
    
    def evaluate_model(self, valid_file: str) -> Dict:
        """
        Evaluate the trained model on validation data
        """
        if not self.model:
            raise ValueError("Model not trained yet!")
        
        try:
            # Test the model
            result = self.model.test(valid_file)
            
            # Extract metrics
            num_samples = result[0]
            precision = result[1]
            recall = result[2]
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics = {
                'samples': num_samples,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score
            }
            
            self.logger.info("📊 Model Evaluation Results:")
            self.logger.info(f"  Samples: {num_samples}")
            self.logger.info(f"  Precision: {precision:.4f}")
            self.logger.info(f"  Recall: {recall:.4f}")
            self.logger.info(f"  F1-Score: {f1_score:.4f}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating model: {e}")
            raise
    
    def save_model(self, model_name: str = "energy_classifier") -> str:
        """
        Save the trained model
        """
        if not self.model:
            raise ValueError("Model not trained yet!")
        
        model_path = os.path.join(self.models_dir, f"{model_name}.bin")
        
        try:
            self.model.save_model(model_path)
            self.logger.info(f"💾 Model saved to: {model_path}")
            return model_path
            
        except Exception as e:
            self.logger.error(f"❌ Error saving model: {e}")
            raise
    
    def load_model(self, model_path: str) -> fasttext.FastText._FastText:
        """
        Load a trained model
        """
        try:
            self.model = fasttext.load_model(model_path)
            self.logger.info(f"📂 Model loaded from: {model_path}")
            return self.model
            
        except Exception as e:
            self.logger.error(f"❌ Error loading model: {e}")
            raise
    
    def predict_text(self, text: str, k: int = 1) -> Tuple[list, list]:
        """
        Predict label for a single text
        """
        if not self.model:
            raise ValueError("Model not trained/loaded yet!")
        
        try:
            labels, probabilities = self.model.predict(text, k=k)
            return labels, probabilities
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting text: {e}")
            raise
    
    def predict_file(self, input_file: str, output_file: str = None) -> list:
        """
        Predict labels for texts in a file
        """
        if not self.model:
            raise ValueError("Model not trained/loaded yet!")
        
        predictions = []
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        # Remove existing label if present
                        if line.startswith('__label__'):
                            text = line.split('\t', 1)[1] if '\t' in line else line
                        else:
                            text = line
                        
                        labels, probabilities = self.predict_text(text)
                        
                        prediction = {
                            'line': line_num,
                            'text': text[:100] + '...' if len(text) > 100 else text,
                            'predicted_label': labels[0],
                            'confidence': probabilities[0]
                        }
                        predictions.append(prediction)
            
            # Save predictions if output file specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(predictions, f, indent=2, ensure_ascii=False)
                self.logger.info(f"💾 Predictions saved to: {output_file}")
            
            self.logger.info(f"🔮 Predicted {len(predictions)} texts")
            return predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting file: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """
        Get information about the trained model
        """
        if not self.model:
            raise ValueError("Model not trained/loaded yet!")
        
        try:
            info = {
                'labels': self.model.get_labels(),
                'vocab_size': len(self.model.get_words()),
                'dimension': self.model.get_dimension(),
                'learning_rate': self.model.lr,
                'epochs': self.model.epoch,
                'word_ngrams': self.model.wordNgrams
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"❌ Error getting model info: {e}")
            raise
    
    def hyperparameter_tuning(self, train_file: str, valid_file: str) -> Dict:
        """
        Perform basic hyperparameter tuning
        """
        self.logger.info("🔧 Starting hyperparameter tuning...")
        
        # Parameter combinations to try
        param_combinations = [
            {'lr': 0.1, 'epoch': 5, 'wordNgrams': 1, 'dim': 50},
            {'lr': 0.5, 'epoch': 10, 'wordNgrams': 2, 'dim': 100},
            {'lr': 1.0, 'epoch': 15, 'wordNgrams': 2, 'dim': 150},
            {'lr': 0.5, 'epoch': 20, 'wordNgrams': 3, 'dim': 100},
        ]
        
        best_f1 = 0
        best_params = None
        results = []
        
        for i, params in enumerate(param_combinations, 1):
            self.logger.info(f"🧪 Testing combination {i}/{len(param_combinations)}: {params}")
            
            try:
                # Train model with these parameters
                model = fasttext.train_supervised(input=train_file, **params, verbose=0)
                
                # Evaluate
                result = model.test(valid_file)
                precision, recall = result[1], result[2]
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                result_dict = {
                    'params': params,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1_score
                }
                results.append(result_dict)
                
                self.logger.info(f"  F1-Score: {f1_score:.4f}")
                
                # Update best if this is better
                if f1_score > best_f1:
                    best_f1 = f1_score
                    best_params = params
                    self.model = model  # Keep the best model
                
            except Exception as e:
                self.logger.error(f"  Error with params {params}: {e}")
        
        self.logger.info(f"🏆 Best parameters: {best_params}")
        self.logger.info(f"🏆 Best F1-Score: {best_f1:.4f}")
        
        return {
            'best_params': best_params,
            'best_f1': best_f1,
            'all_results': results
        }

def main():
    """
    Main training function
    """
    trainer = FastTextTrainer()
    
    print("🚀 Training FastText Energy Classifier")
    print("=" * 50)
    
    # File paths
    train_file = os.path.join(OUTPUT_DIRS['processed_text'], 'train.txt')
    valid_file = os.path.join(OUTPUT_DIRS['processed_text'], 'valid.txt')
    
    # Check if files exist
    if not os.path.exists(train_file):
        print(f"❌ Training file not found: {train_file}")
        print("Please run text_processor.py first!")
        return
    
    if not os.path.exists(valid_file):
        print(f"❌ Validation file not found: {valid_file}")
        print("Please run text_processor.py first!")
        return
    
    try:
        # Train model
        print("🔄 Training model...")
        model = trainer.train_model(train_file)
        
        # Evaluate model
        print("📊 Evaluating model...")
        metrics = trainer.evaluate_model(valid_file)
        
        # Save model
        print("💾 Saving model...")
        model_path = trainer.save_model("energy_classifier")
        
        # Get model info
        info = trainer.get_model_info()
        
        print("\n✅ Training completed successfully!")
        print(f"📁 Model saved to: {model_path}")
        print(f"📊 F1-Score: {metrics['f1_score']:.4f}")
        print(f"🔤 Vocabulary size: {info['vocab_size']}")
        print(f"📏 Vector dimension: {info['dimension']}")
        
        # Test with sample predictions
        print("\n🔮 Testing sample predictions:")
        sample_texts = [
            "solar energy conversion efficiency in photovoltaic systems",
            "machine learning algorithms for image classification",
            "wind power generation and grid integration challenges",
            "web development using react and javascript frameworks"
        ]
        
        for text in sample_texts:
            labels, probs = trainer.predict_text(text)
            print(f"  Text: {text[:50]}...")
            print(f"  Prediction: {labels[0]} (confidence: {probs[0]:.3f})")
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        raise

if __name__ == "__main__":
    main() 