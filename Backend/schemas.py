from pydantic import BaseModel, Field, computed_field
from typing import Literal

EXCHANGE_RATE = 91.0

# Indian Tax Multipliers (US MSRP → Approximate Indian On-Road Price)
# Based on actual GST (18-40%) + Import Duty (15-110%) + Cess structure
# 
# Tier 1: Economy (locally manufactured in India) → ~1.0x of raw conversion
# Tier 2: Mid-range (local + some import) → ~1.3x
# Tier 3: Premium (CKD assembled) → ~1.5x
# Tier 4: Luxury (CKD/CBU) → ~1.9x
# Tier 5: Ultra-Luxury (fully imported CBU) → ~2.5x
# EVs: Special 5% GST bracket → ~1.15x

def get_india_tax_multiplier(msrp_usd, fuel_type=''):
    """Returns the multiplier to convert US MSRP to approximate Indian on-road price."""
    if 'electric' in str(fuel_type).lower():
        return 1.15   # EVs get only 5% GST — massive incentive
    elif msrp_usd > 100000:
        return 2.5    # Ultra-luxury CBU: 70% BCD + 40% AIDC + 40% GST
    elif msrp_usd > 55000:
        return 1.9    # Luxury: high import + 40% GST + cess
    elif msrp_usd > 35000:
        return 1.5    # Premium CKD: 15% CKD duty + 40% GST
    elif msrp_usd > 20000:
        return 1.3    # Mid-range: partial local + 28-40% GST
    else:
        return 1.0    # Economy: locally made, 18% GST


def get_budget_divisor(budget_lakhs):
    """Reverse-maps Indian budget to approximate US MSRP range for model matching."""
    if budget_lakhs >= 200:
        return 2.5
    elif budget_lakhs >= 80:
        return 1.9
    elif budget_lakhs >= 40:
        return 1.5
    elif budget_lakhs >= 15:
        return 1.3
    else:
        return 1.0


class CarRecommendationRequest(BaseModel):
    budget_in_lakhs: float = Field(..., description="User's budget in Lakhs (INR)")
    vehicle_style: str = Field(..., description="Style of the vehicle (e.g., Sedan, 4dr SUV)")
    size: str = Field(..., description="Size class (e.g., Compact, Midsize, Large)")
    focus: Literal['efficiency', 'performance', 'balanced']
    is_luxury: bool
    transmission: str = Field("AUTOMATIC", description="Transmission type")
    fuel_type: str = Field("regular unleaded", description="Fuel type constraint")
    
    yearly_km: int = Field(default=15000, description="Annual driving distance in km to calculate ownership cost")

    @computed_field
    @property
    def budget_usd(self) -> int:
        # 1. Convert Lakhs → raw INR → raw USD
        raw_usd = (self.budget_in_lakhs * 100000) / EXCHANGE_RATE
        
        # 2. Divide by the tax multiplier to find what US MSRP this budget can actually buy
        #    e.g., ₹100L budget / 1.9 multiplier = ~$57k US car (which shows as ~₹100L in India)
        divisor = get_budget_divisor(self.budget_in_lakhs)
        return int(raw_usd / divisor)
