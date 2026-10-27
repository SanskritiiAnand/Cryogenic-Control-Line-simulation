"""
Signal-to-Noise Ratio degradation tracking across multi-stage cryogenic lines
"""
from typing import List, Dict
import numpy as np
from config import def_freq, Stage_Temps, H, k_B
from src.attenuation import db_to_transmittance, thermal_noise_psd, propagate_stage_noise

def output_signal_power(P_watts: float, stage_attenuation_dB: List[float]) -> float:
    """
    Calculates attenuated signal power at the end of the line in Watts

    Parameters:
     P_watts: input microwave signal power at room temperature (W)
     stage_attenuation_dB: list of attenuation values in dB per stage
    """
    total_tranmittance= 1.0

    for att_dB in stage_attenuation_dB:
        total_tranmittance *= db_to_transmittance(att_dB)

    return P_watts * total_tranmittance

def cascaded_noise_psd(stage_temps: List[float], stage_attenuation_dB: List[float], t_room: float=300.0, freq: float= def_freq, include_quantum: bool= False) -> float:
    """
    Calculates total accumulated thermal noise power spectral density (W/Hz) at 10mK

    Parameters:
     stage_temps: list of stage temperatures (K) ordered from top to bottom 
     stage_attenuation_dB: list of stage attenuation values (dB)
     t_room: ambient room temperature netering the first stage (default 300K)
     freq: signal center frequency in Hz
    """
    if len(stage_temps) != len(stage_attenuation_dB):
        raise ValueError("stage_temps and stage_attenuation_dB must have equal length")

    #noise entering the top stage from room temperature
    current_noise_psd= thermal_noise_psd(temp= t_room, freq=freq, include_quantum=include_quantum)

    #cascade through each thermal stage sequentially
    for temp, att_db in zip(stage_temps, stage_attenuation_dB):
        current_noise_psd= propagate_stage_noise(input_noise_psd=current_noise_psd, attenuation_dB=att_db, stage_temp=temp, freq=freq, include_quantum=include_quantum)

    return current_noise_psd

def calculate_snr(P_watts: float, stage_temps: List[float], stage_attennuation_dB: List[float], bandwidth_hz: float=100.0e6, t_room: float=300.0, freq: float= def_freq, include_quantum: bool= False) -> Dict[str, float]:
    """
    Calculates final output signal power, total noise power, and SNR at the 10mK stage

    Parameters:
     P_watts: input RF power in Watts
     stage_temps: List of stage temperature in Kelvin
     stage_attenuation_dB: list of attenuation values in dB per stage
     bandwidth_hz: signal bandwidth in Hz (default 100 MHz)
     t_room: ambient entry temperature (K)
     freq: frequency in Hz

    Returns:
     Dict contaning 'P_sig', 'P_noise', 'snr_linear' and 'snr_dB'
    """
    P_sig= output_signal_power(P_watts, stage_attennuation_dB)
    S_noise= cascaded_noise_psd(stage_temps=stage_temps, stage_attenuation_dB=stage_attennuation_dB, t_room=t_room, freq=freq, include_quantum=include_quantum)
    P_noise= S_noise * bandwidth_hz

    if P_noise <= 0:
        snr_linear= float("inf")
        snr_dB= float("inf")
    else:
        snr_linear= P_sig / P_noise
        snr_dB= 10.0 * np.log10(snr_linear)

    #Transmon thermal population at 10mK mixing chamber (lowest stage)
    t_10mk= stage_temps[-1]
    exponent= (H * freq) / (k_B * t_10mk)

    if exponent > 700:
        n_th= 0.0
    else:
        n_th= 1.0 / (np.exp(exponent) - 1.0)

    p_excited= n_th / (2.0 * n_th + 1.0)

    return {"P_signal": P_sig, "P_noise": P_noise, "SNR_linear": snr_linear, "SNR_dB": snr_dB, "n_thermal_10mK": n_th, "P_excited_10mK": p_excited}
