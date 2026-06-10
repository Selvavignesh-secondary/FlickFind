import database
import models

print("🗑️ Dropping outdated database tables...")
models.Base.metadata.drop_all(bind=database.engine)

print("🏗️ Creating fresh, optimized database layout...")
models.Base.metadata.create_all(bind=database.engine)

print("🏆 Database schemas reset and synced successfully!")