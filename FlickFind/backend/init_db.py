import database
import models

def initialize_database():
    print("🗄️ [Database] Connecting to Docker PostgreSQL container...")
    try:
        database.Base.metadata.create_all(bind=database.engine)
        print("✅ [Database] Table structures created and synchronized successfully!")
    except Exception as e:
        print(f"❌ [Database] Connection failed: {e}")

if __name__ == "__main__":
    initialize_database()