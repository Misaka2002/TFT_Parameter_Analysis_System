"""
Imports from the .dat format of Roman Krahne's lab - Dorwal Marchelli.
"""

import os, json
import pandas as pd
from pathlib import Path
import datetime as dt

path_to_data = os.getenv("PATH_TO_TRANSISTOR_SWEEPS", r"path/to/2021_transistor_sweeps")

'''
The following specs could all be derived from the raw files. 
The raw files contain some additional details, like the time step between sweeps, etc
'''
transistors = {
    'ntype_W100L5_lights_on': {
        'params': {
            'polarity': 'n',
            'w': 100e-6,
            'l': 5e-6,
        },
        'sweeps_vgs': [
            (0.1, -10.000, 30.000, 401, "ntypeW100L5_VDS0p1"),
            (1,   -40.000, 30.000, 401, "ntypeW100L5_VDS1_second"),
            (30,  -30.000, 30.000, 401, "ntypeW100L5_VDS30_second"),
            ],
        'sweeps_vds': [
            (-10, 0.000, 30.000, 301, "ntypeW100L5_VGS-10"),
            (-5,  0.000, 30.000, 301, "ntypeW100L5_VGS-5"),
            (0,   0.000, 30.000, 301, "ntypeW100L5_VGS0"),
            (5,   0.000, 30.000, 301, "ntypeW100L5_VGS5"),
            (10,  0.000, 30.000, 301, "ntypeW100L5_VGS10"),
            (15,  0.000, 30.000, 301, "ntypeW100L5_VGS15"),
            (20,  0.000, 30.000, 301, "ntypeW100L5_VGS20"),
            (25,  0.000, 30.000, 301, "ntypeW100L5_VGS25"),
            (30,  0.000, 30.000, 301, "ntypeW100L5_VGS30"),
            ]
    },
    'ptype_W100L5_lights_on': {
        'params': {
            'polarity': 'p',
            'w': 100e-6,
            'l': 5e-6,
        },
        'sweeps_vgs': [
            (-0.1, -30.000, 30.000, 601, "ptypeW100L5_VDS-0.1"),
            (0.1,  -30.000, 30.000, 601, "ptypeW100L5_VDS0.1"),
            (-5,   -30.000, 30.000, 601, "ptypeW100L5_VDS-5"),
            (5,    -30.000, 30.000, 601, "ptypeW100L5_VDS5"),
            (-30,  -30.000, 30.000, 601, "ptypeW100L5_VDS-30"),
            ],
        'sweeps_vds': [
            (-30, 0.000, 30.000, 301, "ptypeW100L5_VGS-30"),
            (-25, 0.000, 30.000, 301, "ptypeW100L5_VGS-25"),
            (-20, 0.000, 30.000, 301, "ptypeW100L5_VGS-20"),
            (-15, 0.000, 30.000, 301, "ptypeW100L5_VGS-15"),
            (-10, 0.000, 30.000, 301, "ptypeW100L5_VGS-10"),
            (-5,  0.000, 30.000, 301, "ptypeW100L5_VGS-5"),
            (0,   0.000, 30.000, 301, "ptypeW100L5_VGS0"),
            (5,   0.000, 30.000, 301, "ptypeW100L5_VGS5"),
            (10,  0.000, 30.000, 301, "ptypeW100L5_VGS10"),
            (15,  0.000, 30.000, 301, "ptypeW100L5_VGS15"),
            (20,  0.000, 30.000, 301, "ptypeW100L5_VGS20"),
            (25,  0.000, 30.000, 301, "ptypeW100L5_VGS25"),
            (30,  0.000, 30.000, 301, "ptypeW100L5_VGS30"),
            ]
    },
    'ptype_W100L5_lights_off': {
        'params': {
            'polarity': 'p',
            'w': 100e-6,
            'l': 5e-6,
        },
        'sweeps_vgs': [
            (-0.1, -30.000, 30.000, 601, "ptypeW100L5_VDS-0.1"),
            (0.1,  -30.000, 30.000, 601, "ptypeW100L5_VDS0.1"),
            (-5,   -30.000, 30.000, 601, "ptypeW100L5_VDS-5"),
            (5,    -30.000, 30.000, 601, "ptypeW100L5_VDS5"),
            (-30,  -30.000, 30.000, 601, "ptypeW100L5_VDS-30"),
            ],
        'sweeps_vds': [
            (-30, 0.000, 30.000, 301, "ptypeW100L5_VGS-30"),
            (-25, 0.000, 30.000, 301, "ptypeW100L5_VGS-25"),
            (-20, 0.000, 30.000, 301, "ptypeW100L5_VGS-20"),
            (-15, 0.000, 30.000, 301, "ptypeW100L5_VGS-15"),
            (-10, 0.000, 30.000, 301, "ptypeW100L5_VGS-10"),
            (-5,  0.000, 30.000, 301, "ptypeW100L5_VGS-5"),
            (0,   0.000, 30.000, 301, "ptypeW100L5_VGS0"),
            (5,   0.000, 30.000, 301, "ptypeW100L5_VGS5"),
            (10,  0.000, 30.000, 301, "ptypeW100L5_VGS10"),
            (15,  0.000, 30.000, 301, "ptypeW100L5_VGS15"),
            (20,  0.000, 30.000, 301, "ptypeW100L5_VGS20"),
            (25,  0.000, 30.000, 301, "ptypeW100L5_VGS25"),
            (30,  0.000, 30.000, 301, "ptypeW100L5_VGS30"),
            ]
        },
    }

def extract_timestamp_from_header(header_line):
    # Split on 'Date:' and strip
    date_str = header_line.split("Date:")[1].strip()
    # Parse the English date like: "Thu, Sep 9, 2021 1:29 PM"
    dt_obj = dt.datetime.strptime(date_str, "%a, %b %d, %Y %I:%M %p")
    # Convert to the desired format: YY_MM_DD_HH_MM_SS
    return dt_obj.strftime("%y_%m_%d_%H_%M_%S")


def import_transistors(path_to_data=path_to_data):

    with open(Path(path_to_data) / "parameters.json", "r") as f:
        proc_params = json.load(f)
        
    for transistor_name, transistor in transistors.items():
        transistor.setdefault('params', {})
        transistor['params'].update(proc_params)
        transistor['sweeps'] = []
        for vds, sweepLow, sweepHigh, sweepNum, fileName in transistor['sweeps_vgs']:
            idss = []
            with open(str(Path(path_to_data) / transistor_name / (fileName + '.dat')), 'r') as file:
                for idx, line in enumerate(file):
                    if idx == 0:
                        datetime = extract_timestamp_from_header(line)
                    if idx < 36:
                        continue
                    ids = float(line.split(' ')[1])
                    idss.append(ids)
            step = (sweepHigh - sweepLow) / (sweepNum - 1)
            sweep_up = pd.Series(pd.RangeIndex(start=0, stop=sweepNum) * step + sweepLow)
            sweep_down = sweep_up.iloc[::-1]
            vgs_col = pd.concat([sweep_up, sweep_down], ignore_index=True)
            vds_col = pd.Series([vds] * len(vgs_col)) # vds is constant for all points
            ids_col = pd.Series(idss) # ids: convert list → Series, same length as vgs
            df = pd.DataFrame({ # build the dataframe
                "vds": vds_col,
                "vgs": vgs_col,
                "ids": ids_col
            })            
            transistor['sweeps'].append({
                'data': df,
                'type': 'g',
                'datetime': datetime
                })           
                
        for vgs, sweepLow, sweepHigh, sweepNum, fileName in transistor['sweeps_vds']:
            idss = []
            with open(str(Path(path_to_data) / transistor_name  / (fileName + '.dat')), 'r') as file:
                for idx, line in enumerate(file):
                    if idx < 36:
                        continue
                    ids = float(line.split(' ')[1])
                    idss.append(ids)
                
            step = (sweepHigh - sweepLow) / (sweepNum - 1)
            sweep_up = pd.Series(pd.RangeIndex(start=0, stop=sweepNum) * step + sweepLow)
            sweep_down = sweep_up.iloc[::-1]
            vds_col = pd.concat([sweep_up, sweep_down], ignore_index=True)
            vgs_col = pd.Series([vgs] * len(vds_col)) # vds is constant for all points
            ids_col = pd.Series(idss) # ids: convert list → Series, same length as vgs
            df = pd.DataFrame({ # build the dataframe
                "vds": vds_col,
                "vgs": vgs_col,
                "ids": ids_col
            })            
            transistor['sweeps'].append({
                'data': df,
                'type': 'd',
                'datetime': datetime
                })
    
    return transistors
