"""
YOLOv8 Model Conversion Script: .pt → .tflite
Converts trained YOLOv8 model to TensorFlow Lite format for mobile deployment
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
import tensorflow as tf

def convert_model(model_path, output_dir, img_size=416, quantize=True):
    """
    Convert YOLOv8 .pt model to .tflite format (Simplified)
    
    Args:
        model_path (str): Path to best.pt model
        output_dir (str): Directory to save converted model
        img_size (int): Input image size
        quantize (bool): Enable quantization for mobile optimization
    
    Returns:
        str: Path to generated .tflite file
    """
    
    print(f"\n{'='*60}")
    print(f"🚀 YOLOv8 Model Conversion: .pt → .tflite")
    print(f"{'='*60}\n")
    
    # Verify input model exists
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model not found at {model_path}")
        sys.exit(1)
    
    print(f"✓ Input model: {model_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load YOLOv8 model
        print(f"\n📥 Loading YOLOv8 model...")
        model = YOLO(model_path)
        print(f"✓ Model loaded successfully")
        
        # Export to TFLite
        print(f"\n🔄 Exporting to TFLite format...")
        print(f"   - Image size: {img_size}x{img_size}")
        print(f"   - Format: TFLite Lite (optimized for mobile)")
        print(f"   - This may take 3-10 minutes (one-time process)...")
        
        # Simplified export - skip simplify to speed up
        export_result = model.export(
            format='tflite',
            imgsz=img_size,
            half=False,           # Full precision
            dynamic=False,        # Fixed input shape (faster inference)
            simplify=False        # Skip ONNX simplification (faster)
        )
        
        # Get the actual output path
        tflite_path = str(export_result)
        
        # Move to output directory if needed
        if not tflite_path.startswith(output_dir):
            final_tflite = os.path.join(output_dir, 'best.tflite')
            if os.path.exists(tflite_path):
                import shutil
                shutil.move(tflite_path, final_tflite)
                tflite_path = final_tflite
        
        # Verify output
        if not os.path.exists(tflite_path):
            print(f"❌ ERROR: TFLite model not created")
            sys.exit(1)
        
        file_size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
        
        print(f"\n✅ Conversion successful!")
        print(f"{'='*60}")
        print(f"📦 Output model: {tflite_path}")
        print(f"📊 Model size: {file_size_mb:.2f} MB")
        print(f"{'='*60}\n")
        
        return tflite_path
    
    except Exception as e:
        print(f"\n❌ ERROR during conversion: {str(e)}")
        print(f"   Possible solutions:")
        print(f"   1. pip install --upgrade ultralytics")
        print(f"   2. pip install tensorflow opencv-python")
        print(f"   3. Ensure ../best_model/best.pt exists")
        sys.exit(1)

def verify_tflite_model(tflite_path):
    """
    Verify TFLite model can be loaded
    
    Args:
        tflite_path (str): Path to .tflite file
    """
    print(f"\n🔍 Verifying TFLite model...")
    
    try:
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"✓ Model verified successfully")
        print(f"  - Input shape: {input_details[0]['shape']}")
        print(f"  - Output layers: {len(output_details)}")
        
        return True
    
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Configuration
    BEST_PT_PATH = os.path.join("..", "best_model", "best.pt")
    OUTPUT_DIR = "models"
    IMG_SIZE = 416
    
    # Run conversion
    tflite_model = convert_model(
        model_path=BEST_PT_PATH,
        output_dir=OUTPUT_DIR,
        img_size=IMG_SIZE,
        quantize=True
    )
    
    # Verify result
    if tflite_model and os.path.exists(tflite_model):
        verify_tflite_model(tflite_model)
        
        print(f"\n📋 Next steps:")
        print(f"   1. Test the model with: python test_tflite.py")
        print(f"   2. Copy {tflite_model} to Flutter assets/")
        print(f"   3. Follow Flutter integration guide")
    else:
        print(f"⚠️  Conversion may have failed. Check the output above.")
