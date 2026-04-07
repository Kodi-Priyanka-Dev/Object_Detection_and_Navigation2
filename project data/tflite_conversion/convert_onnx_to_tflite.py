"""
Alternative TFLite Conversion: ONNX → TFLite
Uses a simpler two-step process to avoid dependency issues
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO

def export_to_onnx(model_path, output_dir):
    """
    Step 1: Export YOLOv8 .pt to ONNX format (simpler, fewer dependencies)
    """
    print(f"\n{'='*60}")
    print(f"📥 Step 1: Export PyTorch → ONNX")
    print(f"{'='*60}\n")
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        sys.exit(1)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading model: {model_path}")
    model = YOLO(model_path)
    print(f"✓ Model loaded\n")
    
    print(f"🔄 Exporting to ONNX... (This is faster)")
    onnx_path = model.export(
        format='onnx',
        imgsz=416,
        half=False,
        dynamic=False
    )
    
    onnx_path = str(onnx_path)
    final_onnx = os.path.join(output_dir, 'best.onnx')
    
    if os.path.exists(onnx_path) and onnx_path != final_onnx:
        import shutil
        shutil.move(onnx_path, final_onnx)
    
    file_size = os.path.getsize(final_onnx) / (1024 * 1024)
    print(f"✅ ONNX export successful: {final_onnx}")
    print(f"   Size: {file_size:.2f} MB\n")
    
    return final_onnx

def convert_onnx_to_tflite(onnx_path, output_dir):
    """
    Step 2: Convert ONNX → TFLite using onnx2tf
    """
    print(f"{'='*60}")
    print(f"🔄 Step 2: Convert ONNX → TFLite")
    print(f"{'='*60}\n")
    
    if not os.path.exists(onnx_path):
        print(f"❌ ONNX model not found")
        sys.exit(1)
    
    try:
        import onnx2tf
    except ImportError:
        print("⚠️  onnx2tf not installed. Installing...")
        os.system("pip install onnx2tf -q")
        import onnx2tf
    
    os.makedirs(output_dir, exist_ok=True)
    
    tflite_model_path = os.path.join(output_dir, 'best.tflite')
    tflite_dir = os.path.join(output_dir, 'tflite_model')
    
    print(f"Converting: {onnx_path}")
    print(f"Output: {tflite_model_path}\n")
    
    # Use onnx2tf for conversion
    print("🔄 Running ONNX to TFLite conversion...")
    print("   (This may take 2-5 minutes)\n")
    
    import subprocess
    cmd = [
        sys.executable, '-m', 'onnx2tf',
        '-i', onnx_path,
        '-o', tflite_dir,
        '-oiqt'  # Output in quantized TFLite format
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"⚠️  Conversion warning (this might still work):")
        print(f"   {result.stderr[:200]}")
    
    # Look for generated TFLite file
    tflite_candidates = []
    for root, dirs, files in os.walk(tflite_dir):
        for file in files:
            if file.endswith('.tflite'):
                tflite_candidates.append(os.path.join(root, file))
    
    if tflite_candidates:
        generated_tflite = tflite_candidates[0]
        import shutil
        shutil.copy(generated_tflite, tflite_model_path)
        
        file_size = os.path.getsize(tflite_model_path) / (1024 * 1024)
        print(f"\n✅ TFLite conversion successful!")
        print(f"{'='*60}")
        print(f"📦 Output: {tflite_model_path}")
        print(f"📊 Size: {file_size:.2f} MB")
        print(f"{'='*60}\n")
        
        return tflite_model_path
    else:
        print("⚠️  Could not find TFLite file after conversion")
        return None

def main():
    """Main conversion pipeline"""
    BEST_PT =  "../best_model/best.pt"
    OUTPUT_DIR = "models"
    
    # Step 1: Export to ONNX
    onnx_model = export_to_onnx(BEST_PT, OUTPUT_DIR)
    
    # Step 2: Convert to TFLite
    if onnx_model:
        tflite_model = convert_onnx_to_tflite(onnx_model, OUTPUT_DIR)
        
        if tflite_model and os.path.exists(tflite_model):
            print("✅ Full conversion pipeline complete!")
            print(f"\n📋 Next steps:")
            print(f"   1. python test_tflite.py")
            print(f"   2. python flutter_integration_generator.py")
            print(f"   3. Copy {tflite_model} to Flutter assets/models/")
        else:
            print("⚠️  Conversion completed but TFLite file not generated")
            print("   Try: pip install -U onnx2tf tensorflow")

if __name__ == "__main__":
    main()
