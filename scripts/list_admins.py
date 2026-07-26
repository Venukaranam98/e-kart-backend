import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

HERE = os.path.dirname(__file__)
load_dotenv(os.path.join(HERE, '..', '.env'))

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print('DATABASE_URL not set in backend/.env')
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        res = conn.execute(text("SELECT email FROM users WHERE is_admin = true;"))
    except Exception as e:
        print('Query failed:', e)
        raise

    emails = [row[0] for row in res.fetchall()]

print(f"Admins count: {len(emails)}")
for e in emails:
    print(e)
