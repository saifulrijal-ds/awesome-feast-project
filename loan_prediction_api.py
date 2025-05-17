# File: loan_prediction_api.py
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from feast import FeatureStore
import uvicorn
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Loan Default Prediction API")

# Configure paths
REPO_PATH = os.environ.get("FEAST_REPO_PATH", "./feature_repo_local")
MODEL_PATH = os.environ.get("MODEL_PATH", "./models/rsf_pipeline.pkl")

# Load the trained model
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    raise

# Initialize the feature store connection
try:
    store = FeatureStore(repo_path=REPO_PATH)
    logger.info(f"Feature store initialized with repo at {REPO_PATH}")
except Exception as e:
    logger.error(f"Failed to initialize feature store: {str(e)}")
    raise

# Define request/response models
class LoanEntity(BaseModel):
    loan_id: str
    customer_id: str

class BatchPredictionRequest(BaseModel):
    loans: List[LoanEntity]

class PredictionResponse(BaseModel):
    loan_id: str
    risk_score: float
    survival_prob_6m: float
    default_prob_6m: float
    survival_prob_12m: float
    default_prob_12m: float
    survival_prob_24m: float
    default_prob_24m: float
    survival_prob_36m: float
    default_prob_36m: float
    feature_values: Optional[Dict[str, Any]] = None

# Helper function to get features and make predictions
def predict_with_online_features(entity_rows):
    """
    Retrieves features from Feast online store and makes predictions
    
    Args:
        entity_rows: List of entity dictionaries with loan_id and customer_id
        
    Returns:
        List of prediction dictionaries with risk scores and probabilities
    """
    try:
        # Define the feature references to retrieve
        # feature_refs = [
        #     "static_loan_features:loan_amount",
        #     "static_loan_features:interest_rate",
        #     "static_loan_features:loan_term",
        #     "static_loan_features:product_type",
        #     "static_loan_features:collateral_value",
        #     "static_loan_features:ltv_ratio",
        #     "static_loan_features:credit_score",
        #     "static_loan_features:monthly_income",
        #     "static_loan_features:dti_ratio",
        #     "static_loan_features:age",
        #     "static_loan_features:employment_years",
        #     "static_loan_features:province",
        #     "static_loan_features:urban_rural"
        # ]

        feature_refs = store.get_feature_service("loan_prediction_service")
        
        # Retrieve features from online store
        logger.info(f"Retrieving features for {len(entity_rows)} loans")
        online_features = store.get_online_features(
            entity_rows=entity_rows,
            features=feature_refs
        ).to_dict()

        # Extract just the feature names (without prefixes)
        # feature_names = [ref.split(":")[-1] for ref in feature_refs]
        feature_names = [name for name in online_features.keys() 
                        if name not in ['loan_id', 'customer_id']]
        
        # Convert to DataFrame for prediction
        features_df = pd.DataFrame(online_features)
        
        # Check if we have complete feature data
        missing_entities = features_df[features_df['loan_id'].isna()]['loan_id'].count()
        if missing_entities > 0:
            logger.warning(f"Missing feature data for {missing_entities} entities")
        
        # Make predictions with the model using feature names without prefixes
        logger.info("Making predictions with the model")
        
        # Get risk scores
        risk_scores = model.predict(features_df[feature_names])
        
        # Get the RSF model from the pipeline
        rsf_model = model.named_steps['rsf']
        
        # Get survival functions - use feature names without prefixes
        X_transformed = model.named_steps['preprocessor'].transform(features_df[feature_names])
        survival_funcs = rsf_model.predict_survival_function(X_transformed)
        
        # Time points for prediction
        time_points = [6, 12, 24, 36]
        
        # Prepare results
        results = []
        for i, (loan_id, customer_id) in enumerate(zip(online_features['loan_id'], online_features['customer_id'])):
            if loan_id is None:  # Skip if no features found
                logger.warning(f"No features found for entity at index {i}")
                continue
                
            # Create result dictionary
            result = {
                "loan_id": loan_id,
                "risk_score": float(risk_scores[i])
            }
            
            # Add survival probabilities
            for t in time_points:
                surv_prob = float(survival_funcs[i](t))
                result[f"survival_prob_{t}m"] = surv_prob
                result[f"default_prob_{t}m"] = 1.0 - surv_prob
            
            # FIXED: Correctly access feature values using feature names
            result["feature_values"] = {
                feature_name: online_features[feature_name][i]
                for feature_name in feature_names
            }
            
            results.append(result)
            
        return results
    
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise

# Define API endpoints
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "feast_connection": "active"}

@app.post("/predict", response_model=PredictionResponse)
async def predict_single(loan: LoanEntity):
    """
    Predict default risk for a single loan using features from online store
    """
    try:
        # Create entity row
        entity_row = [{"loan_id": loan.loan_id, "customer_id": loan.customer_id}]
        
        # Get predictions
        predictions = predict_with_online_features(entity_row)
        
        if not predictions:
            raise HTTPException(
                status_code=404, 
                detail=f"No features found for loan_id={loan.loan_id}, customer_id={loan.customer_id}"
            )
        
        return predictions[0]
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error in single prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict default risk for multiple loans using features from online store
    """
    try:
        # Create entity rows
        entity_rows = [
            {"loan_id": loan.loan_id, "customer_id": loan.customer_id}
            for loan in request.loans
        ]
        
        # Get predictions
        predictions = predict_with_online_features(entity_rows)
        
        if not predictions:
            raise HTTPException(
                status_code=404, 
                detail=f"No features found for any of the provided loans"
            )
        
        return predictions
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error in batch prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Start API server
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("loan_prediction_api:app", host="0.0.0.0", port=port, reload=True)