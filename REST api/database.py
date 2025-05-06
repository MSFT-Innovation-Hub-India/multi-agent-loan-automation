from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from azure.identity import DefaultAzureCredential
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure SQL details
SERVER = os.getenv("AZURE_SQL_SERVER", "loansrvr.database.windows.net")
DATABASE = os.getenv("AZURE_SQL_DATABASE", "LoanDB")

# Create connection string
connection_string = (
    f"mssql+pyodbc:///?odbc_connect="
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{SERVER},1433;"
    f"Database={DATABASE};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=30;"
    f"Authentication=ActiveDirectoryInteractive;"
    f"UID={os.getenv('AZURE_SQL_USER', 'jyothikakoppula11@jyothikakoppula11gmail.onmicrosoft.com')}"
)

# Create SQLAlchemy engine
engine = create_engine(
    connection_string,
    echo=True  # Set to False in production
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()
