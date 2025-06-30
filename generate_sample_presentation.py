#!/usr/bin/env python3
"""
Generate a sample presentation for review
Uses the demo files to create a PowerPoint presentation you can inspect
"""

import requests
import os
from datetime import datetime

def generate_sample_presentation():
    """Generate a sample presentation using demo files"""
    
    base_url = "http://localhost:5001"
    api_url = f"{base_url}/api"
    
    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API server not running on localhost:5001")
            return False
    except:
        print("❌ API server not running on localhost:5001")
        return False
    
    print("✅ API server is running")
    
    # Use demo files
    demo_files_path = "/mnt/c/Users/cklos/document-slides-poc/demo_files"
    excel_file = os.path.join(demo_files_path, "budget_model.xlsx")
    word_file = os.path.join(demo_files_path, "executive_summary.docx")
    
    if not os.path.exists(excel_file):
        print(f"❌ Demo file not found: {excel_file}")
        return False
    
    if not os.path.exists(word_file):
        print(f"❌ Demo file not found: {word_file}")
        return False
    
    print(f"📁 Using demo files:")
    print(f"   - {excel_file}")
    print(f"   - {word_file}")
    
    # Generate presentation
    try:
        files = [
            ('documents', ('budget_model.xlsx', open(excel_file, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
            ('documents', ('executive_summary.docx', open(word_file, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
        ]
        
        data = {'template_id': 'default'}
        
        print("🔄 Generating presentation...")
        response = requests.post(f"{api_url}/generate-slides", files=files, data=data, timeout=60)
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            # Save the generated file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"sample_presentation_for_review_{timestamp}.pptx"
            output_path = f"/mnt/c/Users/cklos/document-slides-poc/{output_filename}"
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Presentation generated successfully!")
            print(f"📄 Saved as: {output_filename}")
            print(f"📍 Full path: {output_path}")
            print(f"📊 File size: {len(response.content):,} bytes")
            
            # Show file info
            print("\n📋 Presentation Details:")
            print(f"   - Template: default")
            print(f"   - Source files: budget_model.xlsx, executive_summary.docx")
            print(f"   - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Generating Sample Presentation for Review")
    print("=" * 50)
    
    success = generate_sample_presentation()
    
    if success:
        print("\n🎉 Success! You can now open the .pptx file to review the presentation.")
        print("💡 The file will be in your document-slides-poc directory.")
    else:
        print("\n💥 Failed to generate presentation. Please check the API server.")
    
    exit(0 if success else 1)