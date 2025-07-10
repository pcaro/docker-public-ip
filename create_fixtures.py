#!/usr/bin/env python3
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# IP services list
services = [
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
    "https://ipinfo.io/ip",
    "https://wtfismyip.com/text",
    "https://api.ipify.org",
    "https://ifconfig.io/ip",
    "https://www.moanmyip.com/simple",
    "https://ifconfig.co/ip",
    "https://ifconfig.me/ip",
    "https://ipecho.net/plain",
]

# Sample IPs to simulate changes
sample_ips = [
    "192.168.1.100",
    "10.0.0.50",
    "172.16.0.25",
    "192.168.1.100",  # Repeat to simulate stable periods
    "203.0.113.45",
    "198.51.100.78",
    "203.0.113.45",  # Repeat
]


def create_fixtures(db_path="data/ip_history.db"):
    # Create directory if it doesn't exist
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ip_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            service TEXT NOT NULL,
            ip_address TEXT,
            response_time_ms REAL,
            success BOOLEAN DEFAULT 1,
            error_message TEXT
        )
    """)
    
    # Create indexes
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON ip_checks (timestamp DESC)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ip_address 
        ON ip_checks (ip_address)
    """)
    
    # Clear existing data
    conn.execute("DELETE FROM ip_checks")
    
    # Generate data for the last 7 days
    current_time = datetime.now()
    start_time = current_time - timedelta(days=7)
    
    # Current IP for continuity
    current_ip_index = 0
    current_ip = sample_ips[current_ip_index]
    
    # Generate checks
    check_time = start_time
    check_count = 0
    
    while check_time < current_time:
        # Randomly change IP occasionally (about every 12-48 hours)
        if random.random() < 0.002:  # ~0.2% chance per check
            current_ip_index = (current_ip_index + 1) % len(sample_ips)
            current_ip = sample_ips[current_ip_index]
            print(f"IP changed to {current_ip} at {check_time}")
        
        # Select random service
        service = random.choice(services)
        
        # Simulate success/failure (95% success rate)
        success = random.random() < 0.95
        
        if success:
            # Generate realistic response times
            base_time = {
                "https://icanhazip.com": 150,
                "https://checkip.amazonaws.com": 350,
                "https://ipinfo.io/ip": 270,
                "https://wtfismyip.com/text": 350,
                "https://api.ipify.org": 330,
                "https://ifconfig.io/ip": 370,
                "https://www.moanmyip.com/simple": 680,
                "https://ifconfig.co/ip": 220,
                "https://ifconfig.me/ip": 310,
                "https://ipecho.net/plain": 310,
            }
            
            # Add some variance
            response_time = base_time.get(service, 300) + random.randint(-50, 100)
            
            conn.execute(
                """
                INSERT INTO ip_checks 
                (timestamp, service, ip_address, response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (check_time, service, current_ip, response_time, 1, None),
            )
        else:
            # Simulate various errors
            errors = [
                "Connection timeout",
                "HTTP 503",
                "HTTP 500",
                "Connection refused",
            ]
            error = random.choice(errors)
            
            conn.execute(
                """
                INSERT INTO ip_checks 
                (timestamp, service, ip_address, response_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (check_time, service, None, None, 0, error),
            )
        
        check_count += 1
        
        # Progress indicator
        if check_count % 1000 == 0:
            print(f"Generated {check_count} checks...")
        
        # Advance time by 30 seconds (default check interval)
        check_time += timedelta(seconds=30)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\nCreated {check_count} fixture records in {db_path}")
    print(f"Time range: {start_time} to {current_time}")
    print(f"Current IP: {current_ip}")


if __name__ == "__main__":
    create_fixtures()
    print("\nFixtures created successfully!")
    print("You can now run the service and access http://localhost:8080 to see the data.")