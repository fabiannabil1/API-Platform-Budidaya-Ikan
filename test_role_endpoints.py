#!/usr/bin/env python3
"""
Test script for role change endpoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_connection
from psycopg2.extras import RealDictCursor

def test_role_requests_query():
    """Test the role requests query"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Test query that matches the one in change_role_routes.py
                cur.execute('''
                    SELECT r.*, u.name, u.phone
                    FROM role_change_requests r
                    JOIN users u ON r.user_id = u.id
                    ORDER BY r.requested_at DESC
                ''')
                requests = cur.fetchall()
                print(f'✅ Found {len(requests)} role change requests')
                
                if len(requests) == 0:
                    print('ℹ️  No requests found - this is normal for a new installation')
                else:
                    for req in requests:
                        print(f'  Request {req["id"]}: {req["name"]} - {req["status"]}')
                        
                return True
                        
    except Exception as e:
        print(f'❌ Error testing query: {e}')
        return False

def test_users_table():
    """Test if users table exists and has data"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT COUNT(*) as count FROM users')
                result = cur.fetchone()
                print(f'✅ Users table has {result["count"]} users')
                return True
    except Exception as e:
        print(f'❌ Error accessing users table: {e}')
        return False

if __name__ == '__main__':
    print('🧪 Testing role change endpoints...')
    
    # Test users table first
    if not test_users_table():
        print('❌ Cannot proceed without users table')
        sys.exit(1)
    
    # Test role requests query
    if not test_role_requests_query():
        print('❌ Role requests query failed')
        sys.exit(1)
    
    print('✅ All tests passed!')
