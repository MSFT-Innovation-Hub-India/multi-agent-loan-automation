from database import engine
import models

print("Dropping all existing tables...")
models.Base.metadata.drop_all(bind=engine)
print("Creating new tables with updated schema...")
models.Base.metadata.create_all(bind=engine)
print("Database tables recreated successfully!")
