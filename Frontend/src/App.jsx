import React, { useState } from 'react';
import {
  Car, Fuel, Gauge, Settings, Activity, ChevronRight, ChevronDown,
  ArrowLeft, Zap, MapPin, X, TrendingUp, DollarSign
} from 'lucide-react';
import './index.css';

const API_URL = 'http://13.201.70.18:8000/api/cars/recommend';

// Helpers
function fuelBadgeClass(fuelType) {
  if (!fuelType) return 'fuel-badge petrol';
  const f = fuelType.toLowerCase();
  if (f.includes('electric')) return 'fuel-badge electric';
  if (f.includes('diesel')) return 'fuel-badge diesel';
  if (f.includes('premium')) return 'fuel-badge premium';
  return 'fuel-badge petrol';
}

function fuelLabel(fuelType) {
  if (!fuelType) return 'Petrol';
  const f = fuelType.toLowerCase();
  if (f.includes('electric')) return '⚡ Electric';
  if (f.includes('diesel')) return '🛢️ Diesel';
  if (f.includes('premium')) return '🔥 Premium';
  return '⛽ Petrol';
}

function carImageUrl(vehicleStyle) {
  if (!vehicleStyle) return '/sedan.png';
  const style = vehicleStyle.toLowerCase();

  if (style.includes('suv')) return '/suv.png';
  if (style.includes('pickup') || style.includes('truck')) return '/truck.png';
  if (style.includes('hatchback')) return '/hatchback.png';
  if (style.includes('wagon')) return '/wagon.png';
  if (style.includes('coupe')) return '/coupe.png';
  if (style.includes('convertible')) return '/convertible.png';

  // Return sedan for Sedan and anything else
  return '/sedan.png';
}

// ────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState('form');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState(null);

  const [form, setForm] = useState({
    budget_in_lakhs: 20,
    vehicle_style: 'Sedan',
    size: 'Compact',
    focus: 'efficiency',
    is_luxury: false,
    transmission: 'AUTOMATIC',
    fuel_type: 'regular unleaded',
    yearly_km: 15000,
  });

  const set = (key) => (e) => {
    const val = e.target.type === 'checkbox'
      ? e.target.checked
      : e.target.type === 'range'
        ? Number(e.target.value)
        : e.target.value;
    setForm(prev => ({ ...prev, [key]: val }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      setResults(data);
      setPage('results');
    } catch (err) {
      console.error('Fetch failed:', err);
      alert('Could not reach the backend. Make sure FastAPI is running on port 8000.');
    }
    setLoading(false);
  };

  // ─── PAGE 1: HERO + FORM ─────────────────────
  if (page === 'form') {
    return (
      <div className="hero-section">
        {/* Transparent car BG */}
        <div className="hero-bg-car" />

        <div className="hero-brand">
          <Car size={32} strokeWidth={2.5} />
          <span>DriveIQ</span>
        </div>

        <h1 className="hero-title">
          Find Your <span className="highlight">Dream Car</span>
        </h1>
        <p className="hero-subtitle">
          Tell us what you love — and our AI will find the perfect match from 11,000+ vehicles,
          complete with a 5‑year fuel cost breakdown.
        </p>

        {/* FORM CARD */}
        <div className="form-card">
          <h2>🏎️ Your Preferences</h2>

          <form className="form-grid" onSubmit={handleSubmit}>
            {/* Budget */}
            <div className="form-group full-width">
              <label>
                Budget: <span className="value-display">₹{form.budget_in_lakhs} Lakhs</span>
              </label>
              <input type="range" min="5" max="200" step="5"
                value={form.budget_in_lakhs} onChange={set('budget_in_lakhs')} />
              <div className="flex justify-between text-xs text-stone-600 mt-1">
                <span>₹5L</span><span>₹2 Cr</span>
              </div>
            </div>

            {/* Yearly KM */}
            <div className="form-group full-width">
              <label>
                Annual Distance: <span className="value-display">{form.yearly_km.toLocaleString()} km</span>
              </label>
              <input type="range" min="5000" max="50000" step="1000"
                value={form.yearly_km} onChange={set('yearly_km')} />
              <div className="flex justify-between text-xs text-stone-600 mt-1">
                <span>5,000 km</span><span>50,000 km</span>
              </div>
              <small>Powers the 5‑year fuel ownership calculator</small>
            </div>

            {/* Body Style */}
            <div className="form-group">
              <label>Body Style</label>
              <select value={form.vehicle_style} onChange={set('vehicle_style')}>
                <option value="Sedan">Sedan</option>
                <option value="4dr SUV">SUV (4 Door)</option>
                <option value="Coupe">Coupe</option>
                <option value="Convertible">Convertible</option>
                <option value="4dr Hatchback">Hatchback</option>
                <option value="Crew Cab Pickup">Pickup Truck</option>
                <option value="Wagon">Wagon</option>
              </select>
            </div>

            {/* Size */}
            <div className="form-group">
              <label>Size</label>
              <select value={form.size} onChange={set('size')}>
                <option value="Compact">Compact</option>
                <option value="Midsize">Midsize</option>
                <option value="Large">Large</option>
              </select>
            </div>

            {/* Focus */}
            <div className="form-group">
              <label>Primary Focus</label>
              <select value={form.focus} onChange={set('focus')}>
                <option value="efficiency">🌿 Fuel Efficiency</option>
                <option value="balanced">⚖️ Balanced</option>
                <option value="performance">🏎️ Performance</option>
              </select>
            </div>

            {/* Fuel Type */}
            <div className="form-group">
              <label>Fuel Type</label>
              <select value={form.fuel_type} onChange={set('fuel_type')}>
                <option value="regular unleaded">Petrol (Regular)</option>
                <option value="premium unleaded (required)">Petrol (Premium)</option>
                <option value="diesel">Diesel</option>
                <option value="electric">Electric (EV)</option>
              </select>
            </div>

            {/* Transmission */}
            <div className="form-group">
              <label>Transmission</label>
              <select value={form.transmission} onChange={set('transmission')}>
                <option value="AUTOMATIC">Automatic</option>
                <option value="MANUAL">Manual</option>
                <option value="DIRECT DRIVE">Direct Drive (EV)</option>
              </select>
            </div>

            {/* Luxury */}
            <div className="form-group flex justify-center items-end">
              <div className="checkbox-row">
                <input type="checkbox" id="lux" checked={form.is_luxury} onChange={set('is_luxury')} />
                <label htmlFor="lux">Luxury Features</label>
              </div>
            </div>

            <button type="submit" className="btn-find" disabled={loading}>
              {loading
                ? <><div className="spinner" /> Analyzing…</>
                : <>Find My Cars <ChevronRight size={20} /></>
              }
            </button>
          </form>
        </div>
        <p className="mt-16 mb-4 text-sm text-stone-600 z-10">
          Powered by Cosine Similarity &amp; Content‑Based Filtering
        </p>
      </div>
    );
  }

  // ─── LOADING ─────────────────────────────────
  if (loading) {
    return (
      <div className="results-page">
        <div className="loading-screen">
          <Car size={80} className="loading-car" />
          <p>Crunching 11,000+ vehicles…</p>
          <div className="loading-bar"><div className="loading-bar-fill" /></div>
        </div>
      </div>
    );
  }

  // ─── PAGE 2: RESULTS ─────────────────────────
  return (
    <div className="results-page">
      <button className="back-btn" onClick={() => setPage('form')}>
        <ArrowLeft size={18} /> Modify Preferences
      </button>

      <div className="results-header">
        <h1>🎯 Top Matches for You</h1>
        <p>
          ₹{form.budget_in_lakhs}L budget · {form.vehicle_style} · {form.focus} focus · {form.yearly_km.toLocaleString()} km/yr
        </p>
      </div>

      {/* CAR CARDS */}
      {results.length === 0 ? (
        <div className="ownership-cta" style={{ marginTop: '1rem' }}>
          <h3>😕 No Matches Found</h3>
          <p>
            We couldn't find cars matching your exact criteria within your ₹{form.budget_in_lakhs}L budget.
            Try adjusting your budget, body style, or fuel type.
          </p>
          <button className="btn-ownership" onClick={() => setPage('form')}>
            <ArrowLeft size={20} /> Adjust Preferences
          </button>
        </div>
      ) : (
        <div className="cars-grid">
          {results.map((car, i) => (
            <div key={i} className="car-card">
              <div className="car-image-wrapper">
                <img
                  src={carImageUrl(car['Vehicle Style'])}
                  alt={`${car.Make} ${car.Model}`}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>

              <div className="card-body">
                <div className="card-top-row">
                  <div className="car-name">{car.Make} {car.Model}</div>
                  <span className="car-year">{Math.round(car.Year)}</span>
                </div>

                <div className="car-price-row">
                  <span className="rupee">₹</span>
                  <span className="price-val">{car.Expected_Price_Lakhs}</span>
                  <span className="price-unit">Lakhs</span>
                </div>
                <div className="flex items-center gap-2 mb-3 text-sm text-stone-500">
                  <span className="bg-stone-800 px-2 py-0.5 rounded text-xs text-stone-400">
                    Ex-Showroom: ₹{car.Base_Price_Lakhs}L
                  </span>
                  <span className="text-xs text-orange-600 font-semibold">incl. tax</span>
                </div>

                <div className="car-specs">
                  <div className="spec"><Activity size={16} /> {car['Engine HP']} HP</div>
                  <div className="spec"><Gauge size={16} /> {car.km_per_liter?.toFixed(1)} km/L</div>
                  <div className="spec"><Settings size={16} /> {car['Vehicle Style']}</div>
                  <div className="spec">
                    <span className={fuelBadgeClass(car['Engine Fuel Type'])}>
                      {fuelLabel(car['Engine Fuel Type'])}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* OWNERSHIP CTA */}
      {results.length > 0 && (
        <div className="ownership-cta">
          <h3>
            <DollarSign size={28} className="inline text-orange-500 mr-1" />
            Before You Decide…
          </h3>
          <p>
            The sticker price is just chapter one. Discover how much each car will
            <strong className="text-orange-400"> really cost you </strong>
            over 5 years of fuel — based on your {form.yearly_km.toLocaleString()} km/year driving habit.
          </p>
          <button className="btn-ownership" onClick={() => { setModalOpen(true); setExpandedIdx(null); }}>
            <TrendingUp size={20} /> Reveal 5‑Year Ownership Cost
          </button>
        </div>
      )}

      {/* SLIDE‑OUT MODAL */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>5‑Year Fuel Costs</h2>
              <button className="close-btn" onClick={() => setModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="yearly-km-badge">
              <MapPin size={16} /> Driving {form.yearly_km.toLocaleString()} km / year
            </div>

            {results.map((car, i) => {
              const isOpen = expandedIdx === i;
              const totalOwnership = (car.Expected_Price_Lakhs + car['5_Year_Fuel_Cost_Lakhs']).toFixed(2);
              const litersPerYear = car.km_per_liter > 0
                ? Math.round(form.yearly_km / car.km_per_liter)
                : 0;

              return (
                <div
                  key={i}
                  className={`cost-card ${isOpen ? 'expanded' : ''}`}
                  onClick={() => setExpandedIdx(isOpen ? null : i)}
                >
                  <div className="cost-card-header">
                    <span className="car-label">{car.Make} {car.Model}</span>
                    <ChevronDown size={20} className="expand-icon" />
                  </div>

                  {isOpen && (
                    <div className="cost-details">
                      <div className="cost-row">
                        <span className="cost-label"><Car size={16} /> Ex-Showroom (Base)</span>
                        <span className="cost-value">₹{car.Base_Price_Lakhs} L</span>
                      </div>
                      <div className="cost-row">
                        <span className="cost-label"><DollarSign size={16} /> On-Road (incl. Tax)</span>
                        <span className="cost-value text-orange-400">₹{car.Expected_Price_Lakhs} L</span>
                      </div>
                      <div className="cost-row">
                        <span className="cost-label"><Gauge size={16} /> Mileage</span>
                        <span className="cost-value">{car.km_per_liter?.toFixed(1)} km/L</span>
                      </div>
                      <div className="cost-row">
                        <span className="cost-label"><Fuel size={16} /> Fuel / Year</span>
                        <span className="cost-value">{litersPerYear.toLocaleString()} L</span>
                      </div>
                      <div className="cost-row fuel-highlight">
                        <span className="cost-label"><Zap size={16} /> 5‑Year Fuel Cost</span>
                        <span className="cost-value">₹{car['5_Year_Fuel_Cost_Lakhs']} L</span>
                      </div>
                      <div className="cost-row total">
                        <span className="cost-label">Total 5‑Year Ownership</span>
                        <span className="cost-value">₹{totalOwnership} L</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* FOOTER TERMS */}
      <div className="text-center mt-12 pb-6">
        <a href="#terms" className="text-[0.65rem] text-stone-500 hover:text-stone-400 transition-colors">
          *Terms &amp; Conditions: Prices are estimated based on MSRP conversion and may vary in india.
        </a>
      </div>
    </div>
  );
}
