# File: materialize_features.py
import pandas as pd
from feast import FeatureStore
from datetime import datetime, timedelta
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize your feature store
logger.info("Initializing feature store")
store = FeatureStore(repo_path="./feature_repo_local")  # Update to your repository path

# Define the time range for materialization
# Start date should be the earliest date you want to include 
start_date = datetime(2023, 10, 1)

# End date is typically current time or slightly in the past
# It's the point in time up to which data will be materialized
end_date = datetime.now()

logger.info(f"Materializing features from {start_date} to {end_date}")

# Execute the materialization
try:
    # The materialize method reads from your PostgreSQL source and writes to Redis
    store.materialize(
        start_date=start_date,
        end_date=end_date
    )
    logger.info("Materialization completed successfully")
except Exception as e:
    logger.error(f"Materialization failed: {str(e)}")
    raise