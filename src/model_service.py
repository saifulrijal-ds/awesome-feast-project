# File: model_service.py
import pickle
import numpy as np
import pandas as pd

class LoanDefaultPredictor:
    def __init__(self, model_path):
        """Load the trained scikit-learn pipeline"""
        with open(model_path, 'rb') as f:
            self.pipeline = pickle.load(f)
    
    def predict(self, features_df):
        """
        Make predictions using the loaded model
        
        Parameters:
        features_df (pd.DataFrame): DataFrame containing loan features
        
        Returns:
        pd.DataFrame: DataFrame with original features and predictions
        """
        # Make a copy to avoid modifying the input
        result_df = features_df.copy()
        
        # Get the model from the pipeline
        rsf_model = self.pipeline.named_steps['rsf']
        
        # Get risk scores (higher = higher risk)
        result_df['risk_score'] = self.pipeline.predict(features_df)
        
        # Get survival functions
        X_transformed = self.pipeline.named_steps['preprocessor'].transform(features_df)
        survival_funcs = rsf_model.predict_survival_function(X_transformed)
        
        # Calculate survival probabilities at specific time points
        time_points = [6, 12, 24, 36]  # 6 months, 1 year, 2 years, 3 years
        
        for t in time_points:
            # Evaluate survival function at time point t
            surv_probs = np.array([fn(t) for fn in survival_funcs])
            result_df[f'survival_prob_{t}m'] = surv_probs
            result_df[f'default_prob_{t}m'] = 1 - surv_probs
        
        return result_df