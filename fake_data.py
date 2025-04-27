import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from dotenv import load_dotenv
import anyio
import os

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")

# --- Configuration ---
# Replace with your PostgreSQL database connection details
DATABASE_URI = f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}'
TABLE_NAME = 'transactions'
NUM_RECORDS = 1000  # Number of sample transactions to generate

# --- SQLAlchemy Model Definition ---
Base = declarative_base()

class Transaction(Base):
    __tablename__ = TABLE_NAME

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    customer_id = Column(Integer, nullable=True)
    # Added user_name column
    user_name = Column(String, nullable=True)

# --- Data Generation ---
fake = Faker()

def generate_fake_transaction():
    """Generates a single fake transaction record with a user name if customer_id is present."""
    customer_id = random.randint(1000, 9999) if random.random() > 0.1 else None # Optional customer_id

    transaction_data = {
        'product': fake.word().capitalize() + ' Gadget', # Changed slightly for variety
        'quantity': random.randint(1, 10),
        'price': round(random.uniform(5.0, 150.0), 2), # Changed price range slightly
        'timestamp': fake.date_time_between(start_date='-1y', end_date='now'),
        'customer_id': customer_id,
    }

    # Add user_name only if customer_id is not None
    if customer_id is not None:
        transaction_data['user_name'] = fake.name()
    else:
        transaction_data['user_name'] = None # Ensure user_name is None if customer_id is None

    return transaction_data

# --- Database Operations ---
def create_transactions_table(engine):
    """Creates the transactions table if it doesn't exist."""
    Base.metadata.create_all(engine, checkfirst=True)
    print(f"Table '{TABLE_NAME}' checked/created successfully.")

def insert_sample_data(engine, num_records):
    """Generates and inserts sample data into the transactions table."""
    print(f"Generating {num_records} sample transactions...")
    sample_data = [generate_fake_transaction() for _ in range(num_records)]
    print("Sample data generated.")

    with engine.connect() as connection:
        # Use bulk_insert_mappings for efficient insertion of dictionaries
        connection.execute(Transaction.__table__.insert(), sample_data)
        connection.commit()
    print(f"Successfully inserted {num_records} records into '{TABLE_NAME}'.")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URI)

        # Create table (will add the user_name column if the table exists and column is new)
        create_transactions_table(engine)

        # Insert sample data
        insert_sample_data(engine, NUM_RECORDS)

        print("Sample data generation and insertion complete.")

    except Exception as e:
        print(f"An error occurred: {e}")