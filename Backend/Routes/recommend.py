import os
import joblib
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from sklearn.metrics.pairwise import cosine_similarity
from schemas import CarRecommendationRequest

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

try:
    scaler = joblib.load(os.path.join(ARTIFACTS_DIR, 'scaler.pkl'))
    ohe = joblib.load(os.path.join(ARTIFACTS_DIR, 'ohe.pkl'))
    feature_matrix = joblib.load(os.path.join(ARTIFACTS_DIR, 'feature_matrix.pkl'))
    df = joblib.load(os.path.join(ARTIFACTS_DIR, 'df_cleaned.pkl'))
except Exception as e:
    print(f"Warning: Failed to load models from {ARTIFACTS_DIR}. Error: {e}")
    scaler = ohe = feature_matrix = df = None


@router.post("/recommend")
def get_recommendations(request: CarRecommendationRequest, top_n: int = 5):
    if df is None:
        raise HTTPException(status_code=500, detail="Model artifacts not found. Please export from Jupyter Notebook first.")
        
    budget = request.budget_usd
    budget_lakhs = request.budget_in_lakhs   # Raw Indian budget for tier detection
    vehicle_style = request.vehicle_style
    size = request.size
    focus = request.focus
    is_luxury = request.is_luxury
    transmission = request.transmission
    fuel_type = request.fuel_type
    
    # 1. Dynamic Features — Use the RAW Lakhs budget for tier detection!
    #    (Because the USD conversion applies tax discounts that hide the true tier)
    
    if budget_lakhs >= 150:
        # HYPERCAR TIER: ₹1.5 Cr+ (Bugatti, Lamborghini, McLaren territory)
        hp, cyl, hwy_mpg, city_mpg = 650, 12, 14, 10
        is_perf = 1
        is_luxury = True
    elif budget_lakhs >= 60:
        # LUXURY TIER: ₹60L - ₹1.5 Cr (BMW M-Series, Audi RS, Mercedes AMG)
        hp, cyl, hwy_mpg, city_mpg = 400, 6, 24, 17
        is_perf = 1
        is_luxury = True
    elif fuel_type == 'electric':
        hp, cyl, hwy_mpg, city_mpg = 250, 0, 105, 100
        is_perf = 1 if focus == 'performance' else 0
    elif focus == 'efficiency':
        hp, cyl, hwy_mpg, city_mpg = 130, 4, 45, 40
        is_perf = 0
    elif focus == 'performance':
        hp, cyl, hwy_mpg, city_mpg = 350, 6, 22, 16
        is_perf = 1
    else: # balanced
        hp, cyl, hwy_mpg, city_mpg = 200, 4, 30, 24
        is_perf = 0

    user_car = {
        'Make': 'Toyota',             
        'Vehicle Size': size,
        'Vehicle Style': vehicle_style,
        'Driven_Wheels': 'rear wheel drive' if focus == 'performance' else 'front wheel drive',
        'Transmission Type': transmission,
        'Engine Fuel Type': fuel_type,
        'Year': 2017,                   
        'Engine HP': hp,
        'Engine Cylinders': cyl,
        'Number of Doors': 4 if '4dr' in vehicle_style or vehicle_style == 'Sedan' else 2,
        'highway MPG': hwy_mpg,
        'city mpg': city_mpg,
        'Popularity': 1500,           
        'MSRP': budget,
        'Engine_HP_missing': 0,
        'Crossover': 0, 'Diesel': 0, 'Exotic': 1 if budget_lakhs >= 150 else 0, 'Factory Tuner': 0, 'Flex Fuel': 0,
        'Hatchback': 0, 'High-Performance': is_perf, 'Hybrid': 0, 
        'Luxury': int(is_luxury), 'Performance': is_perf, 'Unknown': 0
    }
    
    user_df = pd.DataFrame([user_car])
    
    user_df['log_MSRP'] = np.log1p(user_df['MSRP'])
    user_df['log_Engine_HP'] = np.log1p(user_df['Engine HP'])
    
    num_cols = ['log_MSRP', 'log_Engine_HP', 'Engine Cylinders', 'highway MPG', 
                'city mpg', 'Popularity', 'Year', 'Number of Doors']
    user_df[num_cols] = scaler.transform(user_df[num_cols])
    
    cat_cols = ['Make', 'Vehicle Size', 'Vehicle Style', 'Driven_Wheels', 
                'Transmission Type', 'Engine Fuel Type']
    encoded_cats = ohe.transform(user_df[cat_cols])
    encoded_df = pd.DataFrame(encoded_cats, columns=ohe.get_feature_names_out(cat_cols))
    
    drop_cols = cat_cols + ['MSRP', 'Engine HP'] 
    final_user_vector = pd.concat([user_df.drop(drop_cols, axis=1), encoded_df], axis=1)
    
    final_user_vector = final_user_vector.reindex(columns=feature_matrix.columns, fill_value=0)
    
    brand_cols = [col for col in final_user_vector.columns if 'Make_' in col]
    final_user_vector[brand_cols] = 0
    
    weights = np.ones(len(feature_matrix.columns))
    
    fuel_col = f'Engine Fuel Type_{fuel_type}'
    if fuel_col in feature_matrix.columns:
        idx = feature_matrix.columns.get_loc(fuel_col)
        weights[idx] = 10.0
        
    style_col = f'Vehicle Style_{vehicle_style}'
    if style_col in feature_matrix.columns:
        idx = feature_matrix.columns.get_loc(style_col)
        weights[idx] = 5.0

    weighted_user_vector = final_user_vector * weights
    weighted_feature_matrix = feature_matrix * weights
    
    sim_scores = cosine_similarity(weighted_user_vector, weighted_feature_matrix)[0]
    
    sim_scores_list = list(enumerate(sim_scores))
    sorted_scores = sorted(sim_scores_list, key=lambda x: x[1], reverse=True)
    top_matches = sorted_scores[:150]

    top_indices = [match[0] for match in top_matches]
    
    # We must grab all original scaled columns to properly UN-SCALE them
    num_cols = ['log_MSRP', 'log_Engine_HP', 'Engine Cylinders', 'highway MPG', 'city mpg', 'Popularity', 'Year', 'Number of Doors']
    
    selected_columns = ['Make', 'Model', 'MSRP', 'Engine HP', 'Vehicle Style', 'Engine Fuel Type'] + num_cols
    
    # 1. Grab the top matching cars from the dataframe
    recommendations = df.iloc[top_indices][selected_columns].copy()
    recommendations = recommendations.drop_duplicates(subset=['Make', 'Model'])
    
    # ── FIX 6: EV HARD FILTER ──
    # When user selects 'electric', EVs MUST come first — not petrol hybrids.
    # Diesel/Premium already work fine via cosine similarity weights.
    if 'electric' in fuel_type.lower():
        ev_matches = recommendations[recommendations['Engine Fuel Type'].str.lower().str.contains('electric', na=False)]
        if len(ev_matches) >= 3:
            recommendations = ev_matches
        else:
            # Fallback: include hybrids if not enough pure EVs in budget
            ev_or_hybrid = recommendations[
                recommendations['Engine Fuel Type'].str.lower().str.contains('electric|hybrid', na=False)
            ]
            if len(ev_or_hybrid) > 0:
                recommendations = ev_or_hybrid
    
    # ── FIX: Apply minimum MSRP floors per brand tier ──
    # Old cars (1990s) have absurdly low MSRPs ($2k) which produce ₹1.82L Mercedes.
    # We set realistic floor prices based on brand segment.
    LUXURY_MAKES = {'Mercedes-Benz', 'BMW', 'Audi', 'Porsche', 'Lexus', 'Jaguar',
                    'Land Rover', 'Maserati', 'Bentley', 'Rolls-Royce', 'Lamborghini',
                    'Ferrari', 'Aston Martin', 'McLaren', 'Bugatti', 'Genesis',
                    'Alfa Romeo', 'Infiniti', 'Acura', 'Lincoln', 'Cadillac', 'Volvo'}
    MID_MAKES = {'Toyota', 'Honda', 'Mazda', 'Subaru', 'Volkswagen', 'Hyundai',
                 'Kia', 'Nissan', 'Ford', 'Chevrolet', 'Buick', 'Chrysler', 'Dodge',
                 'Jeep', 'GMC', 'Ram'}
    
    def get_msrp_floor(make):
        if make in LUXURY_MAKES:
            return 25000   # Luxury cars: minimum $25,000 US MSRP
        elif make in MID_MAKES:
            return 15000   # Mid-range: minimum $15,000
        else:
            return 8000    # Economy: minimum $8,000
    
    recommendations['MSRP_Floored'] = recommendations.apply(
        lambda row: max(row['MSRP'], get_msrp_floor(row['Make'])), axis=1
    )
    
    # Use Indian tax multiplier per car (based on its US MSRP tier + fuel type)
    from schemas import get_india_tax_multiplier, EXCHANGE_RATE
    
    # Base price = raw conversion using floored MSRP (Ex-Showroom equivalent)
    recommendations['Base_Price_Lakhs'] = (recommendations['MSRP_Floored'] * EXCHANGE_RATE / 100000).round(2)
    
    # On-Road price = with Indian import duty + GST + cess
    def compute_indian_price(row):
        multiplier = get_india_tax_multiplier(row['MSRP_Floored'], row.get('Engine Fuel Type', ''))
        return round((row['MSRP_Floored'] * EXCHANGE_RATE * multiplier) / 100000, 2)
    
    recommendations['Expected_Price_Lakhs'] = recommendations.apply(compute_indian_price, axis=1)
    
    # ── FIX 1: YEAR FILTER — Remove ancient cars (pre-2010) ──
    # The dataset contains 1990s-2000s cars that are discontinued/unavailable in India.
    # A modern buyer should not be recommended a 1994 Oldsmobile or 2002 Infiniti.
    # We un-scale Year early just for filtering (will be overwritten later for final output)
    year_col_idx = num_cols.index('Year')
    raw_years = scaler.inverse_transform(recommendations[num_cols])[:, year_col_idx].astype(int)
    recommendations['_temp_year'] = raw_years
    recommendations = recommendations[recommendations['_temp_year'] >= 2010]
    recommendations = recommendations.drop(columns=['_temp_year'])
    
    # ── FIX 2: SMART BUDGET RANGE FILTER ──
    # Tiered approach — tight for low budgets, wide for luxury/ultra-luxury
    budget = request.budget_in_lakhs
    max_price = budget * 1.3
    
    if budget >= 100:
        # Luxury/Ultra-luxury: wide range — show everything from mid-premium to max
        min_price = budget * 0.15
    elif budget >= 50:
        # Premium: moderate range
        min_price = budget * 0.25
    else:
        # Economy/Mid: tight range to avoid cheap filler
        min_price = budget * 0.4
    
    filtered_recs = recommendations[
        (recommendations['Expected_Price_Lakhs'] <= max_price) &
        (recommendations['Expected_Price_Lakhs'] >= min_price)
    ]
    
    # ── FIX 3: SMART FALLBACK FOR NARROW BUDGETS ──
    # If the min_price floor was too strict and filtered out everything,
    # try relaxing the minimum floor and just using the max_price cap.
    if len(filtered_recs) == 0:
        fallback = recommendations[recommendations['Expected_Price_Lakhs'] <= max_price]
        if len(fallback) == 0:
            # If STILL zero, it means every single car is more expensive than the max budget.
            # Return empty so the user knows they need to increase their budget.
            return []
        recommendations = fallback
    else:
        recommendations = filtered_recs
    
    # 2. UN-SCALE THE NUMERIC COLUMNS
    # Because 'highway MPG' and 'Year' were scaled between 0 and 1, we must reverse the math!
    unscaled_nums = scaler.inverse_transform(recommendations[num_cols])
    
    # 'highway MPG' is the 4th column (Index 3), 'Year' is the 7th column (Index 6)
    recommendations['true_highway_MPG'] = unscaled_nums[:, 3]
    recommendations['Year'] = unscaled_nums[:, 6].astype(int)
    
    # --- COST OF OWNERSHIP CALCULATOR ---
    yearly_km = request.yearly_km
    # Conversion: 1 US MPG = 0.425144 km/Liter (Using the TRUE unscaled MPG!)
    recommendations['km_per_liter'] = recommendations['true_highway_MPG'] * 0.425144
    
    def calculate_5_year_cost(row):
        fuel = str(row['Engine Fuel Type']).lower()
        
        # Avoid division by zero
        kmpl = row['km_per_liter'] if row['km_per_liter'] > 0 else 10.0 
        
        if 'electric' in fuel:
            # EVs: heavily efficient, approx 1.5 INR per km
            return (yearly_km * 5 * 1.5) / 100000.0 
        elif 'premium' in fuel:
            # Premium Petrol: Approx 110 INR per L
            liters_needed = (yearly_km * 5) / kmpl
            return (liters_needed * 110) / 100000.0
        elif 'diesel' in fuel:
            # Diesel: Approx 90 INR per L
            liters_needed = (yearly_km * 5) / kmpl
            return (liters_needed * 90) / 100000.0
        else:
            # Regular Petrol: Approx 100 INR per L
            liters_needed = (yearly_km * 5) / kmpl
            return (liters_needed * 100) / 100000.0

    # Apply the math and round to 2 decimals for Lakhs
    recommendations['5_Year_Fuel_Cost_Lakhs'] = recommendations.apply(calculate_5_year_cost, axis=1).round(2)
    
    # Create the 'Wow Factor' string for the UI frontend to display
    recommendations['Ownership_Wow_Factor'] = "5-Year Fuel Cost: ₹" + recommendations['5_Year_Fuel_Cost_Lakhs'].astype(str) + " Lakhs"

    # Only return the columns the Frontend actually cares about displaying
    final_output_cols = ['Make', 'Model', 'Year', 'MSRP', 'Base_Price_Lakhs', 'Expected_Price_Lakhs', 'true_highway_MPG', 'km_per_liter', 'Engine HP', 'Vehicle Style', 'Engine Fuel Type', '5_Year_Fuel_Cost_Lakhs', 'Ownership_Wow_Factor']
    
    # ── FIX 4: BUDGET-PROXIMITY SORT ──
    # Instead of cheapest-first (which shows ₹37L Pontiac for a ₹150L budget),
    # sort by how close the price is to the user's budget. Best-value-for-money first.
    recommendations['_budget_distance'] = abs(recommendations['Expected_Price_Lakhs'] - request.budget_in_lakhs)
    recommendations = recommendations.sort_values('_budget_distance', ascending=True)
    recommendations = recommendations.drop(columns=['_budget_distance'])
    
    final_recs = recommendations[final_output_cols].head(top_n)
    final_recs = final_recs.replace({np.nan: None})
    
    return final_recs.to_dict(orient='records')
