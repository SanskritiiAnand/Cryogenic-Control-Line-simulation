"""
Microwave signal attenuation and thermal noise propagation models across cryogenic satges.
"""
import numpy as np
from config import H, k_B, def_freq

def db_to_transmittance(attenuation_dB: float) -> float:
    """
    Converts attenuation in dB to linear power transmittance fraction (0 to 1)

    Parameters:
     attenuation_dB: positive float representing loss in dB
    """
    return 10.0 ** (-abs(attenuation_dB) / 10.0)

def thermal_noise_psd(temp: float, freq: float=def_freq, include_quantum: bool=False) -> float:
    """
    Calculates Johnson-Nyquist thermal noise power spectral density S_P(f, T) in W/Hz

    Parameters:
     temp: temperature (K)
     freq: frequency (Hz), default 5GHz
     include_quantum: if true, include zero-point energy (hf/2)
    """
    if temp <= 0:
        raise ValueError("Temperature must be strictly positive")

    exponent= (H * freq) / (k_B * temp)

    #avoid numerical overflow for extremely small T
    if exponent > 700:
        thermal_term= 0.0
    else:
        thermal_term= (H * freq) / (np.exp(exponent)-1.0)

    if include_quantum:
        return thermal_term + 0.5 * H * freq

    return thermal_term

def propagate_stage_noise(input_noise_psd: float, attenuation_dB: float, stage_temp: float, freq: float= def_freq, include_quantum: bool= False) -> float:
    """
    Calculates output noise power spectral density after an attenuator stage.
    S_out= eta * S_in + (1-eta) * S_noise(T_stage)
    """
    eta= db_to_transmittance(attenuation_dB)
    s_stage= thermal_noise_psd(temp=stage_temp, freq=freq, include_quantum=include_quantum)

    return eta * input_noise_psd + (1.0 - eta) * s_stage