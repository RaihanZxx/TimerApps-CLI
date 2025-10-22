#!/usr/bin/env python3
"""Test parsing logic for mCurrentFocus output."""

import re

def test_package_extraction():
    """Test extracting package from mCurrentFocus output."""
    
    test_cases = [
        # Format: (input_line, expected_output)
        ("  mCurrentFocus=Window{abc123u0 com.instagram.android/com.instagram.activity.MainActivity}", "com.instagram.android"),
        ("  mCurrentFocus=Window{xyz789u0 com.facebook.android/com.facebook.MainActivity}", "com.facebook.android"),
        ("  mCurrentFocus=Window{def456u0 com.whatsapp/com.whatsapp.MainActivity}", "com.whatsapp"),
        ("  mCurrentFocus=Window{ghi789u0 com.tiktok.android/com.tiktok.MainActivity}", "com.tiktok.android"),
        # With extra spaces
        ("  mCurrentFocus=Window{abc123u0 com.instagram.android/com.instagram.activity.MainActivity extra}", "com.instagram.android"),
    ]
    
    print("Testing package extraction from mCurrentFocus output:\n")
    
    for test_input, expected in test_cases:
        print(f"Input:    {test_input}")
        
        # Method 1: Regex
        match = re.search(r"(com\.[a-zA-Z0-9._]+)", test_input)
        if match:
            result = match.group(1)
        else:
            result = None
        
        # Method 2: Fallback
        if not result and "u0 " in test_input:
            try:
                parts = test_input.split("u0 ")
                if len(parts) > 1:
                    result = parts[1].split("/")[0].split(" ")[0]
            except:
                result = None
        
        print(f"Expected: {expected}")
        print(f"Got:      {result}")
        
        if result == expected:
            print("✓ PASS\n")
        else:
            print("✗ FAIL\n")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Package Extraction Parser Test")
    print("=" * 60)
    print()
    
    if test_package_extraction():
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
