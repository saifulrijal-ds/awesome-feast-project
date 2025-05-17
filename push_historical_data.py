# File: push_historical_data.py
import pandas as pd
from feast import FeatureStore
from datetime import datetime

# Initialize your feature store
store = FeatureStore(repo_path="./feature_repo_local")  # Make sure this points to your Feast repo directory

# Load your historical data
# Option 1: If you have a CSV file
# df = pd.read_csv('bfi_loan_complete_training_data.csv')

# Option 2: If you need to query from a database
# Replace with appropriate connection details for your database
# from sqlalchemy import create_engine
# engine = create_engine('postgresql://feast_user:feast_password@localhost:5432/feast')
# df = pd.read_sql('''
#     SELECT * FROM bfi_static_loan_data 
#     WHERE event_timestamp BETWEEN '2023-01-01' AND '2024-01-01'
# ''', engine)

sql_query = """
    SELECT
        loan_id, -- Define all enity
        customer_id, -- Define all entity
        event_timestamp 
    FROM 
        bfi_static_loan_data 
    WHERE 
        event_timestamp BETWEEN '2023-01-01' AND '2024-10-01'
"""

# Retrieve all features from the updated static_loan_features view
# Note that we're now including the new fields we added
df = store.get_historical_features(
    entity_df=sql_query,
    features=[
        # Original features
        "static_loan_features:loan_amount",
        "static_loan_features:interest_rate",
        "static_loan_features:loan_term",
        "static_loan_features:product_type",
        "static_loan_features:collateral_value",
        "static_loan_features:ltv_ratio",
        "static_loan_features:credit_score",
        "static_loan_features:monthly_income",
        "static_loan_features:dti_ratio",
        "static_loan_features:age",
        "static_loan_features:employment_years",
        "static_loan_features:province",
        "static_loan_features:urban_rural",
        
        # Newly added features
        "static_loan_features:origination_date",
        "static_loan_features:time_to_event",
        "static_loan_features:default_flag",
        "static_loan_features:observed"
    ],
).to_df()

# Ensure event_timestamp is in datetime format
if 'event_timestamp' not in df.columns:
    if 'origination_date' in df.columns:
        df['event_timestamp'] = pd.to_datetime(df['origination_date'])
    else:
        print("Warning: No timestamp column found. Adding current timestamp.")
        df['event_timestamp'] = datetime.now()
elif not pd.api.types.is_datetime64_any_dtype(df['event_timestamp']):
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])

# Make sure created_timestamp exists if required by your configuration
if 'created_timestamp' not in df.columns:
    df['created_timestamp'] = df['event_timestamp']

# Keep only the necessary columns for your feature view
feature_columns = [
    'loan_id', 'customer_id', 'event_timestamp',
    'loan_amount', 'interest_rate', 'loan_term', 'product_type',
    'collateral_value', 'ltv_ratio', 'credit_score', 'monthly_income',
    'dti_ratio', 'age', 'employment_years', 'province', 'urban_rural'
]

# Check if all required columns exist
missing_columns = [col for col in feature_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Select only the needed columns
df_to_push = df[feature_columns]

# Push data to the offline store
print(f"Pushing {len(df_to_push)} records to the feature store...")
store.push("loan_features_source", df_to_push)  # Use your feature view name

print("Data pushed successfully to the feature store")