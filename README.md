# Cryogenic Control Line Simulation

## Introduction
Superconducting quantum processors require carefully engineered microwave control lines to deliver high-fidelity signals from room-temperature electronics (300K)  to qubits operating at millikelvin temperatures. These transmission harnesses must satisfy stringent, competing engineering constraints: 
1. Mandatory line attenuation to suppress high-temperature thermal noise and protect quantum states.
2. Resulting microwave signal-power dissipation and phonon-mediated conductive heat transfer must remain strictly bounded within the finite, highly constrained cooling capacities of a multi-stage dilution refrigerator.

This repository presents an analytical, python-based simulation framework designed for rigorous multi-physics modeling of the thermal, thermodynamic, and microwave behaviour of coaxial control harnesses spanning from room-temperature down to the 10mK mixing chamber.

The simulation integrates three fundamental physical mechanisms:
* Thermal Transport: Conductive heat transfer ($Q_{\text{cond}}$) evaluated via temperature-dependent thermal conductivity integrals through coaxial cable segments anchored across intermediate cryogenic stages.
* Microwave Power Dissipation: Ohmic and dielectric thermal energy deposited by discrete attenuators ($Q_{\text{RF}}$) as control pulses propagate through the harness.
* Noise and Signal Integrity: Cascaded thermal noise ppwer spectral density propagation, evaluation of Johnson-Nyquist thermal noise across temperature steps, output signal power ($P_{\text{sig}}$), and SNR optimization at the 10mK mixing chamber. The simulation incorporates an "include_qunatum" flag to evaluate quantum-limited noise floors by adding zero-point vacuum fluctuations ($\frac{1}{2}\hbar\omega$).

To evaluate large-scale hardware configurations, the framework performs automated constraint evaluations against established dilution-refrigerator stage cooling budgets (eg.: 1.5W limit at 4K and $15\,\mu\text{W}$ at 10mK) and generates multidimensional parameter-sweep maps. Three industry-standard coaxial cable material models are natively supported: Stainless Steel 304 (SS304), Beryllium Copper (BeCu), and superconducting Niobium-Titanium (NbTi). 
Ultimately, this codebase bridges classical cryogenic electronics theory with a functional system-level design tool, enabling optimization of control-line attenuation profiles, evaluation of high-density wiring limits ($N \ge 50$ lines), and enforcing strict thermal operating envelopes for scalable superconducting quantum hardware. 

## Physical Model
### Cryogenic Control-Line Architecture
The simulated control line traverses a multi-stage dilution refrigerator architecture, descending across distinct thermal anchors from room-temperature electronics down to the quantum processor:

Cryogenic Stage             Temperature (T)            Physical Role & Engineering Function
____________________________________________________________________________________________________________________________
Room-Temperature Input      300 K                      Microwave signal source (AWG/generators) and 
                                                       initial thermal noise baseline 
4K stage                    4.0 K                      Primary thermal interception anchor; 
                                                       absorbs bulk conductive loads ($1.5\text{ W}$ cooling budget) 
                                                       and bulk RF power dissipation
Intermediate stage          700 mK                     Secondary attenuation stage; 
(Still)                                                provides further thermal isolation and noise suppression
Intermediate Stage          100 mK                     High-attenuation stage for deep thermal noise stripping prior to 
(Cold Plate)                                           mixing chamber entry
Mixing Chamber              10 mK                      Final signal delivery stage ($15\,\mu\text{W}$ cooling budget) 
                                                       housing the quantum device and final output SNR evaluation
