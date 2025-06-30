#!/usr/bin/env python3
"""Debug API error for slide generation"""

import requests
import os
import sys
import traceback

def test_slide_generation():
    """Test slide generation with detailed error tracking"""
    url = "http://localhost:5001/api/generate-slides"
    
    # Prepare test files
    demo_dir = "/mnt/c/Users/cklos/document-slides-poc/demo_files"
    files = []
    
    # Add budget model
    budget_file = os.path.join(demo_dir, "budget_model.xlsx")
    if os.path.exists(budget_file):
        files.append(('documents', ('budget_model.xlsx', open(budget_file, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))
    
    # Add executive summary
    exec_file = os.path.join(demo_dir, "executive_summary.docx")
    if os.path.exists(exec_file):
        files.append(('documents', ('executive_summary.docx', open(exec_file, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')))
    
    if not files:
        print("❌ No demo files found")
        return
    
    # Make request with template_id
    data = {'template_id': 'default'}
    
    try:
        print("🔄 Sending request to API...")
        response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Save the presentation
            with open('debug_output.pptx', 'wb') as f:
                f.write(response.content)
            print("✅ Presentation saved as debug_output.pptx")
        else:
            print(f"❌ Error response: {response.text}")
            
            # Try to get more details from the API
            try:
                error_data = response.json()
                print(f"📋 Error details: {error_data}")
            except:
                print("📋 Could not parse error as JSON")
    
    except Exception as e:
        print(f"💥 Request failed: {str(e)}")
        traceback.print_exc()
    
    finally:
        # Close files
        for _, file_tuple in files:
            file_tuple[1].close()

if __name__ == "__main__":
    print("🔍 Debug API Error Tool")
    print("=" * 50)
    test_slide_generation()