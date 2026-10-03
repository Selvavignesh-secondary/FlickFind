import database
import models

print("Dropping existing tables...")
models.Base.metadata.drop_all(bind=database.engine)

print("Creating fresh tables...")
models.Base.metadata.create_all(bind=database.engine)

print("Database reset complete.")