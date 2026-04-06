# Drive IQ - Intelligent Car Recommendation System

Drive IQ is an intelligent, personalized car recommendation engine designed to bridge the gap between abstract user preferences and real-world vehicle markets. Utilizing a robust machine learning backend alongside a modern, interactive frontend, Drive IQ recommends optimal vehicles based on budget, style, focus (efficiency vs. performance), and luxury requirements.

A standout feature of this system is its **context-aware pricing model for the Indian market**, which intelligently translates US MSRP data into realistic Indian On-Road prices using dynamic, tiered tax brackets, import duties, and GST incentives. The complete containerized system is **successfully deployed in production on an AWS EC2 server.**

## 🏗️ Architecture & Tech Stack

The application is built using a modern decoupled architecture, containerized for reliable deployment.

### Tech Stack
* **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide React (Icons).
* **Backend:** Python, FastAPI, Pandas, NumPy, Scikit-learn, Joblib.
* **Deployment:** Docker, Docker Compose, AWS EC2.
* **ML Model:** Scikit-learn (Cosine Similarity, Data Scaling & One-hot encoding).

### Architecture
1. **Client (Vite/React):** An interactive UI where users configure their preferences (budget in Lakhs, style, size, powertrain).
2. **API (FastAPI):** A fast, asynchronous backend REST API that parses user requests, generates dynamic synthetic user profiles, and evaluates them against the ML model.
3. **ML Engine:** Computes cosine similarities between the generated user profile vector and a pre-processed dataset matrix of thousands of cars.
4. **Post-Processing Unit:** Handles complex price conversions, realistically floors MSRPs based on brand tiers, and applies Indian tax constraints before sorting and returning the final payload.

## 🧠 Model Performance & Similarity Search

The recommendation engine isn't a simple SQL query; it utilizes a multi-dimensional nearest-neighbor approach.

### Feature Engineering
The model transforms categorical data (`Make`, `Vehicle Style`, `Transmission Type`, etc.) using One-Hot Encoding and standardizes numerical fields (`MSRP`, `Engine HP`, `highway MPG`) using logarithmic scaling and MinMax/Standard scalers. 

### Cosine Similarity Search
When a user submits a query:
1. **Synthetic Profile Generation:** The backend constructs an "ideal" `user_car` profile. For example, a user wanting a "performance" car with a high budget yields a profile with high HP, rear-wheel drive, and lower MPG parameters automatically injected.
2. **Weighted Vectors:** The synthetic profile vector is weighted—for example, matching the exact `fuel_type` gets a `10.0x` prioritization multiplier, while `vehicle_style` gets a `5.0x` multiplier.
3. **Cosine Similarity Computation:** The system computes the cosine similarity between the weighted user profile and the entire pre-processed vehicle matrix.
4. **Proximity Sorting:** Instead of just returning the cheapest matching vehicles, the system sorts the highest similarity matches by **Budget Proximity**—ensuring the recommended vehicles are the best value for the *maximum* of the user's budget, rather than simply bottoming out.

## 💰 Indian Market Economics & Taxation

One of the largest hurdles in using open-source automotive datasets is that prices are usually reported in raw US MSRP, which means nothing for an Indian buyer. 

Drive IQ implements a highly realistic financial conversion engine tailored for India:

### MSRP to INR Conversion
The conversion relies on an active `EXCHANGE_RATE` (e.g., ₹91.0). However, direct conversion results in absurdly cheap luxury cars. Thus, a tiered system acts as an intermediary.

### Indian Taxes (GST, Duties, Cess)
We built a custom algorithm to approximate **Ex-Showroom & On-Road Prices** by reverse-mapping budgets to USD MSRP, and forward-mapping MSRPs to Indian INR.

The multipliers factor in GST (18%-40%), Import Duties (15%-110%), and compensation Cess based on the classification of the car:
* **Tier 1 (Economy):** ~1.0x multiplier (Locally manufactured, 18% GST).
* **Tier 2 (Mid-range):** ~1.3x multiplier (Partially local, 28-40% GST).
* **Tier 3 (Premium CKD):** ~1.5x multiplier (15% CKD duty + 40% GST).
* **Tier 4 (Luxury):** ~1.9x multiplier (High import duty + 40% GST + cess).
* **Tier 5 (Ultra-Luxury CBU):** ~2.5x multiplier (70% Basic Customs Duty + 40% AIDC + 40% GST. Think Lamborghini, Rolls-Royce).
* **Electric Vehicles (EVs):** Benefit from the massive 5% GST bracket, gaining a highly competitive ~1.15x multiplier.

### Cost of Ownership Calculator
The backend calculates a **5-Year Fuel Cost** (in Lakhs) based on the un-scaled real-world Highway MPG, converted to km/L, taking into account current petrol, diesel, and electricity EV rates.

## 🧗 Challenges Faced & Solutions

Building this pipeline required solving several critical edge cases:

1. **Ancient/Irrelevant Car Filtering**
   * *Challenge:* A ₹10 Lakh budget was returning 1994 Oldsmobiles and 2002 hatchbacks.
   * *Solution:* Implemented a strict floor to filter out any car manufactured before 2010 during the post-processing phase.
2. **Absurdly Low Luxury MSRPs**
   * *Challenge:* Base dataset contained data errors where older luxury cars (Mercedes-Benz, BMW) had MSRPs of $2,000, causing a Mercedes to be recommended for a ₹3 Lakh budget.
   * *Solution:* Implemented a **Brand Tier Price Floor** (`MSRP_Floored`). Luxury cars default to a minimum of $25,000 USD, Mid-range to $15,000, preventing data corruption from ruining recommendations.
3. **EV Hard Filtering & Hybrid Contamination**
   * *Challenge:* When users explicitly requested Electric Vehicles, petrol hybrids often overshadowed pure EVs due to similarity quirks.
   * *Solution:* Injected a hard-filter pass. If the user specifies "electric", pure EVs are forcibly ranked to the top. Hybrids are only utilized as a fallback if pure EVs are completely out of budget.
4. **Narrow Budget Choking**
   * *Challenge:* Tight minimum floors on budget queries sometimes resulted in zero matches.
   * *Solution:* Built a smart fallback range system. For luxury cars, the query width expands (15% min to 130% max), whereas economy cars have a tighter window (40% min to 130% max). If zero cars return, the minimum floor aggressively drops before gracefully handling a true empty state.

##  How to Run the Project

The easiest way to spin up the entire application is via Docker Compose.

### Prerequisites
* Docker & Docker Compose installed.

### Start the Application
```bash
# Start all containers in detached mode
docker-compose up -d --build
```
* **Frontend:** Accessible at `http://localhost:80`
* **Backend API:** Accessible at `http://localhost:8000`

### Running Manually

**Backend:**
```bash
cd Backend
pip install -r requirements.txt
fastapi dev main.py
```

**Frontend:**
```bash
cd Frontend
npm install
npm run dev
```
