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

|    Cryogenic Stage      |    Temperature (T)    |   Physical Role & Engineering Function    |
|-------------------------|-----------------------|-------------------------------------------|
| Room-Temperature Input  |    300 K              | Microwave signal source (AWG/generators)  | 
|                         |                       | and initial thermal noise baseline.       |
|-------------------------|-----------------------|-------------------------------------------|
| 4K stage                |    4.0 K              | Primary thermal interception anchor;      |
|                         |                       | absorbs bulk conductive loads             |
|                         |                       | ($1.5\text{ W}$ cooling budget) and bulk  |
|                         |                       | RF power dissipation.                     |
|-------------------------|-----------------------|-------------------------------------------|
| Intermediate stage      |    700 mK             | Secondary attenuation stage; provides     |
| (Still)                 |                       | further thermal isolation and noise       |
|                         |                       | suppression.                              |
|-------------------------|-----------------------|-------------------------------------------|
| Intermediate Stage      |    100 mK             | High-attenuation stage for deep thermal   |
| (Cold Plate)            |                       | noise stripping prior to mixing chamber   |
|                         |                       | entry                                     |
|-------------------------|-----------------------|-------------------------------------------|
| Mixing Chamber          |    10 mK              | Final signal delivery stage               |
|                         |                       | ($15\,\mu\text{W}$ cooling budget) housing|
|                         |                       | the quantum device and final output       |
|                         |                       | SNR evaluation                            |
-----------------------------------------------------------------------------------------------

Each stage is parameterized by its absolute temperature, assigned discrete attenuation, and coaxial cable segment dimensions. As input microwave signals propagate downward, power is attenuated sequentially through the cascaded stages. 
To evaluate system performance, the simulation engine decouples and tracks two concurrent physical pathways:
* Thermal Path: Calculates phonon-mediated conductive heat transfer ($Q_{\text{cond}}$) and RF microwave power dissipation ($Q_{\text{RF}}$) deposited at each stage anchor.
* Microwave Path: Propagates signal power ($P_{\text{sig}}$) and cascaded noise power spectral density ($S_{\text{noise}}$) through the attenuator chain.
This architectural separation enables simultaneous evaluation of hardware thermal budget constraints and output signal integrity within a unified computational pipeline.

### Microwave Attenuation
Attenuation specified in decibels is converted into a linnear power-transmission coefficient:
$$\eta = 10^{-\frac{\vert{}A_{\mathrm{dB}}\vert{}}{10}}$$
where $A_{\mathrm{dB}}$: attenuation in decibels
      $\eta$: resulting transmitted power fraction
For a cascaded sequence of $N$ attenuation stages, the total output signal power at the termination of the transmission line is evaluated as:
$$P_{\mathrm{out}} = P_{\mathrm{in}} \prod_{i=1}^{N} \eta_i$$

To interface between standard radio-frequency (RF) power metrics and absolute thermal dissipation calculations, input power specified in decibels-relative-to-one-milliwatt ($\text{dBm}$) is converted into absolute watts via:                                                         $$P_{\mathrm{in}}[\mathrm{W}] = 10^{\frac{P_{\mathrm{in}}[\mathrm{dBm}]}{10}} \times 10^{-3}$$

To protect sensitive millikelvin stages from excessive thermal saturation—such as the strict $15\,\mu\text{W}$ cooling threshold at the $10\text{ mK}$ mixing chamber—the framework distributes total system attenuation across the four primary cryogenic anchor stages according to a non-uniform 40:20:20:20 allocation profile. By dumping $40\%$ of the total attenuation at the robust $4\text{ K}$ thermal anchor (possessiong a large $1.5\text{ W}$ cooling capacity), the system effectively strips high-temperature thermal noise while preventing runaway heating at lower stages.

### Conductive Heat Transfer
Conductive heat transfer through a coaxial cable segment spanning between boundary temperatures $T_{\mathrm{hot}}$ and $T_{\mathrm{cold}}$ is modeled via Fourier's law of thermal conduction:
$$Q_{\mathrm{cond}} = \frac{A}{L} \int_{T_{\mathrm{cold}}}^{T_{\mathrm{hot}}} k(T) \, dT$$
where, A: effective conductor cross-sectional area
       L: physical cable-segment length
       k(T): temperature-dependent thermal conductivity profile.
       $T_{\mathrm{hot}}$: absolute temperature at upper segment boundary
       $T_{\mathrm{cold}}$: absolute temperature at lower segment boundary

For material-based calculations, the thermal conductivity integral is evaluated numerically using high-precision trapezoidal integration across a refined discretization grid of 200 temperature points.
To support simplified preliminary estimations or fallback conditions when a temperature-dependent material fit is omitted, an alternative constant-average-conductivity model is also implemented:
$$Q_{\mathrm{cond}} = k_{\mathrm{avg}} \frac{A}{L} (T_{\mathrm{hot}} - T_{\mathrm{cold}})$$

### RF Dissipation
Microwave power dissipated within an attenuator stage is converted directly into thermal heat load deposited at that specific thermal anchor:
$$Q_{\mathrm{RF}} = P_{\mathrm{in}} (1 - \eta) D$$
where D represents the control signal duty cycle, constrained within the closed interval $0 \le D \le 1$.
The total thermal load $Q_{\mathrm{total}}$ imposed on each individual cryogenic stage is evaluated as the linear superposition of phono-mediated conduction and active RF dissipation:
$$Q_{\mathrm{total}} = Q_{\mathrm{cond}} + Q_{\mathrm{RF}}$$

The simulation framework computes these thermal components independently for every stage and outputs a granular stage-wise breakdown. This isolation allows researchers to directly analyse and inspect the relative contributions of conductive heat transport versus microwave signal dissipation across the dilution refrigerator stack.

### Cryogenic Thermal Load Model
The commplete cryogenic thermal load model is implemented within src/thermal.py, providing a modular computational structure for stage-wise thermodynamics. The module incorporates:
* Temperature dependent thermal conductivity profiles k(T) for multiple coaxial cable material models.
* High-precision numerical integration of conductive heat transfer ($Q_{\text{cond}}$) via trapezoidal integration.
* An alternative constant-average-conductivity approximation ($k_{\text{avg}}$) for preliminary or fallback estimates.
* Active RF power dissipation calculations ($Q_{\text{RF}}$) governed by incident power, discrete stage attenuation, and signal duty cycles.
* Granular per-stage thermal evaluations that calculate conductive, RF, and total heat loads independently, allowing researchers to inspect the relative contributions of transport versus dissipation across the entire harness.

### Material Dependent Conductivity
Three approximate conductivity models are implemented as piecewise functions of temperature to capture distinct material behaviours across cryogenic thermal regimes:
* Stainless Steel 304: The model uses separate temperature-dependent expressions below 1K, between 1K and 10K, and above 10K
* Beryllium Copper (BeCu): The model uses separate expressions below 4K, between 4K and 20K, and above 20K.
* Niobium-Titanium (NbTi): The model distinguishes temperatures below and above the nominal superconducting critical temperature, $$T_c = 9.2\text{ K}$$

Below this critical temperature, a low-temperature power-law fit is applied. Above $T_c$, a distinct power law approximates the normal-state thermal conductivity region.
Note: These are simplified, piecewise conductivity fits utilized to explore material-dependent thermal behavior within the simulation framework. They are not presented or validated as experimental material-property datasets.

## Thermal Noise Spectral Density
The model calculates the thermal noise power spectral density using the Planck-form expression:
$$S_{\mathrm{th}}(f,T) = \frac{hf}{\exp(hf/k_BT)-1}$$
where, $h$: Planck's constant
       $f$: microwave frequency
       $k_B$: Boltzmann's constant
       T: absolute stage temperature
The simulation implementation optionally include the quantum zero-point contribution:
$$S_{\mathrm{model}}(f,T) = S_{\mathrm{th}}(f,T) + \frac{hf}{2}$$
The zero-point contribution is disabled by default and can be enabled during custom simulations and parameter sweeps.

### Cascaded Noise Propagation
Each attenuator is modeled as a thermal element operating at its corresponding stage temperature. The noise power spectral density propagates according to:
$$S_{\mathrm{out}} = \eta S_{\mathrm{in}} + (1 - \eta) S_{\mathrm{th}}(f, T_{\mathrm{stage}})$$
This relation combines the transmitted input noise power spectral density with the thermal noise contribution associated with the attenuator's local thermal environment.
The calculation begins at room temperature (300K) and cascades sequentially through the four cryogenic stages, producing the final accumulated output noise spectral density at the 10mK mixing chamber.

For a specified measurement or control bandwidth B, the integrated output noise power is evaluated as: 
$$P_{\mathrm{noise}} = S_{\mathrm{out}} B$$

### Signal-to-Noise Ratio and Qubit Thermal Metrics
The output SNR is evaluated at the 10mK mixing chamber using the final transmitted signal power and the integrated noise power:
$$\mathrm{SNR}_{\mathrm{linear}} = \frac{P_{\mathrm{signal}}}{P_{\mathrm{noise}}}$$
$$\mathrm{SNR}_{\mathrm{dB}} = 10 \log_{10(\mathrm{SNR}_{\mathrm{linear}})$$

To connect thermal noise performance directly with quantum hardware considerations, the model estimates the thermal photon occupation number $n_{\mathrm{th}}$ at the mixing-chamber temperature:
$$n_{\mathrm{th}} = \frac{1}{\exp(hf/k_B T) - 1}$$
Using this thermal photon occupancy, the simulation computes the corresponding two-level thermal excited-state population $P_1$ for a qubit coupled to the line:
$$P_1 = \frac{n_{\mathrm{th}}}{2n_{\mathrm{th}} + 1}$$

These metrics provide critical quantitative indicators of the residual thermal environment and its direct impact on superconducting-qubit decoherence and operational fidelity.
