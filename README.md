# Loan Default Prediction System

This repository contains a complete system for loan default prediction using a feature store (Feast) and survival analysis. It showcases how to build a model that predicts the probability of loan default over time for an Indonesian financial institution.

## Overview

The system uses the following components:

- **Feast** as a feature store with:
  - PostgreSQL as the offline store and registry
  - Redis as the online store
- **Survival Analysis** model for predicting loan defaults over time
- **FastAPI** service for making real-time predictions

## Implementation Status

| Status | Component | Details |
|:------:|-----------|---------|
| ✅ | PostgreSQL as Data Source / Offline Store | Successfully implemented |
| ✅ | Redis as Online Store | Successfully implemented |
| ✅ | PostgreSQL as Registry database | Successfully implemented |
| ✅ | Feast UI | Running on port 8888 |
| ✅ | Feature Server | Running on port 6566 |
| ✅ | Offline Server | Running on port 8815 |
| ✅ | Registry Server | Running on port 6570 |
| ✅ | Historical Feature Retrieval | Working with both direct access and remote (via serve_offline) |
| ⚠️ | Online Feature Retrieval | Working with direct connection (Python SDK) and HTTP API (feast serve). Remote access via Python SDK fails. |
| ⚠️ | Materialization | Successful via direct connection, fails via remote connection |
| ❌ | Push Source Implementation | Failed to implement Push concept |

This status summary provides a quick overview of the current implementation. Components marked with ✅ are fully functional, ⚠️ indicates partial functionality, and ❌ indicates implementation failures that are still being addressed.

## Prerequisites

- Python 3.11
- Docker and Docker Compose
- pipenv

## Installation and Setup

### 1. Install Dependencies

Install the required Python packages using pipenv:

```bash
pipenv install
```

This will install all dependencies defined in the Pipfile, including:
- feast (with Redis, PostgreSQL, and Great Expectations extras)
- pandas, scipy, scikit-survival
- lifelines, SHAP
- Jupyter and other essential packages

### 2. Setting Up the Feast Docker Container

The project uses Docker to run all the necessary Feast components (registry server, feature server, offline server, and UI).

#### 2.1 Build and Start Docker Containers

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL (offline store and registry)
- Start Redis (online store)
- Build and start the Feast container using Dockerfile.feast

The Docker setup includes:
- `Dockerfile.feast`: Builds the Feast container
- `docker-compose.yml`: Configures all services
- `feature_repo`: Directory mounted to the Feast container
- `init-feast.sh`: Initialization script for Feast
- `supervisord.conf`: Manages the multiple Feast processes

### 3. Generate and Load Data

Generate synthetic loan data and load it into PostgreSQL:

```bash
python src/postgres_loader.py
```

This script will:
- Generate synthetic loan data using `data_generator.py`
- Create the necessary tables in PostgreSQL
- Load the data into the PostgreSQL tables

### 4. Feature Repository Configuration

The project uses two feature repository configurations:
- `feature_repo_local`: For direct connection from your local machine to the datastores
- `feature_repo_remote`: For connecting through the Feast servers (not fully tested yet)

### 5. Register Features with Feast

Navigate to the feature repository directory and apply the feature definitions:

```bash
cd feature_repo_local
feast apply
```

This registers all the feature definitions from `features.py` with the Feast registry.

### 6. Explore Historical Data

Run the Jupyter notebook for exploring historical data:

```bash
jupyter notebook 01_Get_Historical_Data.ipynb
```

This notebook shows how to:
- Connect to the feature store
- Retrieve historical features
- Prepare data for survival analysis

You can modify the connection type in the notebook:

```python
store = FeatureStore(
    repo_path="../feature_repo_local",  # Change to feature_repo_remote to test remote connection
)
```

### 7. Build Survival Analysis Model

Run the survival analysis notebook:

```bash
jupyter notebook 02_Survival_Analysis.ipynb
```

This notebook demonstrates:
- Preparing data for survival analysis
- Building a Random Survival Forest model
- Evaluating model performance
- Saving the model for deployment

### 8. Materialize Features for Online Serving

Materialize features to make them available in the online store:

```bash
python materialize_features.py
```

This process:
- Reads features from the offline store (PostgreSQL)
- Writes them to the online store (Redis)
- Makes features available for real-time serving

### 9. Check Online Features

Verify that features are correctly materialized in the online store using two different methods:

```bash
python check_online_features.py
```

This enhanced script demonstrates two approaches to retrieving online features:

#### Method 1: Using the Feast Python SDK

The first part of the script:
- Initializes a connection to the feature store using the SDK
- Defines entity rows with loan_id and customer_id
- Specifies feature references in the format "feature_view:feature_name"
- Calls `store.get_online_features()` to retrieve the features
- Displays results as both a dictionary and DataFrame
- Validates that features exist for the given entity IDs

Example Python SDK code:
```python
# Initialize the feature store
store = FeatureStore(repo_path="./feature_repo_local")

# Define entity rows
entity_rows = [{"loan_id": "L12713", "customer_id": "C5380"}]

# Define feature references
feature_refs = [
    "static_loan_features:loan_amount",
    "static_loan_features:interest_rate",
    # Additional features...
]

# Retrieve features using the SDK
online_features = store.get_online_features(
    entity_rows=entity_rows,
    features=feature_refs
)

# Convert to dictionary or DataFrame for inspection
result_dict = online_features.to_dict()
result_df = online_features.to_df()
```

#### Method 2: Using the Feast HTTP API

The second part of the script:
- Prepares a JSON payload for the HTTP request
- Sends a POST request to the Feast Feature Server's `/get-online-features` endpoint
- Processes the JSON response
- Compares results between the SDK and HTTP methods

Example HTTP API code:
```python
# Prepare HTTP request payload
http_payload = {
    "features": feature_refs,
    "entities": {
        "loan_id": [entity_rows[0]["loan_id"]],
        "customer_id": [entity_rows[0]["customer_id"]]
    }
}

# Make HTTP request to Feast Feature Server
http_response = requests.post(
    "http://localhost:6566/get-online-features",
    json=http_payload
)

# Process the response
http_result = http_response.json()
```

#### Why Use Different Methods?

- **Python SDK**: Ideal for local development, debugging, and when your application is written in Python. Provides tight integration with pandas and other Python data tools.

- **HTTP API**: Best for language-agnostic access, microservice architectures, or when the client and Feast server are deployed separately. Allows any service that can make HTTP requests to access features.

Both methods should return identical feature values, providing flexibility in how you integrate feature retrieval into your production systems.

## API Service Options

### Option 1: API with Feast Integration

Use the full prediction API that retrieves features from Feast:

```bash
python loan_prediction_api.py
```

The API provides:
- Health check endpoint: `/health`
- Single prediction endpoint: `/predict`
- Batch prediction endpoint: `/predict/batch`

Test this API using:

```bash
python test_prediction_api.py
```

### Option 2: Standalone API without Feast

If you want to test the model without relying on Feast's online features, use the standalone API:

```bash
python api_service.py
```

This simplified API:
- Works with feature data provided directly in the request
- Does not require a connection to the feature store
- Uses the same model for predictions

Test the standalone API using:

```bash
python test_api.py
```

Key differences:
- The standalone API expects all features in the request payload
- The Feast-integrated API retrieves features from the online store using only entity IDs
- Use the standalone API for testing or when feature retrieval is handled by an upstream service

## Directory Structure

- `feature_repo_local/`: Feature repository for local connections
- `feature_repo_remote/`: Feature repository for remote connections
- `src/`: Source code for data generation and model serving
- `notebooks/`: Jupyter notebooks for analysis and modeling
- `models/`: Saved machine learning models

## Feature Definitions

The system includes several feature views:
- `static_loan_features`: Loan characteristics at origination
- `time_varying_features`: Features that change over the loan lifetime
- `combined_loan_features`: Join of static and time-varying features

These features are used in the following feature services:
- `loan_prediction_service`: For static feature-based predictions
- `combined_prediction_service`: For predictions using both static and time-varying features

## Workflow Summary

1. Install dependencies
2. Start Docker containers for Feast
3. Generate and load synthetic data
4. Register feature definitions
5. Explore historical data
6. Build and train survival analysis model
7. Materialize features for online serving
8. Run prediction API

## Next Steps


## License

[Add appropriate license information here]
