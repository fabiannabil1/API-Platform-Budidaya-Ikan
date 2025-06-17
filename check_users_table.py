#!/usr/bin/env python3
from models.db import get_connection
from psycopg2.extras import RealDictCursor

def check_users_table():
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('''
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                ''')
                columns = cur.fetchall()
                print('Users table structure:')
                for col in columns:
                    print(f'  {col["column_name"]}: {col["data_type"]}')
                
                # Also check a sample user
                cur.execute('SELECT * FROM users LIMIT 1')
                user = cur.fetchone()
                if user:
                    print('\nSample user:')
                    for key, value in user.items():
                        print(f'  {key}: {value}')
                
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    check_users_table()
