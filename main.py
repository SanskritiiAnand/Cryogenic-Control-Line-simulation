"""
Execution controller and CLI validation for the Cryogenic Control Line Constraints Simulation.
Runs end-to-end simulations across dilution refrigerator thermal stages (4K down to 10mK), evaluating conducing heat load, RF attenuation dissipation, and output SNR degradation.
"""
from __future__ import annotations
import numpy as np
import argparse, json
from typing import Dict, Any
from config import Stage_Temps, def_freq, cable_deflen
from src.simulator import run_control_line
from src.sweeps import power_attenuation_sweep, evaluate_stage_constraints, plot_constraint_map, plot_snr_map

def format_watt_power(power_watts: float) -> str:
    """
    Formats raw power in Watts into readable microW, nanoW, picoW etc.
    """
    if power_watts >= 1e-3:
        return f"{power_watts * 1e3:.3f} mW"
    elif power_watts >= 1e-6:
        return f"{power_watts * 1e6:.3f} µW"
    elif power_watts >= 1e-9:
        return f"{power_watts * 1e9:.3f} nW"
    elif power_watts >= 1e-12:
        return f"{power_watts * 1e12:.3f} pW"
    elif power_watts >= 1e-15:
        return f"{power_watts * 1e15:.3f} fW"
    else:
        return f"{power_watts * 1e18:.3f} aW"

def simulation_report(results: Dict[str, Any]) -> None:
    """
    Prints a structured summary report of thermal loads and output SNr metrics to console.
    """
    print("====================================================")
    print("Cryogenic Control Line Constraints Simulation Report")
    print("====================================================")
    print(f"Input Power at 300K: {results['input_power_dbm']:.2f} dBm ({format_watt_power(results['input_power_watts'])})")
    print("\n---------------------------------------------------")
    print("Thermal Breakdown Per Stage:")
    print("-----------------------------------------------------")
    print(f"{'Stage': <10} | {'conductive (Q_cond)': <20} | {'RF Dissipated(Q_rf)': <20} | {'Total Heat Load': <18}")
    print("-" * 75)

    stage_breakdown= results["stage_thermal_breakdown"]
    for stage, q_data in stage_breakdown.items():
        q_cond_str= format_watt_power(q_data["Q_cond"])
        q_rf_str= format_watt_power(q_data["Q_RF"])
        q_total_str= format_watt_power(q_data["Q_Total"])
        print(f"{stage:<10} | {q_cond_str:<20} | {q_rf_str:<20} | {q_total_str:<18}")

    print("--------------------------------------------------")
    print("10mK Mixing Chamber & Qubit Output Metrics:")
    print("--------------------------------------------------")
    snr= results["snr_metrics"]
    print(f"Output Signal Power (P_sig): {format_watt_power(snr['P_signal'])}")
    print(f"Total Noise Power (P_noise): {format_watt_power(snr['P_noise'])}")
    print(f"Output SNR (linear):         {snr['SNR_linear']:.2e}")
    print(f"Output SNR (dB):             {snr['SNR_dB']:.2f} dB")

    if "n_thermal_10mK" in snr:
        print(f"Thermal Photon Occupancy(n_th): {snr['n_thermal_10mK']:.4e}")
        print(f"Excited State Population P(|1>): {snr['P_excited_10mK']:.4e}")

    #checking dilution fridge thermal constraints
    constraint= evaluate_stage_constraints(stage_breakdown)
    print("\n---------------------------------------------------")
    print("Dilution Refrigerator thermal Constraint Evaluation:")
    print("-----------------------------------------------------")
    if constraint["is_valid"]:
        print("STATUS: Acceptable operating region (all stages within thermal budget)")
    else:
        print("STATUS: thermal constraint violation detected")
        for stage, data in constraint["violations"].items():
            print(f"[!]{stage} Exceeded Budget: {format_watt_power(data['applied_load'])} > Limit {format_watt_power(data['budget_limit'])}")
    print("=====================================================")

def display_menu() -> None:
    print("==================================================")
    print(" Cryogenic Control Simulation ")
    print("==================================================")
    print("Select  a mode to run")
    print("1.Standard Cryogenic Simulation (Default Settings)")
    print("2.Custom Parameter Simulation")
    print("3.Parameter Sweep & Thermal Constraint Map")
    print("0.Exit")
    print("==================================================")

def get_input(prompt: str, default: float) -> float:
    user_in= input(f"{prompt} [default: {default}]: ").strip()
    if not user_in:
        return default
    try:
        return float(user_in)
    except ValueError:
        print(f"Invalid input. Using default value: {default}")
        return default

def get_bool_input(prompt: str, default: bool=False) -> bool:
    default_str= "y" if default else "n"
    user_in= input(f"{prompt} (y/n) [default: {default_str}]: ").strip().lower()
    if not user_in:
        return default
    return user_in in ("y", "yes")

def get_material_input() -> str:
    print("\nSelect Coaxial Cable Material:")
    print("1. Stainless Steel 304 (default)")
    print("2. Beryllium Copper (BeCu)")
    print("3. Superconducting NbTi")
    choice= input("Enter choice 1-3 [default: 1]: ").strip()
    if choice == "2":
        return "becu"
    elif choice == "3":
        return "nbti"
    return "stainless_steel"

def default_simulation() -> None:
    print("\nRunning default simulation setup...")
    stage_attenuation= {"4K": 10.0, "700mK": 10.0, "100mK": 10.0, "10mK": 20.0}

    results= run_control_line(P_in_dbm= -5.0, stage_attenuation=stage_attenuation, stage_temps=Stage_Temps, bandwidth=100.0 * 1e6, duty_cycle=0.5, freq=def_freq, include_quantum=False, material="stainless_steel")

    simulation_report(results)
    json_export(results)

def custom_simulation() -> None:
    print("\n--- Enter Parameters ---")
    p_in_dbm= get_input("Input Power at 300K (dBm)", -5.0)
    att_4k= get_input("Attenuation at 4K stage (dB)", 10.0)
    att_700mk= get_input("Attenuation at 700mK stage (dB)", 10.0)
    att_100mk= get_input("Attenuation at 100mK stage (dB)", 10.0)
    att_10mk= get_input("Attenuation at 10mK stage (dB)", 20.0)
    bandwidth= get_input("Bandwidth (MHz)", 100.0)
    duty_cycle= get_input("Duty Cycle (0.0 to 1.0)", 0.5)
    include_quantum= get_bool_input("Include Quantum Zero-Point Noise (1/2*hbar*omega)?", default=False)
    material= get_material_input()

    stage_attenuation= {"4K": att_4k, "700mK": att_700mk, "100mK": att_100mk, "10mK": att_10mk}

    print("\nRunning simulation with custom inputs...")

    results= run_control_line(P_in_dbm=p_in_dbm, stage_attenuation=stage_attenuation, stage_temps=Stage_Temps, bandwidth=bandwidth * 1e6, duty_cycle=duty_cycle, freq=def_freq, include_quantum=include_quantum, material=material)

    simulation_report(results)
    json_export(results)

def run_sweep_mode() -> None:
    print("\n--- Running Power vs Attenuation Constraint Sweep ---")
    material= get_material_input()
    num_lines= int(get_input("Number of Coaxial Control Lines", 24.0))
    include_quantum= get_bool_input("Include quantum noise zero-point floor?", default=False)

    #10 power steps x 10 attenuation steps
    p_range= np.linspace(-30.0, 10.0, 10)
    att_range= np.linspace(10.0, 60.0, 10)

    sweep_results= power_attenuation_sweep(p_in_dbm_range=p_range, total_att_db_range=att_range, material=material, include_quantum=include_quantum, num_lines=num_lines)

    valid_matrix= sweep_results["valid_operating_region"]

    print("\n=================================================")
    print(f"Operating Constraint Map ({material.upper()})")
    print(" [0]= Acceptable Thermal Operating Region")
    print(" [X]= Thermal Budget constraint Violation")
    print("===================================================")
    print(f"{'P_in (dBm)':<10} | "+" ".join([f"{att:>4.0f}dB" for att in att_range]))
    print("-" * 65)

    for i, p_val in enumerate(p_range):
        row_str= f"{p_val:>9.1f} |"
        for j in range(len(att_range)):
            row_str += "[0]" if valid_matrix[i,j] else "[X]" 
        print(row_str)
    print("===================================================")

    plot_choice= get_bool_input("\nDisplay GUI Heatmap Plot?", default=True)
    if plot_choice:
        plot_constraint_map(sweep_results, material=material, num_lines=num_lines, save_path=f"constraint_map_{material}_{num_lines}lines.png")
        plot_snr_map(sweep_results=sweep_results, material=material, num_lines=num_lines, save_path=f"snr_map_{material}_{num_lines}lines.png")

def json_export(results: Dict[str, Any]) -> None:
    export= input("Export raw results to JSON? (y/n)").strip().lower()
    if export in ("y", "Y"):
        filepath= (input("Enter output filename: ").strip())
        if not filepath:
            filepath= "sim_output.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, default=lambda x: float(x))
        print(f"Raw simulation metrics saved to: {filepath}")

def main() -> None:
    """
    Main application loop
    """
    while True:
        display_menu()
        choice= input("Enter option (0-3): ").strip()

        if choice=="1":
            default_simulation()
        elif choice=="2":
            custom_simulation()
        elif choice=="3":
            run_sweep_mode()
        elif choice=="0":
            print("\nExiting cryogenic control simulation")
            break
        else:
            print("\n[!] Invalid choice. Enter 0, 1, 2, or 3.\n")

        input("\nPress enter to return to main menu...")
        print("\n")

if __name__ == "__main__":
    main()