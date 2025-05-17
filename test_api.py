# File: test_api.py
import requests
import json
import pandas as pd

# API endpoint
API_URL = "http://localhost:8001"

def test_single_prediction():
    """Test prediction for a single loan"""
    # Example loan data
    loan_data = {
        "loan_id": "L12345",
        "customer_id": "C67890",
        "loan_amount": 150000,
        "interest_rate": 0.08,
        "loan_term": 36,
        "product_type": "Car",
        "collateral_value": 180000,
        "ltv_ratio": 0.83,
        "credit_score": 720,
        "monthly_income": 7500,
        "dti_ratio": 0.32,
        "age": 35,
        "employment_years": 8.5,
        "province": "Jakarta",
        "urban_rural": "Urban"
    }
    
    # Make the request
    response = requests.post(f"{API_URL}/predict", json=loan_data)
    
    # Print the results
    if response.status_code == 200:
        result = response.json()
        print("Single Prediction Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_batch_prediction(data_path):
    """Test prediction for multiple loans"""
    # Load some sample data
    df = pd.read_csv(data_path)
    
    # Take just a few rows for testing
    sample_df = df.head(3)
    
    # Prepare the request payload
    loans = []
    for _, row in sample_df.iterrows():
        loan_dict = {
            "loan_id": str(row['loan_id']),
            "customer_id": str(row['customer_id']),
            "loan_amount": int(row['loan_amount']),
            "interest_rate": float(row['interest_rate']),
            "loan_term": int(row['loan_term']),
            "product_type": str(row['product_type']),
            "collateral_value": int(row['collateral_value']),
            "ltv_ratio": float(row['ltv_ratio']),
            "credit_score": int(row['credit_score']),
            "monthly_income": int(row['monthly_income']),
            "dti_ratio": float(row['dti_ratio']),
            "age": int(row['age']),
            "employment_years": float(row['employment_years']),
            "province": str(row['province']),
            "urban_rural": str(row['urban_rural'])
        }
        loans.append(loan_dict)
    
    # Make the request
    response = requests.post(f"{API_URL}/predict/batch", json={"loans": loans})
    
    # Print the results
    if response.status_code == 200:
        result = response.json()
        print("\nBatch Prediction Results:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Update this path to your sample data
    DATA_PATH = "notebooks/bfi_loan_complete_training_data.csv"
    
    # Run the tests
    test_single_prediction()
    test_batch_prediction(DATA_PATH)