#!/usr/bin/env python3
"""
Fine-Tune YOLOv8 Model on New Dataset
=====================================

Transfer learning using the new synthetic dataset
"""

import os
import yaml
import torch
from pathlib import Path
from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinetuneYOLO:
    def __init__(self):
        self.model_path = "best_model/best.pt"
        self.data_yaml = r"C:\Users\Priyanka\Documents\project data\dataset_fine_tune\data.yaml"
        self.resume_checkpoint = "runs/detect/finetune/weights/last.pt"
        self.device = 0 if torch.cuda.is_available() else "cpu"
        
        # Fine-tuning parameters
        self.params = {
            'epochs': 40,
            'batch': 64,
            'imgsz': 640,
            'lr0': 0.0001,  # Very low learning rate for fine-tuning
            'lrf': 0.01,
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'warmup_momentum': 0.8,
            'patience': 10,
            'device': self.device,
            'exist_ok': True,
            'verbose': True,
            'amp': True,
            'plots': True,
            'save': True,
            'cache': 'ram',
            'workers': 8,
        }
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("\n" + "=" * 80)
        print("🔍 CHECKING PREREQUISITES")
        print("=" * 80)
        
        checks_passed = True
        
        # Check GPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✅ GPU available: {gpu_name}")
            print(f"   Memory: {gpu_memory:.1f} GB")
        else:
            print("⚠️  No GPU detected - will use CPU (very slow!)")
        
        # Check model
        if os.path.exists(self.model_path):
            model_size = os.path.getsize(self.model_path) / 1e6
            print(f"✅ Pre-trained model found: {self.model_path}")
            print(f"   Size: {model_size:.1f} MB")
        else:
            print(f"❌ Pre-trained model not found: {self.model_path}")
            checks_passed = False
        
        # Check dataset
        if os.path.exists(self.data_yaml):
            with open(self.data_yaml, 'r') as f:
                data_config = yaml.safe_load(f)
                print(f"✅ Dataset config found: {self.data_yaml}")
                print(f"   Classes: {data_config.get('nc', 'unknown')}")
                
                # Check if actual data exists
                base_path = data_config.get('path', '')
                for split in ['train', 'val', 'test']:
                    split_path = os.path.join(base_path, split, 'images')
                    if os.path.exists(split_path):
                        img_count = len(list(Path(split_path).glob("*")))
                        print(f"   ✅ {split}: {img_count} images")
                    else:
                        print(f"   ❌ {split} not found: {split_path}")
                        checks_passed = False
        else:
            print(f"❌ Dataset config not found: {self.data_yaml}")
            checks_passed = False
        
        print("=" * 80)
        
        if not checks_passed:
            raise RuntimeError("❌ Prerequisites check failed!")
        else:
            print("✅ All prerequisites OK!\n")
        
        return True
    
    def load_model(self):
        """Load pre-trained model"""
        print("🔄 Loading pre-trained model...")
        self.model = YOLO(self.model_path)
        print(f"✅ Model loaded: {self.model.model_name}")
        return self.model
    
    def finetune(self):
        """Execute fine-tuning"""
        print("\n" + "=" * 80)
        print("🚀 STARTING FINE-TUNING")
        print("=" * 80)
        print(f"📊 Configuration:")
        print(f"   Epochs: {self.params['epochs']}")
        print(f"   Batch Size: {self.params['batch']}")
        print(f"   Learning Rate: {self.params['lr0']}")
        print(f"   Image Size: {self.params['imgsz']}")
        print(f"   Device: {self.params['device']}")
        print("=" * 80 + "\n")
        
        try:
            # Start training
            results = self.model.train(
                data=self.data_yaml,
                project="runs/detect",
                name="finetune",
                **self.params,
            )
            
            return results
        
        except Exception as e:
            print(f"❌ Training error: {e}")
            raise
    
    def print_results(self):
        """Print and analyze results"""
        print("\n" + "=" * 80)
        print("📈 TRAINING RESULTS")
        print("=" * 80)
        
        weights_dir = Path("runs/detect/finetune/weights")
        if weights_dir.exists():
            best_model = weights_dir / "best.pt"
            last_model = weights_dir / "last.pt"
            
            if best_model.exists():
                size = best_model.stat().st_size / 1e6
                print(f"✅ Best model: {best_model}")
                print(f"   Size: {size:.1f} MB")
                
                # Print model complexity
                model = YOLO(str(best_model))
                print(f"   Params: {sum(p.numel() for p in model.model.parameters()) / 1e6:.1f}M")
        
        print("=" * 80)
        print("\n✅ Fine-tuning complete!")
        print("\nNext steps:")
        print("  1. Deploy: cp runs/detect/finetune/weights/best.pt best_model/best.pt")
        print("  2. Restart backend: python backend_service.py")
        print("  3. Test in app: flutter run")
    
    def resume_finetuning(self):
        """Resume fine-tuning from checkpoint"""
        print(f"\n🔄 Resuming from checkpoint: {self.resume_checkpoint}")
        if os.path.exists(self.resume_checkpoint):
            self.model = YOLO(self.resume_checkpoint)
            results = self.model.train(
                data=self.data_yaml,
                project="runs/detect",
                name="finetune",
                resume=True,
                **self.params,
            )
            return results
        else:
            print(f"❌ Checkpoint not found: {self.resume_checkpoint}")
            return None
    
    def run(self, resume=False):
        """Main workflow"""
        try:
            # Step 1: Check prerequisites
            self.check_prerequisites()
            
            # Step 2: Load model
            self.load_model()
            
            # Step 3: Fine-tune
            if resume and os.path.exists(self.resume_checkpoint):
                results = self.resume_finetuning()
            else:
                results = self.finetune()
            
            # Step 4: Print results
            self.print_results()
            
            print("\n" + "=" * 80)
            print("🎉 FINE-TUNING PIPELINE COMPLETE!")
            print("=" * 80)
            
            return results
        
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            raise

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-tune YOLOv8 on new dataset')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    finetune = FinetuneYOLO()
    finetune.run(resume=args.resume)
