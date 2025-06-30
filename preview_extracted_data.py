#!/usr/bin/env python3
"""Preview what data is being extracted from demo files"""

import requests
import os
import json

def preview_extraction():
    """Preview extraction results"""
    base_url = "http://localhost:5001"
    
    # Use demo files
    demo_files_path = "/mnt/c/Users/cklos/document-slides-poc/demo_files"
    excel_file = os.path.join(demo_files_path, "budget_model.xlsx")
    word_file = os.path.join(demo_files_path, "executive_summary.docx")
    
    files = [
        ('documents', ('budget_model.xlsx', open(excel_file, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
        ('documents', ('executive_summary.docx', open(word_file, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
    ]
    
    print("🔄 Extracting content from demo files...")
    response = requests.post(f"{base_url}/api/generate-slides/preview", files=files, timeout=30)
    
    # Close file handles
    for _, file_tuple in files:
        file_tuple[1].close()
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n📊 Extracted Data Preview:")
        print("=" * 50)
        
        # Pretty print the JSON
        print(json.dumps(data, indent=2))
        
        # Save to file for analysis
        with open('extracted_data_preview.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print("\n✅ Full data saved to extracted_data_preview.json")
        
        # Analyze what we have
        print("\n📈 Data Analysis:")
        if 'analysis' in data:
            analysis = data['analysis']
            
            if 'financial_metrics' in analysis:
                print(f"  - Financial metrics: {len(analysis['financial_metrics'])} items")
                
            if 'company_overview' in analysis:
                print(f"  - Company overview: {list(analysis['company_overview'].keys())}")
                
            if 'key_insights' in analysis:
                print(f"  - Key insights: {len(analysis['key_insights'])} insights")
                
            if 'charts_data' in analysis:
                print(f"  - Chart data available: {list(analysis['charts_data'].keys())}")
        
    else:
        print(f"❌ Preview failed: {response.text}")

if __name__ == "__main__":
    preview_extraction()