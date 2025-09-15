#!/usr/bin/env python3
"""
Fix Template Formatting Issues

This script fixes all the problematic Jinja2 template formatting syntax
that's causing Internal Server Errors.
"""

import re
from pathlib import Path

def fix_template_formatting(file_path):
    """Fix formatting issues in a template file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix common formatting patterns
    replacements = [
        # Currency formatting
        (r'\{\{ "([^"]*):,\.0f"\|format\(([^)]+)\) \}\}', r'{{ \2|round(0)|int }}'),
        (r'\$\{\{ "([^"]*):,\.0f"\|format\(([^)]+)\) \}\}', r'${{ \2|round(0)|int }}'),
        
        # Percentage formatting
        (r'\{\{ "([^"]*):\.1f"\|format\(([^)]+)\) \}\}%', r'{{ \2|round(1) }}%'),
        (r'\{\{ "([^"]*):\.2f"\|format\(([^)]+)\) \}\}%', r'{{ \2|round(2) }}%'),
        (r'\{\{ "([^"]*):\+\.1f"\|format\(([^)]+)\) \}\}%', r'{{ \2|round(1) }}%'),
        (r'\{\{ "([^"]*):\+\.2f"\|format\(([^)]+)\) \}\}%', r'{{ \2|round(2) }}%'),
        
        # Decimal formatting
        (r'\{\{ "([^"]*):,\.2f"\|format\(([^)]+)\) \}\}', r'{{ \2|round(2) }}'),
        (r'\$\{\{ "([^"]*):,\.2f"\|format\(([^)]+)\) \}\}', r'${{ \2|round(2) }}'),
        
        # Integer formatting
        (r'\{\{ "([^"]*):,\.0f"\|format\(([^)]+)\) \}\}', r'{{ \2|round(0)|int }}'),
        
        # Simple percentage
        (r'\{\{ "([^"]*)\%\.2f"\|format\(([^)]+)\) \}\}', r'{{ \2|round(2) }}'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Additional manual fixes for specific cases
    content = content.replace(
        '{{ "{:+.1f}"|format(holding.pnl_percent) }}%',
        '{{ holding.pnl_percent|round(1) }}%'
    )
    content = content.replace(
        '{{ "{:+.2f}"|format(portfolio.total_pnl_percent) }}%',
        '{{ portfolio.total_pnl_percent|round(2) }}%'
    )
    content = content.replace(
        '{{ "{:.1f}"|format(holding.market_value / portfolio.total_value * 100) }}%',
        '{{ (holding.market_value / portfolio.total_value * 100)|round(1) }}%'
    )
    content = content.replace(
        '{{ "{:.1f}"|format(analytics.avg_return) }}%',
        '{{ analytics.avg_return|round(1) }}%'
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path.name}")

def main():
    """Fix all template files."""
    templates_dir = Path(__file__).parent / "templates"
    
    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return
    
    template_files = list(templates_dir.glob("*.html"))
    
    print(f"🔧 Fixing {len(template_files)} template files...")
    
    for template_file in template_files:
        fix_template_formatting(template_file)
    
    print("✅ All template formatting issues fixed!")

if __name__ == "__main__":
    main()

