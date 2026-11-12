import os, sys
sys.path.insert(0, '.')
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
from sqlalchemy import create_engine, text

e = create_engine(os.getenv('DATABASE_URL'), connect_args={"connect_timeout": 10})
with e.connect() as c:
    existe = c.execute(text("SHOW COLUMNS FROM responsaveis LIKE 'senha_hash'")).first()
    if existe:
        print('Coluna ja existe.')
    else:
        c.execute(text('ALTER TABLE responsaveis ADD COLUMN senha_hash BLOB NULL'))
        c.commit()
        print('Coluna adicionada.')
