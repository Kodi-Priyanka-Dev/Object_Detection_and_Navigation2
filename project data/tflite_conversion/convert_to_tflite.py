"""
YOLOv8 Model Conversion Script: .pt → .tflite
Converts trained YOLOv8 model to TensorFlow Lite format for mobile deployment
Supports model switching: YOLOv8n (official) vs Custom Best Model
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
import tensorflow as tf
import tkinter as tk
from tkinter import messagebox, ttk
import threading

def convert_model(model_path, output_dir, img_size=416, quantize=True, model_name=None):
    """
    Convert YOLOv8 .pt model to .tflite format (Simplified)
    
    Args:
        model_path (str): Path to best.pt model or yolov8n.pt
        output_dir (str): Directory to save converted model
        img_size (int): Input image size
        quantize (bool): Enable quantization for mobile optimization
        model_name (str): Name prefix for output (e.g., 'best' or 'yolov8n')
    
    Returns:
        str: Path to generated .tflite file
    """
    
    print(f"\n{'='*60}")
    print(f"🚀 YOLOv8 Model Conversion: .pt → .tflite")
    print(f"{'='*60}\n")
    
    # Verify input model exists
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model not found at {model_path}")
        return None
    
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
            model_suffix = model_name if model_name else 'best'
            final_tflite = os.path.join(output_dir, f'{model_suffix}.tflite')
            if os.path.exists(tflite_path):
                import shutil
                shutil.move(tflite_path, final_tflite)
                tflite_path = final_tflite
        
        # Verify output
        if not os.path.exists(tflite_path):
            print(f"❌ ERROR: TFLite model not created")
            return None
        
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
        print(f"   3. Ensure model file exists and is valid")
        return None

def verify_tflite_model(tflite_path):
    """
    Verify TFLite model can be loaded
    
    Args:
        tflite_path (str): Path to .tflite file
    
    Returns:
        bool: True if verification successful, False otherwise
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

# ============================================================================
# GUI MODEL SWITCHER & CONVERTER
# ============================================================================

class TFLiteConverterApp:
    """GUI Application for YOLOv8 to TFLite conversion with model switching"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YOLOv8 → TFLite Model Converter")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Model configuration
        self.models = {
            'Custom Best': {
                'path': os.path.join("..", "best_model", "best.pt"),
                'name': 'best'
            },
            'YOLOv8n (Official)': {
                'path': os.path.join("..", "yolov8n.pt"),
                'name': 'yolov8n'
            }
        }
        
        self.selected_model = 'Custom Best'
        self.output_dir = "models"
        self.img_size = 416
        self.is_converting = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the GUI components"""
        
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text="🚀 YOLOv8 → TFLite Converter",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Model Selection Frame
        model_frame = tk.LabelFrame(self.root, text="📦 Select Model", padx=15, pady=15)
        model_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Model info label
        self.model_info_label = tk.Label(
            model_frame,
            text="Current Model: Custom Best",
            font=("Arial", 10),
            fg="#27ae60"
        )
        self.model_info_label.pack(pady=10)
        
        # Model buttons
        button_sub_frame = tk.Frame(model_frame)
        button_sub_frame.pack(fill=tk.X)
        
        self.custom_btn = tk.Button(
            button_sub_frame,
            text="🎯 Custom Best Model",
            width=25,
            command=lambda: self._select_model('Custom Best'),
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED
        )
        self.custom_btn.pack(side=tk.LEFT, padx=5)
        
        self.yolo_btn = tk.Button(
            button_sub_frame,
            text="🟡 YOLOv8n Official",
            width=25,
            command=lambda: self._select_model('YOLOv8n (Official)'),
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED
        )
        self.yolo_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings Frame
        settings_frame = tk.LabelFrame(self.root, text="⚙️  Conversion Settings", padx=15, pady=15)
        settings_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Image size
        size_frame = tk.Frame(settings_frame)
        size_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(size_frame, text="Image Size:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value="416")
        size_spinbox = tk.Spinbox(
            size_frame,
            from_=128,
            to=640,
            width=10,
            textvariable=self.size_var,
            font=("Arial", 10)
        )
        size_spinbox.pack(side=tk.LEFT, padx=5)
        tk.Label(size_frame, text="(128-640)", font=("Arial", 9), fg="gray").pack(side=tk.LEFT)
        
        # Output directory
        dir_frame = tk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(dir_frame, text="Output Dir:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="models")
        output_entry = tk.Entry(dir_frame, textvariable=self.output_var, width=40, font=("Arial", 10))
        output_entry.pack(side=tk.LEFT, padx=5)
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="📊 Status", padx=15, pady=15)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.status_text = tk.Text(status_frame, height=8, width=70, font=("Courier", 9))
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for status text
        scrollbar = tk.Scrollbar(self.status_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)
        
        # Control Buttons Frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.convert_btn = tk.Button(
            control_frame,
            text="🔄 Convert to TFLite",
            width=25,
            command=self._start_conversion,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            activebackground="#229954"
        )
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            control_frame,
            text="🗑️  Clear Log",
            width=15,
            command=self._clear_status,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold")
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Initial status
        self._log_status("Ready to convert models\n")
    
    def _select_model(self, model_name):
        """Update selected model"""
        self.selected_model = model_name
        self.model_info_label.config(text=f"Current Model: {model_name}")
        
        # Update button colors
        if model_name == 'Custom Best':
            self.custom_btn.config(bg="#3498db", relief=tk.SUNKEN)
            self.yolo_btn.config(bg="#95a5a6", relief=tk.RAISED)
        else:
            self.custom_btn.config(bg="#95a5a6", relief=tk.RAISED)
            self.yolo_btn.config(bg="#3498db", relief=tk.SUNKEN)
        
        self._log_status(f"✓ Selected: {model_name}\n")
    
    def _log_status(self, message):
        """Append message to status text"""
        self.status_text.insert(tk.END, message)
        self.status_text.see(tk.END)
        self.root.update()
    
    def _clear_status(self):
        """Clear status text"""
        self.status_text.delete(1.0, tk.END)
    
    def _start_conversion(self):
        """Start conversion in separate thread to avoid freezing UI"""
        if self.is_converting:
            messagebox.showwarning("Warning", "Conversion already in progress!")
            return
        
        threading.Thread(target=self._run_conversion, daemon=True).start()
    
    def _run_conversion(self):
        """Run the actual conversion"""
        self.is_converting = True
        self.convert_btn.config(state=tk.DISABLED, bg="#95a5a6")
        
        try:
            model_info = self.models[self.selected_model]
            model_path = model_info['path']
            model_name = model_info['name']
            output_dir = self.output_var.get()
            img_size = int(self.size_var.get())
            
            self._log_status(f"\n{'='*60}\n")
            self._log_status(f"Starting conversion...\n")
            self._log_status(f"Model: {self.selected_model}\n")
            self._log_status(f"Path: {model_path}\n")
            self._log_status(f"Output: {output_dir}\n")
            self._log_status(f"Image Size: {img_size}x{img_size}\n")
            self._log_status(f"{'='*60}\n\n")
            
            # Check if model exists
            if not os.path.exists(model_path):
                self._log_status(f"❌ ERROR: Model not found at {model_path}\n")
                messagebox.showerror("Error", f"Model not found at:\n{model_path}")
                return
            
            # Convert model
            tflite_path = convert_model(
                model_path=model_path,
                output_dir=output_dir,
                img_size=img_size,
                quantize=True,
                model_name=model_name
            )
            
            if tflite_path:
                self._log_status(f"\n✅ Conversion successful!\n")
                self._log_status(f"Output: {tflite_path}\n\n")
                
                # Verify
                if verify_tflite_model(tflite_path):
                    self._log_status(f"✅ Model verified!\n")
                    file_size = os.path.getsize(tflite_path) / (1024 * 1024)
                    self._log_status(f"📊 File size: {file_size:.2f} MB\n")
                    
                    messagebox.showinfo(
                        "Success",
                        f"Model converted successfully!\n\n"
                        f"Output: {tflite_path}\n"
                        f"Size: {file_size:.2f} MB"
                    )
                else:
                    self._log_status(f"⚠️  Verification failed\n")
            else:
                self._log_status(f"❌ Conversion failed!\n")
                messagebox.showerror("Error", "Conversion failed. Check the log for details.")
        
        except Exception as e:
            self._log_status(f"❌ ERROR: {str(e)}\n")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.is_converting = False
            self.convert_btn.config(state=tk.NORMAL, bg="#27ae60")


if __name__ == "__main__":
    root = tk.Tk()
    app = TFLiteConverterApp(root)
    root.mainloop()
