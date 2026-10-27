"""
Core simulation tying thermal heat load calculations and RF noise propagation into a unified cryogenic control line execution pipeline
"""
from typing import List, Dict, Any, Optional
import numpy as np
from config import Stage_Temps, def_freq
from src.thermal import stage_total_heat_load
from src.snr import calculate_snr, output_signal_power

def run_control_line(P_in_dbm: float, stage_attenuation: Dict[str, float], stage_temps: Dict[str, float]= Stage_Temps, cable_lengths: Optional[Dict[str, float]]=None, cable_areas: Optional[Dict[str, float]]=None, avg_k_values: Optional[Dict[str, float]]=None, bandwidth: float=100.0e6, duty_cycle: float=1.0, freq: float= def_freq, include_quantum: bool=False, material: Optional[str]= None) -> Dict[str, Any]:
    """
    Runs a complete thermal load and SNR constraint simulation across all cryogenic stages

    Parameters:
     P_in_dbm: input microwave power at 300K (dBm)
     stage_attenuation: map of stage names ('4K', '700mK' etc) to attenuator loss (in dB)
     stage_temps: map of stage names to Kelvin temperatures
     cable_lengths: map of stage names to cable segment lengths (m)
     cable_areas: map of stage names to conductor cross-sectional areas (m^2)
     avg_k_values: map of stage names to average thermal conductivities (W/(m*K))
     bandwidth: signal bandwidth in Hz (default 100 MHz)
     duty_cycle: control signal duty cycle fraction (0.0 to 1.0)
     freq: carrier signal frequency in Hz (default 5 GHz)

    Returns:
     Dict containing per-stage thermal breakdowns, total heat loads, and our SNR metrics.
    """
    #convert input power from dBm to Watts
    P_in_watts= (10.0 ** (P_in_dbm / 10.0)) / 1000.0

    stages= list(stage_temps.keys())
    temp_values= list(stage_temps.values())
    attenuation_values= [stage_attenuation.get(s, 0.0) for s in stages]

    #Default physical parameter fallback mappings
    if cable_lengths is None:
        cable_lengths= {s: 0.1 for s in stages}
    if cable_areas is None:
        cable_areas= {s: 1.0e-6 for s in stages}
    if avg_k_values is None:
        avg_k_values= {s: 1.0 for s in stages}

    stage_thermal_results= {}
    current_power= P_in_watts
    t_prev= 300.0  #room temperature entry point

    for stage in stages:
        t_curr= stage_temps[stage]
        att_dB= stage_attenuation.get(stage, 0.0)

        #dictionary fallbacks per key
        len_val= cable_lengths.get(stage, 0.1)
        area_val= cable_areas.get(stage, 1.0e-6)
        k_val= None if material else avg_k_values.get(stage, 1.0)

        #compute thermal load deposited at this stage
        thermal_data= stage_total_heat_load(t_hot=t_prev, t_cold=t_curr, attenuation_dB=att_dB, P_watts=current_power, length=cable_lengths.get(stage, 0.1), area=cable_areas.get(stage, 1.0e-6), avg_k=avg_k_values.get(stage, 1.0), duty_cycle=duty_cycle, material=material)

        stage_thermal_results[stage]= thermal_data

        #track RF power entering the next stage
        eta= 10.0 ** (-abs(att_dB) / 10.0)
        current_power *= eta
        t_prev= t_curr

    #compute line SNR at the 10mK mixing chamber
    snr_metrics= calculate_snr(P_watts=P_in_watts, stage_temps=temp_values, stage_attennuation_dB=attenuation_values, bandwidth_hz=bandwidth, t_room=300.0, freq=freq, include_quantum=include_quantum)

    return {"input_power_dbm": P_in_dbm, "input_power_watts": P_in_watts, "stage_thermal_breakdown": stage_thermal_results, "snr_metrics": snr_metrics}