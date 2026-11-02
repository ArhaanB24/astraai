from typing import Dict, Any


def calculate_cagr(initial_value: float, final_value: float, years: float) -> Dict[str, Any]:
    """
    Calculates Compound Annual Growth Rate (CAGR).
    Formula: CAGR = (Final Value / Initial Value) ** (1 / Years) - 1
    """
    if initial_value <= 0:
        return {
            "success": False,
            "error_code": "INVALID_AMOUNT",
            "message": "Initial investment value must be greater than zero."
        }
    if final_value < 0:
        return {
            "success": False,
            "error_code": "INVALID_AMOUNT",
            "message": "Final investment value cannot be negative."
        }
    if years <= 0:
        return {
            "success": False,
            "error_code": "INVALID_TIME_PERIOD",
            "message": "Time period in years must be greater than zero."
        }

    cagr = ((final_value / initial_value) ** (1.0 / years)) - 1.0
    return {
        "success": True,
        "cagr_percentage": round(float(cagr * 100.0), 2),
        "cagr_decimal": float(cagr),
        "initial_value": float(initial_value),
        "final_value": float(final_value),
        "years": float(years)
    }
