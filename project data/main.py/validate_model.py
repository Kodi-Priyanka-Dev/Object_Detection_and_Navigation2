import torch
import os

model_path = 'best_model/best.pt'

# Check file exists and size
if os.path.exists(model_path):
    file_size = os.path.getsize(model_path)
    print(f"✓ File exists: {model_path}")
    print(f"  Size: {file_size / (1024*1024):.2f} MB")
else:
    print(f"✗ File not found: {model_path}")
    exit(1)

# Try to load the model
try:
    model = torch.load(model_path, weights_only=False)
    print(f"✓ Model loaded successfully")
    print(f"  Type: {type(model)}")
    
    if isinstance(model, dict):
        print(f"  Keys: {list(model.keys())}")
    else:
        print(f"  Model object: {model}")
    
    print("\n✓ NO ERRORS - Model file is valid!")
    
except Exception as e:
    print(f"✗ ERROR loading model: {type(e).__name__}")
    print(f"  Message: {str(e)}")
    exit(1)
