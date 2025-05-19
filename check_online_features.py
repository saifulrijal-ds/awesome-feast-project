# File: check_online_features.py
from feast import FeatureStore
import pandas as pd
import json
import requests

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

# Try to retrieve the features using Python SDK
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

# Now let's also check using the HTTP API endpoint
print("\n\n=== Checking features via HTTP API ===")

# Extract just the feature names without the view prefix for HTTP request
feature_names = [ref.split(":")[-1] for ref in feature_refs]
feature_views = list(set([ref.split(":")[0] for ref in feature_refs]))

# Prepare request payload for HTTP API
http_payload = {
    "features": feature_refs,
    "entities": {
        "loan_id": [entity_rows[0]["loan_id"]],
        "customer_id": [entity_rows[0]["customer_id"]]
    }
}

# Make the HTTP request
try:
    print("Sending HTTP request to Feast Feature Server...")
    print(f"Request payload: {json.dumps(http_payload, indent=2)}")
    
    http_response = requests.post(
        "http://localhost:6566/get-online-features",
        json=http_payload
    )
    
    if http_response.status_code == 200:
        http_result = http_response.json()
        print("\nHTTP API Response:")
        print(json.dumps(http_result, indent=2))
        
        # Check if we got features back
        if "results" in http_result and len(http_result["results"]) > 0:
            print("\nFeatures successfully retrieved via HTTP API!")
        else:
            print("\nWARNING: No features found via HTTP API!")
    else:
        print(f"\nError from HTTP API: {http_response.status_code} - {http_response.text}")
    
except Exception as e:
    print(f"Error with HTTP request: {str(e)}")

# Print a comparison if both methods returned results
print("\n=== Comparison between SDK and HTTP API results ===")
print("If both methods worked, they should return the same feature values.")