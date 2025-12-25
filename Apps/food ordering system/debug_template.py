#!/usr/bin/env python3
"""
Template Block Analyzer - Debug Django template syntax errors
"""
import re

def analyze_template_blocks(file_path):
    """Analyze Django template blocks to find mismatches"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if_stack = []
    for i, line in enumerate(lines, 1):
        # Find Django template tags
        tags = re.findall(r'{%\s*(if|elif|else|endif|for|endfor|block|endblock)\s*.*?%}', line)
        
        for tag in tags:
            tag_type = tag.split()[0]
            
            if tag_type in ['if', 'for', 'block']:
                if_stack.append((tag_type, i))
                print(f"Line {i}: OPEN {tag_type}")
            elif tag_type in ['endif', 'endfor', 'endblock']:
                if if_stack:
                    open_tag, open_line = if_stack.pop()
                    expected_close = 'end' + open_tag
                    if tag_type != expected_close:
                        print(f"ERROR: Line {i} - Found {tag_type} but expected {expected_close} (opened at line {open_line})")
                    else:
                        print(f"Line {i}: CLOSE {tag_type} (matches {open_tag} from line {open_line})")
                else:
                    print(f"ERROR: Line {i} - Found {tag_type} with no matching open tag")
            elif tag_type in ['elif', 'else']:
                if if_stack and if_stack[-1][0] == 'if':
                    print(f"Line {i}: {tag_type} (continues if from line {if_stack[-1][1]})")
                else:
                    print(f"ERROR: Line {i} - Found {tag_type} without matching if")
    
    # Check for unclosed blocks
    if if_stack:
        print("\nUNCLOSED BLOCKS:")
        for open_tag, open_line in if_stack:
            print(f"  {open_tag} from line {open_line} was never closed")

if __name__ == "__main__":
    template_path = "d:/Project/Python/Apps/food ordering system/templates/customer/restaurant_detail.html"
    analyze_template_blocks(template_path)
