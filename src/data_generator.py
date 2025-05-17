import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from scipy import stats

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_synthetic_loan_data(num_loans=1000, start_date='2023-01-01', end_date='2024-01-01', 
                               target_default_rate=0.55, max_history_months=24):
    """
    Generate synthetic static loan data for survival analysis with BFI Finance Indonesia characteristics
    
    Parameters:
    -----------
    num_loans : int
        Number of loans to generate
    start_date : str
        Start date for loan origination (YYYY-MM-DD)
    end_date : str
        End date for loan origination (YYYY-MM-DD)
    target_default_rate : float
        Target proportion of loans that should default (0.0-1.0). The function will try to achieve
        a default rate within ±5% of this target.
    max_history_months : int
        Maximum number of months to generate for censored loans
        
    Returns:
    --------
    DataFrame with static loan features
    """
    # Modified: Restrict product types to only Motorcycle and Car
    product_types = ['Motorcycle', 'Car']
    product_weights = [0.6, 0.4]  # Adjusted weights for just two products
    
    provinces = ['Jakarta', 'West Java', 'East Java', 'Central Java', 'Banten', 
                'North Sumatra', 'South Sulawesi', 'Bali']
    province_weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.05, 0.05, 0.05]
    
    urban_rural = ['Urban', 'Rural']
    urban_rural_weights = [0.7, 0.3]  # BFI likely has more urban customers
    
    # Generate loan IDs and customer IDs
    loan_ids = [f'L{10001 + i}' for i in range(num_loans)]
    customer_ids = [f'C{random.randint(1000, 9999)}' for _ in range(num_loans)]
    
    # Generate origination dates
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    days_range = (end_datetime - start_datetime).days
    origination_dates = [start_datetime + timedelta(days=random.randint(0, days_range)) 
                         for _ in range(num_loans)]
    
    # Generate product types based on weights
    product_types_data = random.choices(product_types, weights=product_weights, k=num_loans)
    
    # Generate loan amounts based on product type
    loan_amounts = []
    interest_rates = []
    loan_terms = []
    collateral_values = []  # Added for LTV calculation
    
    # Modified: Simplified to handle only Motorcycle and Car products
    for product in product_types_data:
        if product == 'Motorcycle':
            amount = max(3000000, np.random.lognormal(mean=16.5, sigma=0.3))  # Around 15M IDR
            rate = np.random.uniform(15.0, 22.0)  # Higher rates for motorcycles
            term = random.choice([12, 24, 36])  # Shorter terms for motorcycles
            # Collateral value (motorcycles typically financed at higher LTV)
            collateral = amount * np.random.uniform(0.8, 1.1)
        else:  # Car
            amount = max(50000000, np.random.lognormal(mean=18.5, sigma=0.4))  # Around 100M IDR
            rate = np.random.uniform(12.0, 18.0)
            term = random.choice([12, 24, 36, 48, 60])
            # Cars typically have higher collateral value than loan amount
            collateral = amount * np.random.uniform(1.0, 1.3)
        
        loan_amounts.append(int(amount))
        interest_rates.append(round(rate, 1))
        loan_terms.append(term)
        collateral_values.append(int(collateral))
    
    # Calculate LTV ratios
    ltv_ratios = [round(loan / collateral, 2) for loan, collateral in zip(loan_amounts, collateral_values)]
    
    # Generate borrower characteristics
    credit_scores = np.random.normal(700, 70, num_loans).astype(int)
    credit_scores = np.clip(credit_scores, 300, 850)  # Clip to valid score range
    
    monthly_incomes = []
    for amount in loan_amounts:
        # Income should be related to loan amount but with some variation
        if amount < 20000000:  # Motorcycle loan range
            income = np.random.uniform(3000000, 8000000)  # 3-8M IDR monthly
        else:  # Car loan range
            income = np.random.uniform(7000000, 20000000)  # 7-20M IDR monthly
        monthly_incomes.append(int(income))
    
    # DTI should be related to loan amount vs income
    dti_ratios = []
    for amount, income, term in zip(loan_amounts, monthly_incomes, loan_terms):
        # Calculate approximate payment
        monthly_rate = interest_rates[loan_amounts.index(amount)] / 100 / 12
        payment = amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
        dti = payment / income + np.random.uniform(0, 0.2)  # Add some other debt
        dti_ratios.append(min(round(dti, 2), 0.9))  # Cap at 90% DTI
    
    # Other borrower characteristics
    ages = np.random.normal(35, 10, num_loans).astype(int)
    ages = np.clip(ages, 21, 65)  # Valid age range for borrowers
    
    employment_years = np.clip(np.random.lognormal(mean=1.5, sigma=0.8, size=num_loans), 0.5, 30)
    employment_years = [round(y, 1) for y in employment_years]
    
    provinces_data = random.choices(provinces, weights=province_weights, k=num_loans)
    urban_rural_data = random.choices(urban_rural, weights=urban_rural_weights, k=num_loans)
    
    # Calculate default probability based on features (simplified Cox-like model)
    # We'll calibrate this to achieve a more realistic default rate
    default_probs = []
    for i in range(num_loans):
        # Start with a low base probability
        prob = 0.1
        
        # Credit score effect (lower score = higher risk)
        credit_factor = 1.0 - (credit_scores[i] / 850) * 0.8
        prob *= credit_factor * 2.0
        
        # DTI impact (higher DTI = higher risk)
        prob *= (1 + dti_ratios[i] * 1.2)
        
        # LTV impact (higher LTV = higher risk)
        prob *= (1 + ltv_ratios[i] * 0.7)
        
        # Product type impact
        if product_types_data[i] == 'Motorcycle':
            prob *= 1.3  # Higher risk for motorcycles
        else:  # Car
            prob *= 1.1
        
        # Geographic impact
        if provinces_data[i] == 'Jakarta':
            prob *= 0.9  # Lower risk in Jakarta
        elif urban_rural_data[i] == 'Rural':
            prob *= 1.2  # Higher risk in rural areas
        
        # Employment stability impact
        prob *= (1 + np.exp(-0.15 * employment_years[i]))
        
        # Cap at 0.95 to prevent certainty
        default_probs.append(min(prob, 0.95))
    
    # Simulate default events based on calibrated probabilities
    # We'll convert probabilities to defaults in a way that targets the desired default rate
    
    # Sort loans by default probability (highest to lowest)
    indices_by_risk = sorted(range(len(default_probs)), key=lambda i: default_probs[i], reverse=True)
    
    # Calculate how many loans should default to hit target rate
    target_defaults = int(round(num_loans * target_default_rate))
    
    # Initialize default flags and time-to-events
    default_flags = [0] * num_loans
    time_to_events = [0] * num_loans
    observed_flags = [0] * num_loans
    
    # Assign defaults to the riskiest loans
    for i in range(target_defaults):
        idx = indices_by_risk[i]
        default_flags[idx] = 1
        observed_flags[idx] = 1
    
    # For defaulted loans, generate time to default based on risk
    for i in range(num_loans):
        if default_flags[i] == 1:
            # Higher risk loans default sooner
            # Use a Weibull distribution with parameters tuned to risk
            shape = 1.2  # Increasing failure rate (common in loans)
            scale = max(3, int(20 * (1 - default_probs[i])))  # Higher risk = shorter time to default
            
            # Generate time to default (between 1 and loan term)
            time_to_default = max(1, min(loan_terms[i], round(np.random.weibull(shape) * scale)))
            time_to_events[i] = time_to_default
        else:
            # FIX: For non-defaulting loans, set time_to_event to min of loan_term and max_history_months
            # This ensures consistency between static and time-varying data
            time_to_events[i] = min(loan_terms[i], max_history_months)
    
    # Create DataFrame
    static_loan_df = pd.DataFrame({
        'loan_id': loan_ids,
        'customer_id': customer_ids,
        'product_type': product_types_data,
        'loan_amount': loan_amounts,
        'interest_rate': interest_rates,
        'loan_term': loan_terms,
        'collateral_value': collateral_values,
        'ltv_ratio': ltv_ratios,
        'origination_date': origination_dates,
        'credit_score': credit_scores,
        'monthly_income': monthly_incomes,
        'dti_ratio': dti_ratios,
        'age': ages,
        'employment_years': employment_years,
        'province': provinces_data,
        'urban_rural': urban_rural_data,
        'time_to_event': time_to_events,
        'default_flag': default_flags,
        'observed': observed_flags  # 1 if default observed, 0 if censored
    })
    
    # Add event_timestamp for Feast compatibility
    static_loan_df['event_timestamp'] = static_loan_df['origination_date']
    
    # Print default rate info
    actual_default_rate = static_loan_df['default_flag'].mean() * 100
    print(f"Generated {num_loans} loans with {actual_default_rate:.1f}% default rate")
    
    return static_loan_df

def generate_time_varying_data(static_loan_df, max_history_months=24):
    """
    Generate time-varying loan data based on the static loan information
    
    Parameters:
    -----------
    static_loan_df : DataFrame
        DataFrame with static loan information
    max_history_months : int
        Maximum number of months to generate for censored loans
        
    Returns:
    --------
    DataFrame with time-varying features
    """
    time_varying_rows = []
    
    # Find the maximum possible month we'll need data for
    max_required_months = max(
        static_loan_df['loan_term'].max(),  # Longest loan term
        static_loan_df['time_to_event'].max()  # Longest time to event
    )
    max_months = max(max_required_months + 12, max_history_months + 12)  # Add buffer
    
    # Generate macroeconomic data (common across all loans for each month)
    # Starting values
    base_inflation = 5.3  # Starting inflation rate (%)
    base_unemployment = 5.5  # Starting unemployment rate (%)
    base_exchange_rate = 15200  # Starting IDR/USD rate
    
    # Generate enough months of macro data with realistic time series
    months = range(1, max_months + 1)
    
    # Model with some seasonality and trends
    inflation_rates = []
    unemployment_rates = []
    exchange_rates = []
    
    for i in months:
        # Inflation follows AR(1) process with slight seasonality
        if i == 1:
            inflation = base_inflation
        else:
            inflation = inflation_rates[-1] * 0.8 + np.random.normal(0, 0.15) + 0.1 * np.sin(i * np.pi / 6)
            inflation = max(4.0, min(8.0, inflation))  # Keep in realistic bounds
        inflation_rates.append(round(inflation, 2))
        
        # Unemployment rate with persistence and small random changes
        if i == 1:
            unemployment = base_unemployment
        else:
            unemployment = unemployment_rates[-1] * 0.9 + np.random.normal(0, 0.1) + 0.05 * np.sin(i * np.pi / 6)
            unemployment = max(4.5, min(7.0, unemployment))
        unemployment_rates.append(round(unemployment, 1))
        
        # Exchange rate with random walk and reversion
        if i == 1:
            exchange_rate = base_exchange_rate
        else:
            exchange_rate = exchange_rates[-1] * 0.95 + base_exchange_rate * 0.05 + np.random.normal(0, 50)
            exchange_rate = max(14000, min(16500, exchange_rate))
        exchange_rates.append(int(exchange_rate))
    
    # Define default threshold as 90+ days past due
    default_threshold = 90
    
    # Process each loan
    for _, loan in static_loan_df.iterrows():
        loan_id = loan['loan_id']
        origination_date = loan['origination_date']
        loan_term = loan['loan_term']
        loan_amount = loan['loan_amount']
        interest_rate = loan['interest_rate']
        default_flag = loan['default_flag']
        time_to_event = loan['time_to_event']
        
        # Calculate payment amount (simplified)
        monthly_rate = interest_rate / 100 / 12
        payment_amount = loan_amount * (monthly_rate * (1 + monthly_rate) ** loan_term) / ((1 + monthly_rate) ** loan_term - 1)
        payment_amount = round(payment_amount)
        
        # Determine how many months to generate
        if default_flag == 1:
            # If defaulted, generate up to the default month
            months_to_generate = time_to_event
        else:
            # If not defaulted, generate up to the censoring point
            # This now matches what's in the static data due to our fix above
            months_to_generate = time_to_event
        
        # Remaining balance starts at loan amount
        remaining_balance = loan_amount
        
        # Generate payment behavior
        # More likely to miss payments as approaching default
        for month in range(1, months_to_generate + 1):
            observation_date = origination_date + timedelta(days=30*month)
            
            # Calculate remaining balance (simplified)
            if month == 1:
                remaining_balance = loan_amount
            else:
                # Simple interest calculation for remaining balance
                principal_payment = payment_amount - (remaining_balance * monthly_rate)
                remaining_balance = max(0, remaining_balance - principal_payment)
            
            # Determine payment status and days past due
            # CORRECTED payment status classification:
            # - On Time: days_past_due = 0
            # - 0+: 0 < days_past_due <= 30
            # - 30+: 30 < days_past_due <= 60
            # - 60+: 60 < days_past_due <= 90
            # - 90+: days_past_due > 90
            
            if default_flag == 0 or month < time_to_event - 3:
                # Regular good payment behavior with small chance of late payment
                rand = np.random.random()
                if rand < 0.85:
                    payment_status = 'On Time'
                    days_past_due = 0
                elif rand < 0.95:
                    payment_status = '0+'
                    days_past_due = np.random.randint(1, 31)  # 1-30 days
                else:
                    payment_status = '30+'
                    days_past_due = np.random.randint(31, 61)  # 31-60 days
            elif month == time_to_event - 3:
                # Three months before default, increasing delinquency
                rand = np.random.random()
                if rand < 0.3:
                    payment_status = 'On Time'
                    days_past_due = 0
                elif rand < 0.7:
                    payment_status = '0+'
                    days_past_due = np.random.randint(1, 31)  # 1-30 days
                else:
                    payment_status = '30+'
                    days_past_due = np.random.randint(31, 61)  # 31-60 days
            elif month == time_to_event - 2:
                # Two months before default, high delinquency
                rand = np.random.random()
                if rand < 0.2:
                    payment_status = '0+'
                    days_past_due = np.random.randint(1, 31)  # 1-30 days
                elif rand < 0.6:
                    payment_status = '30+'
                    days_past_due = np.random.randint(31, 61)  # 31-60 days
                else:
                    payment_status = '60+'
                    days_past_due = np.random.randint(61, 91)  # 61-90 days
            elif month == time_to_event - 1:
                # One month before default, severe delinquency
                rand = np.random.random()
                if rand < 0.3:
                    payment_status = '30+'
                    days_past_due = np.random.randint(31, 61)  # 31-60 days
                else:
                    payment_status = '60+'
                    days_past_due = np.random.randint(61, 91)  # 61-90 days
            elif month == time_to_event and default_flag == 1:
                # Default month - days past due > 90
                payment_status = '90+'
                days_past_due = np.random.randint(91, 121)  # 91-120 days past due
            
            # Get macroeconomic indicators for this month
            # Use month index to get corresponding macro data
            macro_idx = month - 1  # 0-indexed
            inflation_rate = inflation_rates[macro_idx]
            unemployment_rate = unemployment_rates[macro_idx]
            exchange_rate = exchange_rates[macro_idx]
            
            # For default month, set payment status explicitly as '90+'
            if default_flag == 1 and month == time_to_event:
                payment_status = '90+'
            
            # Add row to time-varying data
            time_varying_rows.append({
                'loan_id': loan_id,
                'observation_date': observation_date,
                'month': month,
                'payment_status': payment_status,
                'days_past_due': days_past_due,
                'remaining_balance': int(remaining_balance),
                'payment_amount': payment_amount,
                'inflation_rate': inflation_rate,
                'unemployment_rate': unemployment_rate,
                'exchange_rate': exchange_rate,
                'event_timestamp': observation_date  # For Feast compatibility
            })
    
    # Create DataFrame
    time_varying_df = pd.DataFrame(time_varying_rows)
    return time_varying_df

def validate_dataset_consistency(static_df, time_varying_df):
    """
    Validate consistency between static and time-varying datasets
    
    Parameters:
    -----------
    static_df : DataFrame
        Static loan data
    time_varying_df : DataFrame
        Time-varying loan data
    """
    # 1. Verify all loan IDs in static data exist in time-varying data
    static_loan_ids = set(static_df['loan_id'])
    time_varying_loan_ids = set(time_varying_df['loan_id'])
    
    missing_in_tv = static_loan_ids - time_varying_loan_ids
    missing_in_static = time_varying_loan_ids - static_loan_ids
    
    if missing_in_tv:
        print(f"ERROR: {len(missing_in_tv)} loans in static data are missing from time-varying data!")
    else:
        print("✓ All loans in static data have corresponding time-varying data")
        
    if missing_in_static:
        print(f"ERROR: {len(missing_in_static)} loans in time-varying data are missing from static data!")
    else:
        print("✓ All loans in time-varying data have corresponding static data")
    
    # 2. Check default timing and status consistency
    default_timing_mismatches = 0
    censoring_mismatches = 0
    
    for _, loan in static_df.iterrows():
        loan_id = loan['loan_id']
        time_to_event = loan['time_to_event']
        default_flag = loan['default_flag']
        
        # Get time-varying records for this loan
        loan_tv = time_varying_df[time_varying_df['loan_id'] == loan_id]
        
        if len(loan_tv) == 0:
            continue  # Skip if no time-varying data (should have been caught above)
        
        # A. Check observation period consistency
        max_month = loan_tv['month'].max()
        
        if max_month != time_to_event:
            if default_flag == 1:
                default_timing_mismatches += 1
            else:
                censoring_mismatches += 1
                
        # B. Check default status consistency for defaulted loans
        if default_flag == 1:
            # Find when loan first hits 90+ DPD
            default_months = loan_tv[loan_tv['days_past_due'] > 90]
            
            if len(default_months) == 0:
                print(f"ERROR: Loan {loan_id} is marked as defaulted but never reaches 90+ DPD!")
            else:
                first_default_month = default_months['month'].min()
                if first_default_month != time_to_event:
                    print(f"ERROR: Loan {loan_id} first defaults at month {first_default_month} but time_to_event is {time_to_event}")
    
    # Report timing consistency results
    if default_timing_mismatches > 0:
        print(f"ERROR: {default_timing_mismatches} defaulted loans have mismatched time_to_event values!")
    else:
        print("✓ All defaulted loans have consistent default timing between datasets")
        
    if censoring_mismatches > 0:
        print(f"ERROR: {censoring_mismatches} censored loans have mismatched observation periods!")
    else:
        print("✓ All censored loans have consistent observation periods between datasets")
    
    # 3. Check payment behavior consistency
    payment_issues = 0
    
    for loan_id in static_loan_ids:
        loan_tv = time_varying_df[time_varying_df['loan_id'] == loan_id]
        
        # Check that days_past_due and payment_status are consistent
        # FIX: Updated to match the corrected payment status ranges
        for _, record in loan_tv.iterrows():
            status = record['payment_status']
            dpd = record['days_past_due']
            
            if status == 'On Time' and dpd != 0:
                payment_issues += 1
            elif status == '0+' and (dpd <= 0 or dpd > 30):
                payment_issues += 1
            elif status == '30+' and (dpd <= 30 or dpd > 60):
                payment_issues += 1
            elif status == '60+' and (dpd <= 60 or dpd > 90):
                payment_issues += 1
            elif status == '90+' and dpd <= 90:
                payment_issues += 1
    
    if payment_issues > 0:
        print(f"WARNING: {payment_issues} payment records have inconsistent status and days_past_due values")
    else:
        print("✓ All payment records have consistent status and days_past_due values")
    
    # 4. Check financial consistency (loan amounts and payments)
    financial_issues = 0
    
    for _, loan in static_df.iterrows():
        loan_id = loan['loan_id']
        loan_amount = loan['loan_amount']
        interest_rate = loan['interest_rate']
        loan_term = loan['loan_term']
        
        # Calculate expected payment amount
        monthly_rate = interest_rate / 100 / 12
        expected_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** loan_term) / ((1 + monthly_rate) ** loan_term - 1)
        expected_payment = round(expected_payment)
        
        # Get first time-varying record to check initial balance and payment
        loan_tv_first = time_varying_df[(time_varying_df['loan_id'] == loan_id) & (time_varying_df['month'] == 1)]
        
        if len(loan_tv_first) == 0:
            continue
            
        # Check initial balance
        initial_balance = loan_tv_first['remaining_balance'].iloc[0]
        if abs(initial_balance - loan_amount) > 1:  # Allow for rounding differences
            financial_issues += 1
            
        # Check payment amount
        payment_amount = loan_tv_first['payment_amount'].iloc[0]
        if abs(payment_amount - expected_payment) > 1:  # Allow for rounding differences
            financial_issues += 1
    
    if financial_issues > 0:
        print(f"WARNING: {financial_issues} loans have financial consistency issues")
    else:
        print("✓ All loans have consistent financial values between datasets")
        
    # Summary
    print("\nConsistency check summary:")
    issues_found = len(missing_in_tv) + len(missing_in_static) + default_timing_mismatches + censoring_mismatches + payment_issues + financial_issues
    
    if issues_found == 0:
        print("✅ SUCCESS: Static and time-varying datasets are fully consistent!")
    else:
        print(f"⚠️ ALERT: Found {issues_found} consistency issues that should be fixed!")

# Function to run full data generation process
def generate_and_save_bfi_loan_data(num_loans=1000, target_default_rate=0.55, output_prefix="bfi", max_history_months=24):
    """
    Generate and save both static and time-varying loan data
    
    Parameters:
    -----------
    num_loans : int
        Number of loans to generate
    target_default_rate : float
        Target proportion of loans that should default (0.0-1.0)
    output_prefix : str
        Prefix for output filenames
    max_history_months : int
        Maximum number of months to generate for censored loans
    
    Returns:
    --------
    tuple of (static_data, time_varying_data) DataFrames
    """
    # Generate data
    print(f"Generating {num_loans} synthetic loans...")
    static_loan_data = generate_synthetic_loan_data(
        num_loans=num_loans, 
        target_default_rate=target_default_rate,
        max_history_months=max_history_months
    )
    
    print("Generating time-varying data...")
    time_varying_data = generate_time_varying_data(
        static_loan_data,
        max_history_months=max_history_months
    )
    
    # Run comprehensive consistency checks between the datasets
    print("\nRunning consistency checks between static and time-varying data...")
    validate_dataset_consistency(static_loan_data, time_varying_data)
    
    # Preview the data
    print("\nStatic Loan Data preview (first 5 rows):")
    print(static_loan_data.head(5)[['loan_id', 'product_type', 'loan_amount', 'ltv_ratio', 'default_flag', 'observed']].to_string())
    
    # Print one defaulted loan's time-varying data
    defaulted_loan = static_loan_data[static_loan_data['default_flag'] == 1]['loan_id'].iloc[0]
    print(f"\nTime-Varying Data preview (sample for defaulted loan {defaulted_loan}):")
    print(time_varying_data[time_varying_data['loan_id'] == defaulted_loan].tail(5)[
        ['loan_id', 'month', 'payment_status', 'days_past_due']
    ].to_string())
    
    # Save to CSV for further use
    static_csv = f"{output_prefix}_static_loan_data.csv"
    time_varying_csv = f"{output_prefix}_time_varying_data.csv"
    
    static_loan_data.to_csv(static_csv, index=False)
    time_varying_data.to_csv(time_varying_csv, index=False)
    
    print(f"\nData saved to {static_csv} and {time_varying_csv}")
    
    return static_loan_data, time_varying_data

# Example usage:
# if __name__ == "__main__":
#     static_data, time_data = generate_and_save_bfi_loan_data(
#         num_loans=1000, 
#         target_default_rate=0.55,
#         output_prefix="bfi",
#         max_history_months=24
#     )