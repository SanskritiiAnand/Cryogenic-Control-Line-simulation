"""
Temperature profile generation along the coaxial line path.
Supports continuous linear profile and stage wise discrete steps
"""
from typing import Dict, Union
import numpy as np
from config import Stage_Temps

def linear_temp_profile(x: Union[float, np.ndarray], length: float=0.5, t_start: float= Stage_Temps["4K"], t_end: float= Stage_Temps["10mk"]) -> Union[float, np.ndarray]:
    """
    Calculates continuous linear temperature T(x) along coaxial cable length x.
    x=0: 4K stage; x= length: 10mK stage
    """
    return t_start - (t_start - t_end) * (x / length)

def discrete_stage_profile(stage_name: str, stage_dict: Dict[str, float]= Stage_Temps) -> float:
    """
    Returns the discrete temperature for a specific cryogenic stage
    """
    if stage_name not in stage_dict:
        raise ValueError(f"Stage '{stage_name}' unknown. Valid stages: {list(stage_dict.keys())}")

    return stage_dict[stage_name]