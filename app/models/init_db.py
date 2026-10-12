from app.models.database import Base,engine
from sqlalchemy import text
# Import models so SQLAlchemy knows about them
from app.models import Website,DocumentChunk

def init_database()-> None:
    """Enable the pgvector extension and create the application's tables."""

     # Connect and run the raw DDL command to enable pgvector first
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database()
    print("Database table created successfully.")
