# File: check_online_features.py
from feast import FeatureStore
import pandas as pd
import json

# Initialize the feature store
store = FeatureStore(repo_path="./feature_repo_local")

# Example entity rows - use the same IDs you're trying in your API
entity_rows = [
    {"loan_id": "L12713", "customer_id": "C5380"}
]

# Define the feature references
feature_refs = [
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
    "static_loan_features:urban_rural"
]

# Try to retrieve the features
print(f"Attempting to retrieve features for {entity_rows}")
try:
    online_features = store.get_online_features(
        entity_rows=entity_rows,
        features=feature_refs
    )
    
    # Print the result as a dictionary
    result_dict = online_features.to_dict()
    print("\nFeatures as dictionary:")
    print(json.dumps(result_dict, indent=2, default=str))
    
    # Print column names in DataFrame format
    result_df = online_features.to_df()
    print("\nColumns in DataFrame format:")
    print(result_df.columns.tolist())
    
    # Check if features exist
    if result_df['loan_id'][0] is None:
        print("\nWARNING: No features found for this entity ID!")
    else:
        print("\nFeatures successfully retrieved!")
        print(result_df.head())
        
except Exception as e:
    print(f"Error retrieving features: {str(e)}")