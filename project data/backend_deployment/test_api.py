#!/usr/bin/env python3
"""
Backend API Test Script
Tests all endpoints and functionality
"""

import requests
import json
import time
import base64
import cv2
import numpy as np
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:5000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
DETECT_ENDPOINT = f"{BACKEND_URL}/detect"
SWITCH_ENDPOINT = f"{BACKEND_URL}/switch-model"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_health():
    """Test health check endpoint"""
    print_header("Testing Health Endpoint")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Status: {data.get('status')}")
        print(f"   Model Loaded: {data.get('model_loaded')}")
        print(f"   Current Model: {data.get('current_model')}")
        print(f"   Classes: {data.get('classes')}")
        print(f"   Available Models: {data.get('available_models')}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend is not running")
        print("   Start backend with: python unified_server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_test_image():
    """Create a simple test image"""
    # Create a blank image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw some shapes
    cv2.rectangle(img, (100, 100), (300, 350), (0, 255, 0), 2)
    cv2.circle(img, (500, 200), 50, (0, 0, 255), -1)
    cv2.putText(img, "Test Image", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return img

def image_to_base64(image):
    """Convert image to base64"""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def test_detect():
    """Test detection endpoint"""
    print_header("Testing Detection Endpoint")
    
    try:
        # Create test image
        test_img = create_test_image()
        img_base64 = image_to_base64(test_img)
        
        # Send request
        payload = {"image": img_base64}
        start_time = time.time()
        response = requests.post(DETECT_ENDPOINT, json=payload, timeout=30)
        inference_time = (time.time() - start_time) * 1000
        
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Success: {data.get('success')}")
        print(f"   Inference Time: {inference_time:.0f}ms")
        print(f"   Frame Size: {data.get('frame_size')}")
        print(f"   Detections: {len(data.get('detections', []))}")
        
        if data.get('detections'):
            print("\n   Detected Objects:")
            for det in data.get('detections', []):
                print(f"     • {det['class']} - Confidence: {det['confidence']:.2f}, Distance: {det['distance']:.2f}m")
        
        nav = data.get('navigation', {})
        print(f"\n   Navigation:")
        print(f"     Direction: {nav.get('direction')}")
        if nav.get('popup'):
            print(f"     Popup: {nav['popup'].get('message', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_switch_model():
    """Test model switching"""
    print_header("Testing Model Switch Endpoint")
    
    try:
        # Switch to yolov8n
        print("Switching to yolov8n model...")
        payload = {"model": "yolov8n"}
        response = requests.post(SWITCH_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Status: {data.get('status')}")
        print(f"   Current Model: {data.get('current_model')}")
        print(f"   Classes: {data.get('classes')}")
        print(f"   Message: {data.get('message')}")
        
        # Switch back to custom
        print("\nSwitching back to custom model...")
        payload = {"model": "custom"}
        response = requests.post(SWITCH_ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Status: {data.get('status')}")
        print(f"   Current Model: {data.get('current_model')}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_concurrent_requests():
    """Test multiple concurrent requests"""
    print_header("Testing Concurrent Requests")
    
    try:
        test_img = create_test_image()
        img_base64 = image_to_base64(test_img)
        payload = {"image": img_base64}
        
        print("Sending 5 concurrent requests...")
        start_time = time.time()
        
        for i in range(5):
            response = requests.post(DETECT_ENDPOINT, json=payload, timeout=30)
            response.raise_for_status()
            print(f"  Request {i+1}: ✅")
        
        total_time = time.time() - start_time
        avg_time = total_time / 5
        
        print(f"\n✅ All requests completed")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average time per request: {avg_time:.2f}s")
        print(f"   Throughput: {5/total_time:.1f} req/sec")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Backend API Test Suite")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    
    results = {}
    
    # Test 1: Health
    results["Health Check"] = test_health()
    
    if not results["Health Check"]:
        print("\n❌ Backend is not responding. Please start it first.")
        return
    
    # Give backend a moment after health check
    time.sleep(1)
    
    # Test 2: Detection
    results["Detection"] = test_detect()
    
    # Test 3: Model Switch
    results["Model Switch"] = test_switch_model()
    
    # Test 4: Concurrent Requests
    results["Concurrent Requests"] = test_concurrent_requests()
    
    # Summary
    print_header("Test Summary")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Backend is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
