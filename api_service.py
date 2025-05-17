# File: api_service.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import uvicorn
from src.model_service import LoanDefaultPredictor

# Initialize the model service
MODEL_PATH = "models/rsf_pipeline.pkl"  # Update this path to your model
model_service = LoanDefaultPredictor(MODEL_PATH)

# Initialize FastAPI app
app = FastAPI(title="Loan Default Prediction API")

# Define request models
class LoanFeatures(BaseModel):
    loan_id: str
    customer_id: str
    loan_amount: int
    interest_rate: float
    loan_term: int
    product_type: str
    collateral_value: Optional[int] = None
    ltv_ratio: Optional[float] = None
    credit_score: Optional[int] = None
    monthly_income: Optional[int] = None
    dti_ratio: Optional[float] = None
    age: Optional[int] = None
    employment_years: Optional[float] = None
    province: Optional[str] = None
    urban_rural: Optional[str] = None

class BatchPredictionRequest(BaseModel):
    loans: List[LoanFeatures]

# Define API endpoints
@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.post("/predict")
def predict_single(loan: LoanFeatures):
    """Make predictions for a single loan"""
    try:
        # Convert to DataFrame (single row)
        features_df = pd.DataFrame([loan.dict()])
        
        # Make prediction
        result_df = model_service.predict(features_df)
        
        # Convert to dictionary for response
        response = result_df.iloc[0].to_dict()
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
def predict_batch(request: BatchPredictionRequest):
    """Make predictions for multiple loans"""
    try:
        # Convert list of loans to DataFrame
        features_list = [loan.dict() for loan in request.loans]
        features_df = pd.DataFrame(features_list)
        
        # Make predictions
        result_df = model_service.predict(features_df)
        
        # Convert to list of dictionaries for response
        predictions = result_df.to_dict(orient='records')
        
        return {"predictions": predictions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the app
if __name__ == "__main__":
    uvicorn.run("api_service:app", host="0.0.0.0", port=8001, reload=True)