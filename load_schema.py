

import mysql.connector

conn = mysql.connector.connect(
    host='mysql-alserhan-alserhandbproject.g.aivencloud.com',
    port=15800,
    user='avnadmin',
    password='AVNS_O1WacK-MiRUfuesTzN5',
    database='defaultdb',
    use_pure=True,
    ssl_disabled=False,
)

cursor = conn.cursor()

# First, drop any tables that may have been partially created
print("Cleaning up existing tables...")
for table in ['REWARD', 'TICKET', 'CONCERT', 'CUSTOMER', 'ARTIST']:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"  Dropped {table}")
    except Exception as e:
        print(f"  {table}: {e}")
conn.commit()

# Now load schema fresh
with open('schema.sql', 'r') as f:
    sql_content = f.read()

statements = [s.strip() for s in sql_content.split(';') if s.strip()]

success = 0
fail = 0
for i, stmt in enumerate(statements):
    try:
        cursor.execute(stmt)
        # Drain any results to prevent "Unread result found"
        try:
            cursor.fetchall()
        except:
            pass
        conn.commit()
        success += 1
    except Exception as e:
        print(f"FAIL ({i+1}): {stmt[:60]}... -> {e}")
        fail += 1

print(f"\nSuccess: {success}, Failed: {fail}")

cursor.close()
conn.close()
print("Done!")
