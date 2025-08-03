
#!/usr/bin/env python3
"""
Test script to verify the extraction of file maps from JavaScript and CSS files.
This specifically tests the special format without nested comments.
"""

import sys
import os
import re
import json
from pathlib import Path

# Add the src directory to the path for importing
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# Import the functions from genfilemap
from genfilemap.utils.file_utils import extract_existing_file_map, get_comment_style

# Override debug_print function to see debug output
def debug_print(msg):
    print(f"DEBUG: {msg}")

# Replace the debug_print function in file_utils
import genfilemap.utils.file_utils
genfilemap.utils.file_utils.debug_print = debug_print

# Test files
js_test_file = "test_js_file.js"
css_test_file = "test_css_style.css"

def test_extraction(file_path):
    print(f"\nTesting extraction for: {file_path}")
    
    # Get file extension and comment style
    ext = Path(file_path).suffix.lower()
    comment_style = get_comment_style(file_path)
    print(f"File extension: {ext}")
    print(f"Comment style: {comment_style}")
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the file map
    print("Extracting file map...")
    result = extract_existing_file_map(content, comment_style)
    
    if result is not None and len(result) == 2:
        file_map, remaining_content = result
        print(f"Successfully extracted file map ({len(file_map)} chars)")
        print(f"First 100 chars of file map: {file_map[:100]}...")
        
        # Try to find the JSON content within the file map
        print("Looking for JSON in the file map...")
        json_pattern = r'(\{.*\})'
        json_match = re.search(json_pattern, file_map, re.DOTALL)
        
        if json_match:
            json_content = json_match.group(1)
            print(f"Found JSON content ({len(json_content)} chars)")
            
            # Try to parse the JSON
            try:
                json_obj = json.loads(json_content)
                print("Successfully parsed JSON content!")
                print(f"File metadata: {json.dumps(json_obj.get('file_metadata', {}), indent=2)}")
                return True
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {str(e)}")
                return False
        else:
            print("No JSON content found in the file map")
            return False
    else:
        print("No file map found in the content (extraction returned None)")
        return False

def main():
    print("File Map Extraction Test")
    print("=======================")
    
    # Test JavaScript file
    if os.path.exists(js_test_file):
        js_success = test_extraction(js_test_file)
        print(f"JavaScript test: {'SUCCESS' if js_success else 'FAILURE'}")
    else:
        print(f"JavaScript test file not found: {js_test_file}")
    
    # Test CSS file
    if os.path.exists(css_test_file):
        css_success = test_extraction(css_test_file)
        print(f"CSS test: {'SUCCESS' if css_success else 'FAILURE'}")
    else:
        print(f"CSS test file not found: {css_test_file}")

if __name__ == "__main__":
    main() 