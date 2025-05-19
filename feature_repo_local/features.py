"""
features.py - Feature definitions for BFI Finance Indonesia loan monitoring

This file contains the complete feature definitions for the BFI Finance loan monitoring
system, including static loan features, time-varying loan features, and combined features
for various business purposes such as survival analysis, early warning, and financial reporting.

The feature store uses PostgreSQL as the offline store and Redis as the online store.
"""

from datetime import timedelta
from feast import (
    Entity, 
    FeatureView, 
    Field, 
    FeatureService, 
    ValueType, 
    PushSource,
    Project
)
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource
from feast.types import Float32, Int64, String, UnixTimestamp


# Deifine a project for the feature repo

# project = Project(name="BFI Loan Features", description="A project for loan survival analysis")
# Define entities
# ------------------------------
# Entities represent the primary keys that uniquely identify feature records
# and allow Feast to join features from different sources

loan_entity = Entity(
    name="loan",
    join_keys=["loan_id"],
    description="Loan identifier for tracking loan performance and characteristics",
    value_type=ValueType.STRING
)

customer_entity = Entity(
    name="customer",
    join_keys=["customer_id"],
    description="Customer identifier for tracking customer behavior across multiple loans",
    value_type=ValueType.STRING
)

# Define data sources
# ------------------------------
# PostgreSQLSource objects define how to retrieve feature data from PostgreSQL tables

# Static loan features source - attributes that don't change over time
# Update the static loan source to include all columns
static_loan_source = PostgreSQLSource(
    name="static_loan_source",
    query="""
    SELECT 
        loan_id,
        customer_id,
        product_type,
        loan_amount,
        interest_rate,
        loan_term,
        collateral_value,
        ltv_ratio,
        origination_date,
        credit_score,
        monthly_income,
        dti_ratio,
        age,
        employment_years,
        province,
        urban_rural,
        time_to_event,
        default_flag,
        observed,
        event_timestamp
    FROM 
        bfi_static_loan_data
    """,
    timestamp_field="event_timestamp",
)

# Time-varying loan features source - attributes that change over loan lifetime
time_varying_source = PostgreSQLSource(
    name="time_varying_source",
    query="""
    SELECT 
        loan_id,
        payment_status,
        days_past_due,
        remaining_balance,
        payment_amount,
        inflation_rate,
        unemployment_rate,
        exchange_rate,
        event_timestamp
    FROM 
        bfi_time_varying_data
    """,
    timestamp_field="event_timestamp",
)

# Combined loan features source - joining static and time-varying data
combined_loan_source = PostgreSQLSource(
    name="combined_loan_source",
    query="""
    SELECT 
        tv.loan_id,
        tv.payment_status,
        tv.days_past_due,
        tv.remaining_balance,
        tv.payment_amount,
        tv.inflation_rate,
        tv.unemployment_rate,
        tv.exchange_rate,
        tv.event_timestamp,
        s.customer_id,
        s.loan_amount,
        s.interest_rate,
        s.loan_term,
        s.product_type,
        s.ltv_ratio,
        s.credit_score,
        s.dti_ratio,
        s.monthly_income,
        s.province,
        s.urban_rural
    FROM 
        bfi_time_varying_data tv
    JOIN 
        bfi_static_loan_data s
    ON 
        tv.loan_id = s.loan_id
    """,
    timestamp_field="event_timestamp",
)

# batch_source = PostgreSQLSource(
#     name="statical_loan_batch_source",
#     query="""
#     SELECT 
#         loan_id,
#         customer_id,
#         product_type,
#         loan_amount,
#         interest_rate,
#         loan_term,
#         collateral_value,
#         ltv_ratio,
#         origination_date,
#         credit_score,
#         dti_ratio,
#         time_to_event,
#         default_flag,
#         event_timestamp
#     FROM 
#         bfi_static_loan_data
#     """,
#     timestamp_field="event_timestamp",
#     created_timestamp_column='created'
# )

# # Define Push Sources
# push_source = PushSource(
#     name="statical_loan_push_source",
#     batch_source=batch_source
# )


# Define feature views
# ------------------------------
# FeatureView objects define a group of features that share the same data source and entities
# Static loan features - characteristics fixed at loan origination
# Update the static loan features to include all fields
static_loan_features = FeatureView(
    name="static_loan_features",
    entities=[loan_entity],
    ttl=timedelta(days=3650),  # 10 years
    schema=[
        # Existing fields
        Field(name="loan_amount", dtype=Float32),
        Field(name="interest_rate", dtype=Float32),
        Field(name="loan_term", dtype=Int64),
        Field(name="product_type", dtype=String),
        Field(name="collateral_value", dtype=Float32),
        Field(name="ltv_ratio", dtype=Float32),
        Field(name="credit_score", dtype=Int64),
        Field(name="monthly_income", dtype=Float32),
        Field(name="dti_ratio", dtype=Float32),
        Field(name="age", dtype=Int64),
        Field(name="employment_years", dtype=Float32),
        Field(name="province", dtype=String),
        Field(name="urban_rural", dtype=String),
        
        # New fields
        Field(name="origination_date", dtype=UnixTimestamp),  # For date fields
        Field(name="time_to_event", dtype=Int64),  # Assuming this is measured in days or months
        Field(name="default_flag", dtype=Int64),  # Boolean for default status
        Field(name="observed", dtype=Int64),  # Boolean for observation status
    ],
    source=static_loan_source,
    online=True,
    tags={"category": "loan_origination", "owner": "credit_team"},
)

# Time-varying loan features - characteristics that change over time
time_varying_features = FeatureView(
    name="time_varying_features",
    entities=[loan_entity],
    ttl=timedelta(days=3650),  # Features valid for 90 days
    schema=[
        Field(name="payment_status", dtype=String),
        Field(name="days_past_due", dtype=Int64),
        Field(name="remaining_balance", dtype=Float32),
        Field(name="payment_amount", dtype=Float32),
        Field(name="inflation_rate", dtype=Float32),
        Field(name="unemployment_rate", dtype=Float32),
        Field(name="exchange_rate", dtype=Float32),
    ],
    source=time_varying_source,
    online=True,
    tags={"category": "payment_behavior", "owner": "collections_team"},
)

# Combined loan features - join of static and time-varying data
combined_loan_features = FeatureView(
    name="combined_loan_features",
    entities=[loan_entity, customer_entity],
    ttl=timedelta(days=3650),  # Using the more restrictive TTL of the time-varying data
    schema=[
        # Time-varying features
        Field(name="payment_status", dtype=String),
        Field(name="days_past_due", dtype=Int64),
        Field(name="remaining_balance", dtype=Float32),
        Field(name="payment_amount", dtype=Float32),
        Field(name="inflation_rate", dtype=Float32),
        Field(name="unemployment_rate", dtype=Float32),
        Field(name="exchange_rate", dtype=Float32),
        
        # Static features
        Field(name="loan_amount", dtype=Float32),
        Field(name="interest_rate", dtype=Float32),
        Field(name="loan_term", dtype=Int64),
        Field(name="product_type", dtype=String),
        Field(name="ltv_ratio", dtype=Float32),
        Field(name="credit_score", dtype=Int64),
        Field(name="dti_ratio", dtype=Float32),
        Field(name="monthly_income", dtype=Float32),
        Field(name="province", dtype=String),
        Field(name="urban_rural", dtype=String),
    ],
    source=combined_loan_source,
    online=True,
    tags={"category": "combined_view", "owner": "data_science_team"},
)

# push_loan_features = FeatureView(
#     name="push_loan_features",
#     entities=[loan_entity],
#     ttl=timedelta(days=3650),  # 10 years
#     schema=[
#         # Existing fields
#         Field(name="loan_amount", dtype=Float32),
#         Field(name="interest_rate", dtype=Float32),
#         Field(name="loan_term", dtype=Int64),
#         Field(name="product_type", dtype=String),
#         Field(name="collateral_value", dtype=Float32),
#         Field(name="ltv_ratio", dtype=Float32),
#         Field(name="credit_score", dtype=Int64),
#         Field(name="dti_ratio", dtype=Float32),
        
#         # New fields
#         Field(name="origination_date", dtype=UnixTimestamp),  # For date fields
#         Field(name="time_to_event", dtype=Int64),  # Assuming this is measured in days or months
#         Field(name="default_flag", dtype=Int64),  # Boolean for default status
#     ],
#     source=push_source,
#     online=True,
#     tags={"category": "push_loan_origination", "owner": "data_engineer_team"},
# )


# Define feature services
# ------------------------------
# FeatureService objects group features for different model use cases


# Feature service for loan prediction using your provided feature references
loan_prediction_service_fs = FeatureService(
    name="loan_prediction_service",
    features=[
        static_loan_features[[
            "loan_amount", "interest_rate", "loan_term", "product_type",
            "collateral_value", "ltv_ratio", "credit_score",
            "monthly_income", "dti_ratio", "age", "employment_years",
            "province", "urban_rural"
        ]]
    ],
    tags={"description": "Features for loan prediction models"}
)

# Combined feature service with time-varying and static features
combined_prediction_service_fs = FeatureService(
    name="combined_prediction_service",
    features=[
        # Time-varying features - include all available time-varying features
        time_varying_features[[
            "payment_status", "days_past_due", "remaining_balance", 
            "payment_amount", "inflation_rate", "unemployment_rate", 
            "exchange_rate"
        ]],
        # Key static features that would complement time-varying data
        static_loan_features[[
            "loan_amount", "interest_rate", "loan_term", "product_type",
            "ltv_ratio", "credit_score", "dti_ratio", "monthly_income"
        ]]
    ],
    tags={"description": "Combined time-varying and static features for enhanced prediction"}
)
# Survival analysis - predicting time-to-default
# survival_model_features = FeatureService(
#     name="survival_model_features",
#     features=[
#         static_loan_features[["loan_amount", "interest_rate", "loan_term", 
#                              "ltv_ratio", "credit_score", "dti_ratio"]],
#         time_varying_features[["days_past_due", "remaining_balance"]]
#     ],
#     description="Features for survival analysis models to predict time to default",
#     tags={"model_type": "survival_analysis", "owner": "risk_modeling_team"},
# )

# # Early warning system - detecting potential defaults before they happen
# early_warning_features = FeatureService(
#     name="early_warning_features",
#     features=[
#         time_varying_features[["payment_status", "days_past_due", "remaining_balance"]],
#         static_loan_features[["credit_score", "dti_ratio", "ltv_ratio", "product_type"]]
#     ],
#     description="Features for early warning system to detect potential defaults",
#     tags={"model_type": "classification", "owner": "collections_team"},
# )

# # Macroeconomic impact analysis - understanding macro factors on loan performance
# macro_impact_features = FeatureService(
#     name="macro_impact_features",
#     features=[
#         time_varying_features[["inflation_rate", "unemployment_rate", "exchange_rate", "days_past_due"]],
#         static_loan_features[["province", "urban_rural", "product_type"]]
#     ],
#     description="Features for analyzing macroeconomic impacts on loan performance",
#     tags={"model_type": "regression", "owner": "economic_research_team"},
# )

# # Financial reporting - aggregate metrics for business reporting
# financial_reporting_features = FeatureService(
#     name="financial_reporting_features",
#     features=[
#         combined_loan_features[["loan_amount", "remaining_balance", "payment_status", 
#                               "product_type", "province"]]
#     ],
#     description="Features for financial reporting and business intelligence",
#     tags={"model_type": "reporting", "owner": "finance_team"},
# )

# # Comprehensive risk model - all relevant risk factors
# comprehensive_risk_features = FeatureService(
#     name="comprehensive_risk_features",
#     features=[
#         combined_loan_features[["loan_amount", "interest_rate", "loan_term", 
#                               "ltv_ratio", "credit_score", "dti_ratio",
#                               "days_past_due", "remaining_balance", 
#                               "payment_status", "inflation_rate", 
#                               "unemployment_rate", "product_type"]]
#     ],
#     description="Comprehensive set of features for holistic risk assessment",
#     tags={"model_type": "mixed", "owner": "enterprise_risk_team"},
# )

# # Customer profile features - customer-level aggregations
# customer_profile_features = FeatureService(
#     name="customer_profile_features",
#     features=[
#         static_loan_features[["credit_score", "monthly_income", "age", 
#                              "employment_years", "province"]]
#     ],
#     description="Customer demographic and credit profile features",
#     tags={"model_type": "customer_segmentation", "owner": "marketing_team"},
# )