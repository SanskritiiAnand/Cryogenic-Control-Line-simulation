"""
Parameter sweep and thermal constraint mapping engine for cryogenic control lines.
Evaluates thermal load violations against standard dilution refrigerator stage budgets.
"""
from typing import Dict, List, Any
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from config import Stage_Temps, def_freq
from src.simulator import run_control_line

#Standard commercial dilution refrigerator coolong power limits (in Watts)
STAGE_COOLING_BUDGETS= {"4K": 1.5, "700mK": 10.0e-3, "100mK": 100.0e-6, "10mK": 15.0e-6}

def evaluate_stage_constraints(stage_thermal_breakdown: Dict[str, Dict[str, float]], num_lines: int=24) -> Dict[str, Any]:
    """
    Compares total thermal loads across N lines against dilution fridge cooling budgets .
    Returns dictionary with per-stage headroom and overall constraint status.
    """
    violations= {}
    headroom= {}
    is_valid= True

    for stage, budgets in STAGE_COOLING_BUDGETS.items():
        if stage in stage_thermal_breakdown:
            q_total= stage_thermal_breakdown[stage]["Q_Total"] * num_lines
            margin= budgets - q_total
            headroom[stage]= margin

            if q_total > budgets:
                violations[stage]= { "applied_load": q_total, "budget_limit": budgets, "excess_load": q_total - budgets}
                is_valid= False

    return {"is_valid": is_valid, "headroom": headroom, "violations": violations}

def power_attenuation_sweep(p_in_dbm_range: np.ndarray, total_att_db_range: np.ndarray, freq: float= def_freq, duty_cycle: float=0.5, material: str= "stainless_steel", include_quantum: bool= False, num_lines: int=24) -> Dict[str, Any]:
    """
    Sweeps input power vs total attenuation across stages to generate an  operating constraint map.
    Parameters:
     p_in_dbm_range: array of input power levels in dBm
     total_att_db_range: array of total attenuation values in dB
     material: coax material ('stainless_steel', 'becu', 'nbti')
    """
    grid_size= (len(p_in_dbm_range), len(total_att_db_range))
    valid_map= np.zeros(grid_size, dtype=bool)
    snr_db_map= np.zeros(grid_size)
    heat_10mk_map= np.zeros(grid_size)

    for i, p_in in enumerate(p_in_dbm_range):
        for j, total_att in enumerate(total_att_db_range):
            stage_att= {"4K": total_att*0.40, "700mK": total_att*0.20, "100mK": total_att*0.20, "10mK": total_att*0.20}

            results= run_control_line(P_in_dbm=p_in, stage_attenuation=stage_att, stage_temps=Stage_Temps, bandwidth=100.0e6, duty_cycle=duty_cycle, freq=freq, include_quantum=include_quantum, material=material)

            constraint_status= evaluate_stage_constraints(results["stage_thermal_breakdown"], num_lines=num_lines)

            valid_map[i,j]= constraint_status["is_valid"]
            snr_db_map[i,j]= results["snr_metrics"]["SNR_dB"]
            heat_10mk_map[i,j]= results["stage_thermal_breakdown"]["10mK"]["Q_Total"] * num_lines

    return {"p_in_range": p_in_dbm_range, "att_range": total_att_db_range, "valid_operating_region": valid_map, "snr_db_grid": snr_db_map, "heat_10mk_grid": heat_10mk_map} 

def plot_constraint_map(sweep_results: Dict[str, Any], material: str="stainless_steel", num_lines: int=1, save_path: str=None) -> None:
    """
    Generates a 2D color-coded heatmap for cryogenic thermal operating constraints
    Green= safe/acceptable region; Red= thermal budget violation
    """
    p_range= sweep_results["p_in_range"]
    att_range= sweep_results["att_range"]

    valid_matrix= sweep_results["valid_operating_region"].astype(int)

    p_labels= [f"{p:.1f}" for p in p_range]
    att_labels= [f"{att:.0f}" for att in att_range]

    plt.figure(figsize=(10,7))

    cmap= sns.color_palette(["#e74c3c", "#2ecc71"])

    ax= sns.heatmap(valid_matrix, annot=False, cmap=cmap, cbar=False, xticklabels=att_labels, yticklabels=p_labels, linewidth=0.5, linecolor="white")
    ax.invert_yaxis()

    plt.title(f"Thermal Operating Constraint Map\nMaterial: {material.upper()} | Harness: {num_lines} Lines", fontsize=14, pad=15, fontweight="bold")
    plt.xlabel("total line attenuation (dB)", fontsize=12, labelpad=10)
    plt.ylabel("300K input power $P_{in}$ (dBm)", fontsize=12, labelpad=10)

    from matplotlib.patches import Patch

    legend_elements= [Patch(facecolor="#2ecc71", edgecolor="none", label="[0] Safe Operating Region"),
                      Patch(facecolor="#e74c3c", edgecolor="none", label="[X] Thermal Budget Violation")
                     ]
    plt.legend(handles=legend_elements, loc="upper right", frameon=True)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"\n[+] Constraint map plot saved to: {save_path}")

    plt.show()

def plot_snr_map(sweep_results: Dict[str, Any], material: str="stainless_steel", num_lines: int=1, save_path: str=None) -> None:
    """
    Plots side-by-side Heatmaps: SNR(dB) vs Thermal Constraint Map.
    """
    fig, axes= plt.subplots(1, 2, figsize=(16,6))

    p_labels= [f"{p:.1f}" for p in sweep_results["p_in_range"]]
    att_labels= [f"{att:.0f}" for att in sweep_results["att_range"]]

    #plot 1: output SNR (db)
    sns.heatmap(sweep_results["snr_db_grid"], ax=axes, cmap="viridis", annot=True, fmt=".1f", xticklabels= att_labels, yticklabels= p_labels, linewidths=0.5, linecolor="white")
    axes.invert_yaxis()
    axes.set_title(f"Output SNR (dB) - {material.upper()} | Harness: {num_lines} Lines", fontsize=12, fontweight="bold")
    axes.set_xlabel("Total Attenuation (dB)", fontsize=10)
    axes.set_ylabel("Input Power, P_in (dBm)", fontsize=10)

    plt.tight_layout()
    plt.show()