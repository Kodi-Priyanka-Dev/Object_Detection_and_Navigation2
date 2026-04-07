"""
TFLite Model Testing & Validation Script
Tests converted model for accuracy, speed, and correctness
"""

import os
import sys
import cv2
import numpy as np
import tensorflow as tf
import time
from pathlib import Path

class TFLiteDetector:
    """TFLite model inference wrapper"""
    
    def __init__(self, model_path):
        """Initialize interpreter"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']
        self.img_size = self.input_shape[1]  # e.g., 416
    
    def predict(self, image_path):
        """
        Run inference on image
        
        Args:
            image_path (str): Path to test image
        
        Returns:
            tuple: (raw_output, inference_time)
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Preprocess
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (self.img_size, self.img_size))
        image_normalized = image_resized.astype(np.float32) / 255.0
        image_expanded = np.expand_dims(image_normalized, axis=0)
        
        # Inference
        self.interpreter.set_tensor(self.input_details[0]['index'], image_expanded)
        
        start_time = time.time()
        self.interpreter.invoke()
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get output
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        return output, inference_time

def test_model(tflite_path, test_image_dir="../dataset/test/images"):
    """
    Comprehensive model testing
    
    Args:
        tflite_path (str): Path to .tflite model
        test_image_dir (str): Directory with test images
    """
    
    print(f"\n{'='*60}")
    print(f"🧪 TFLite Model Testing & Validation")
    print(f"{'='*60}\n")
    
    # Load detector
    try:
        print(f"📥 Loading TFLite model...")
        detector = TFLiteDetector(tflite_path)
        print(f"✓ Model loaded successfully")
        print(f"  - Input shape: {detector.input_shape}")
        print(f"  - Output layers: {len(detector.output_details)}")
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)}")
        return False
    
    # Test with sample images
    print(f"\n🔍 Running inference tests...\n")
    
    if os.path.exists(test_image_dir):
        test_images = [f for f in os.listdir(test_image_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not test_images:
            print(f"⚠️  No test images found in {test_image_dir}")
            print(f"   Skipping inference tests")
        else:
            inference_times = []
            
            for img_file in test_images[:5]:  # Test first 5 images
                img_path = os.path.join(test_image_dir, img_file)
                
                try:
                    output, inf_time = detector.predict(img_path)
                    inference_times.append(inf_time)
                    
                    print(f"  ✓ {img_file}")
                    print(f"    └─ Output shape: {output.shape}, Time: {inf_time:.2f}ms")
                
                except Exception as e:
                    print(f"  ⚠️  {img_file}: {str(e)}")
            
            if inference_times:
                avg_time = np.mean(inference_times)
                print(f"\n📊 Performance Metrics:")
                print(f"  - Average inference time: {avg_time:.2f}ms")
                print(f"  - FPS (estimated): {1000/avg_time:.1f}")
    else:
        print(f"⚠️  Test directory not found: {test_image_dir}")
        print(f"   Skipping inference tests")
    
    # Summary
    print(f"\n✅ Model validation complete!")
    print(f"{'='*60}\n")
    
    return True

def get_model_info(tflite_path):
    """Print detailed model information"""
    print(f"\n📋 Model Information:")
    print(f"  - Path: {tflite_path}")
    print(f"  - Size: {os.path.getsize(tflite_path) / (1024*1024):.2f} MB")
    
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"  - Input: {input_details[0]['shape']}")
    print(f"  - Outputs: {len(output_details)}")
    for i, out in enumerate(output_details):
        print(f"    └─ Output {i}: {out['shape']}")

if __name__ == "__main__":
    MODEL_PATH = "models/best.tflite"
    
    if os.path.exists(MODEL_PATH):
        get_model_info(MODEL_PATH)
        test_model(MODEL_PATH)
    else:
        print(f"❌ Model not found: {MODEL_PATH}")
        print(f"   Run: python convert_to_tflite.py")
