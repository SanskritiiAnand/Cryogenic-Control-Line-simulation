"""
Thermal load calculation module for cryogenic coaxial control lines.
Computes conducive heat transport and microwave power dissipation per stage
"""
from typing import Dict, Union, Optional
import numpy as np
from config import Stage_Temps
from src.attenuation import db_to_transmittance

def stainless_steel(T: float) -> float:
    """
    Fit for satinless steel 304 thermal conductivity (W/m*K) from 0.01K to 300K
    """
    T= max(T, 1e-3)
    if T < 1.0:
        return 0.08 * T
    elif T < 10.0:
        return 0.06 * (T**1.3)
    else: 
        return 0.5 * (T**0.6)

def beryllium_copper(T: float) -> float:
    """
    fit for Beryllium Copper (BeCu) thermal conductivity (W/(m*K)) from 0.01K to 300K
    """
    T= max(T, 1e-3)
    if T < 4.0:
        return 0.15 * T
    elif T < 20.0:
        return 0.10 * (T**1.2)
    else:
        return 1.2 * (T**0.5)

def niobium_titanium(T: float) -> float:
    """
    Fit for Niobium Titanium (NbTi) superconducting coax thermal conductivity (W/(m*K))
    """
    T= max(T, 1e-3)
    Tc= 9.2 #Critical temperature

    if T >= Tc:
        return 0.05 * (T ** 0.85)
    else:
        return 0.001 * (T ** 2.2)

def integrated_conducive_heat_load(t_hot: float, t_cold: float, length: float= 0.1, area: float= 1e-6, material: str= "stainless_steel") -> float:
    """
    Calculates conducive heat load (Q_cond) via numerical integral of k(T)dT:
    Q_cond= (A/L) * integral_{T_cold}^{T_hot} k(T)dT
    """
    if material == "stainless_steel":
        k_func= stainless_steel
    elif material in ("becu", "beryllium_copper"):
        k_func= beryllium_copper
    elif material in ("nbti", "niobium_titanium"):
        k_func= niobium_titanium
    else:
        raise ValueError(f"Unknown material '{material}'. Choose 'stainless_steel', 'becu', or 'nbti'.")

    #numerical integration using NumPy trapezoidal rule over 200 temperature slices
    t_steps= np.linspace(t_cold, t_hot, 200)
    k_vals= np.array([k_func(t) for t in t_steps])
    k_integral= np.trapezoid(k_vals, t_steps)

    return (area/length) * k_integral

def conducive_heat_load(t_hot: float, t_cold: float, length: float=0.1, area: float=1e-6, avg_k: float=1.0, material: Optional[str]= None) -> float:
    """
    Calculates conducive heat load (Q_cond) across a cable segment in Watts
    Q_cond= avg_k * (A/L) * (T_hot- T_cold)

    Parameters:
     t_hot: temperature at upper stage boundary (K)
     t_cold: temperature at lower stage boundary (K)
     length: segment length in meters
     area: cross-sectional area of coaxial conductors in square meters
     avg_k: effective/average thermal conductivity (W/(m*K))
    """
    if t_hot < t_cold:
        raise ValueError("t_hot must be greater than or equal to t_cold")

    if length <= 0 or area <= 0:
        raise ValueError("length and area must be positive")

    if material is not None:
        return integrated_conducive_heat_load(t_hot=t_hot, t_cold=t_cold, length=length, area=area, material=material)

    return avg_k * (area/length) * (t_hot - t_cold)

def rf_dissipation_heat_load(P_watts: float, attenuation_dB: float, duty_cycle: float=1.0) -> float:
    """
    Calculates RF power dissipated as heat in an attenuator stage in Watts

    Q_RF= P_in * (1-eta) * duty_cycle
    """
    if not (0.0 <= duty_cycle <= 1.0):
        raise ValueError("Duty cycle must be between 0.0 and 1.0")

    eta= db_to_transmittance(attenuation_dB)
    P_dissipated= P_watts * (1.0 - eta)

    return P_dissipated * duty_cycle

def stage_total_heat_load(t_hot: float, t_cold: float, attenuation_dB: float, P_watts: float, length: float=0.1, area: float=1e-6, avg_k: float=1.0, duty_cycle: float=1.0, material: Optional[str]= None) -> Dict[str, float]:
    """
    Computes total thermal load breakdown (conducive + RF dissipation) for a single stage
    Returns dictionary containing 'Q_cond', 'Q_RF', and 'Q_total' in watts
    """
    Q_cond= conducive_heat_load(t_hot=t_hot, t_cold=t_cold, length=length, area=area, avg_k=avg_k, material=material)

    Q_rf= rf_dissipation_heat_load(P_watts=P_watts, attenuation_dB=attenuation_dB, duty_cycle=duty_cycle)

    Q_Total= Q_cond + Q_rf
    return {"Q_cond": Q_cond, "Q_RF": Q_rf, "Q_Total": Q_Total}