#!/usr/bin/env python3
"""
Comprehensive Template Fix Script

Fixes all Jinja2 template formatting issues by replacing problematic
format() calls with simple Jinja2 filters.
"""

from pathlib import Path

def fix_template_file(file_path):
    """Fix all formatting issues in a template file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace all problematic format patterns
    replacements = [
        # Currency with commas
        ('{{ "{:,.0f}"|format(portfolio.total_value) }}', '{{ portfolio.total_value|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(portfolio.total_pnl) }}', '{{ portfolio.total_pnl|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(holding.quantity) }}', '{{ holding.quantity|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(holding.market_value) }}', '{{ holding.market_value|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(holding.pnl) }}', '{{ holding.pnl|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(analytics.total_invested) }}', '{{ analytics.total_invested|round(0)|int }}'),
        ('{{ "{:,.0f}"|format(analytics.best_performer.pnl) }}', '{{ analytics.best_performer.pnl|round(0)|int }}'),
        
        # Currency with decimals
        ('{{ "{:,.2f}"|format(holding.avg_price) }}', '{{ holding.avg_price|round(2) }}'),
        ('{{ "{:,.2f}"|format(holding.current_price) }}', '{{ holding.current_price|round(2) }}'),
        
        # Percentages
        ('{{ "{:+.1f}"|format(holding.pnl_percent) }}', '{{ holding.pnl_percent|round(1) }}'),
        ('{{ "{:+.1f}"|format(portfolio.total_pnl_percent) }}', '{{ portfolio.total_pnl_percent|round(1) }}'),
        ('{{ "{:+.2f}"|format(portfolio.total_pnl_percent) }}', '{{ portfolio.total_pnl_percent|round(2) }}'),
        ('{{ "{:+.1f}"|format(analytics.best_performer.pnl_percent) }}', '{{ analytics.best_performer.pnl_percent|round(1) }}'),
        ('{{ "{:.1f}"|format(holding.market_value / portfolio.total_value * 100) }}', '{{ (holding.market_value / portfolio.total_value * 100)|round(1) }}'),
        ('{{ "{:.1f}"|format(analytics.avg_return) }}', '{{ analytics.avg_return|round(1) }}'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Additional fixes for $ prefixed values
    content = content.replace('${{ "{:,.0f}"|format(portfolio.total_value) }}', '${{ portfolio.total_value|round(0)|int }}')
    content = content.replace('${{ "{:,.0f}"|format(portfolio.total_pnl) }}', '${{ portfolio.total_pnl|round(0)|int }}')
    content = content.replace('${{ "{:,.0f}"|format(holding.market_value) }}', '${{ holding.market_value|round(0)|int }}')
    content = content.replace('${{ "{:,.0f}"|format(holding.pnl) }}', '${{ holding.pnl|round(0)|int }}')
    content = content.replace('${{ "{:,.0f}"|format(analytics.total_invested) }}', '${{ analytics.total_invested|round(0)|int }}')
    content = content.replace('${{ "{:,.0f}"|format(analytics.best_performer.pnl) }}', '${{ analytics.best_performer.pnl|round(0)|int }}')
    content = content.replace('${{ "{:,.2f}"|format(holding.avg_price) }}', '${{ holding.avg_price|round(2) }}')
    content = content.replace('${{ "{:,.2f}"|format(holding.current_price) }}', '${{ holding.current_price|round(2) }}')
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path.name}")

def main():
    """Fix all template files."""
    templates_dir = Path(__file__).parent / "templates"
    
    template_files = [
        templates_dir / "landing.html",
        templates_dir / "dashboard.html", 
        templates_dir / "portfolio.html",
        templates_dir / "analytics.html"
    ]
    
    print("🔧 Fixing all template formatting issues...")
    
    for template_file in template_files:
        if template_file.exists():
            fix_template_file(template_file)
    
    print("✅ All template formatting issues fixed!")

if __name__ == "__main__":
    main()

