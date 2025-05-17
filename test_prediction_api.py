# File: test_prediction_api.py
import requests
import json
import pandas as pd
import random
from datetime import datetime

# API endpoint
API_URL = "http://localhost:8001"

def test_health():
    """Test the health check endpoint"""
    response = requests.get(f"{API_URL}/health")
    print(f"Health check status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")

def test_single_prediction():
    """Test prediction for a single loan"""
    # Replace with an actual loan_id and customer_id from your data
    loan_data = {
        "loan_id": "L12713",
        "customer_id": "C5380"
    }
    
    print(f"\nTesting single prediction for loan_id={loan_data['loan_id']}")
    
    # Make the request
    response = requests.post(f"{API_URL}/predict", json=loan_data)
    
    # Parse the response
    if response.status_code == 200:
        result = response.json()
        print("Prediction successful!")
        print(f"Risk score: {result['risk_score']:.2f}")
        print(f"12-month default probability: {result['default_prob_12m']:.2%}")
        print(f"24-month default probability: {result['default_prob_24m']:.2%}")
        
        # Print some of the features used for the prediction
        print("\nKey features used:")
        features = result.get("feature_values", {})
        for key in ["credit_score", "ltv_ratio", "interest_rate", "dti_ratio"]:
            if key in features:
                print(f"  {key}: {features[key]}")
        
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_batch_prediction():
    """Test prediction for multiple loans"""
    # Replace with actual loan_ids and customer_ids from your data
    loans = [
        {"loan_id": "L13669", "customer_id": "C9761"},
        {"loan_id": "L14012", "customer_id": "C4624"},
        {"loan_id": "L13463", "customer_id": "C8478"}
    ]
    	
    print(f"\nTesting batch prediction for {len(loans)} loans")
    
    # Make the request
    response = requests.post(f"{API_URL}/predict/batch", json={"loans": loans})
    
    # Parse the response
    if response.status_code == 200:
        results = response.json()
        print(f"Batch prediction successful! Got results for {len(results)} loans")
        
        # Print summary statistics
        risk_scores = [result["risk_score"] for result in results]
        default_probs = [result["default_prob_12m"] for result in results]
        
        print("\nSummary statistics:")
        print(f"Average risk score: {sum(risk_scores)/len(risk_scores):.2f}")
        print(f"Average 12-month default probability: {sum(default_probs)/len(default_probs):.2%}")
        print(f"Min risk score: {min(risk_scores):.2f}")
        print(f"Max risk score: {max(risk_scores):.2f}")
        
        # Print individual results
        print("\nIndividual predictions:")
        for i, result in enumerate(results):
            print(f"\nLoan {i+1} (ID: {result['loan_id']}):")
            print(f"  Risk score: {result['risk_score']:.2f}")
            print(f"  12-month default probability: {result['default_prob_12m']:.2%}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_health()
    test_single_prediction()
    test_batch_prediction()