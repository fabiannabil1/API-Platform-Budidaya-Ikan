#!/usr/bin/env python3
"""
Database migration script to create role_change_requests table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import get_connection
from psycopg2.extras import RealDictCursor

def create_role_change_table():
    """Create the role_change_requests table if it doesn't exist"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'role_change_requests'
                    );
                """)
                exists = cur.fetchone()['exists']
                
                if not exists:
                    print('Creating role_change_requests table...')
                    # Create the table
                    cur.execute("""
                        CREATE TABLE role_change_requests (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES users(id),
                            reason TEXT,
                            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            processed_at TIMESTAMP,
                            processed_by INTEGER REFERENCES users(id),
                            rejection_reason TEXT
                        );
                    """)
                    
                    # Create indexes for better performance
                    cur.execute("""
                        CREATE INDEX idx_role_change_requests_user_id ON role_change_requests(user_id);
                        CREATE INDEX idx_role_change_requests_status ON role_change_requests(status);
                    """)
                    
                    conn.commit()
                    print('✅ Table created successfully!')
                else:
                    print('✅ Table already exists')
                    
                # Verify table structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'role_change_requests'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print('\nTable structure:')
                for col in columns:
                    print(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
                    
    except Exception as e:
        print(f'❌ Error: {e}')
        return False
    
    return True

if __name__ == '__main__':
    print('🚀 Starting database migration...')
    success = create_role_change_table()
    if success:
        print('✅ Migration completed successfully!')
    else:
        print('❌ Migration failed!')
        sys.exit(1)
