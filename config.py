"""
Global physical constant and cryogenic stage configurations
"""
#Physical constants (SI units)
k_B= 1.380649e-23 #boltzmann constant (J/K)
hbar= 1.054571817e-34 #reduced planck constant (J.s)
H= 6.62607015e-34 #planck constant (J.s)

#Default temperature stages in K
Stage_Temps= {"4K": 4.0, "700mK": 0.700, "100mK": 0.100, "10mK": 0.010}

#cable & physical defaults
cable_deflen= 0.5 #total coaxial length across stages
def_freq= 5.0e9 #target microwave signal frequency (5 GHz)