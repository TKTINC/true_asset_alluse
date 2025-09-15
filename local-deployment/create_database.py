#!/usr/bin/env python3
"""
Database Initialization Script for True-Asset-ALLUSE

Creates the SQLite database and populates it with sample portfolio data.
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """Create the database and populate with sample data."""
    
    # Create database directory
    db_dir = Path(__file__).parent.parent / "database"
    db_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = db_dir / "true_asset_alluse.db"
    
    print(f"🗄️  Creating database at: {db_path}")
    
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create portfolio table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_price REAL NOT NULL,
            current_price REAL NOT NULL,
            market_value REAL NOT NULL,
            pnl REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM portfolio")
    
    # Sample portfolio data - high-performing tech stocks
    portfolio_data = [
        ("GOOGL", 50, 2800.00, 3100.00, 155000, 15000),
        ("NVDA", 100, 450.00, 520.00, 52000, 7000),
        ("TSLA", 80, 250.00, 290.00, 23200, 3200),
        ("AAPL", 200, 180.00, 195.00, 39000, 3000),
        ("MSFT", 150, 350.00, 380.00, 57000, 4500),
        ("AMZN", 30, 3200.00, 3400.00, 102000, 6000),
        ("META", 60, 320.00, 350.00, 21000, 1800),
        ("NFLX", 40, 400.00, 450.00, 18000, 2000),
        ("AMD", 120, 100.00, 115.00, 13800, 1800),
        ("CRM", 50, 220.00, 240.00, 12000, 1000),
        ("ADBE", 25, 480.00, 520.00, 13000, 1000),
        ("PYPL", 80, 75.00, 85.00, 6800, 800),
        ("INTC", 200, 45.00, 50.00, 10000, 1000),
        ("QCOM", 70, 140.00, 155.00, 10850, 1050),
        ("BABA", 90, 90.00, 95.00, 8550, 450),
        ("UBER", 100, 45.00, 52.00, 5200, 700),
        ("SNAP", 150, 12.00, 15.00, 2250, 450),
        ("TWTR", 80, 35.00, 40.00, 3200, 400),
        ("SPOT", 30, 150.00, 170.00, 5100, 600),
        ("ZM", 40, 120.00, 135.00, 5400, 600)
    ]
    
    # Insert sample data
    cursor.executemany("""
        INSERT INTO portfolio (symbol, quantity, avg_price, current_price, market_value, pnl)
        VALUES (?, ?, ?, ?, ?, ?)
    """, portfolio_data)
    
    # Commit changes
    conn.commit()
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM portfolio")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(market_value), SUM(pnl) FROM portfolio")
    total_value, total_pnl = cursor.fetchone()
    
    print(f"✅ Database created successfully!")
    print(f"📊 Portfolio entries: {count}")
    print(f"💰 Total portfolio value: ${total_value:,.0f}")
    print(f"📈 Total P&L: ${total_pnl:,.0f}")
    print(f"📍 Database location: {db_path}")
    
    conn.close()
    return str(db_path)

if __name__ == "__main__":
    create_database()

