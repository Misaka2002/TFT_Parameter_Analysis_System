# Transistor Sweep Dataset – File Format Specification

This dataset (DOI: 10.5281/zenodo.17701094) contains raw transistor sweep data acquired in Roman Krahne’s optoelectronics lab at Italian Institute of Technology in 2021.
Technician: Dorwal Marchelli.
Other data collectors: Simeon Bamford, Simon Mueller-Cleve.
PI: Chiara Bartolozzi.
Dataset curation: Simeon Bamford.
The transistors were OFETs from samples kindly supplied by Flexterra, with thanks to Antonio Facchetti and Xia Yu.
 
Simon-Mueller-Cleve was funded by H2020 "NeuTouch: Neuromorphic Embedded Processing for Touch" grant agreement ID 813713, DOI 10.3030.813713.

# Contents

Several transistors of both P and N-type were swept. Lighting was varied both within and between sweeps. The file headers (as well as the file names themselves) document the transistors used, according to the file format described below. 

Key process parameters are documented in parameters.json file.

Example sweep visualisations for one transistors are also included, in both png and html format - the html can be viewed in any browser and gives interactive 3D visualisation of the IDS-VGS-VDS landscape.

An example script for importing some data is included; however for the latest import scripts please see:

https://github.com/event-driven-robotics/ofet_import

To generate visualsations, consider using: 

https://github.com/event-driven-robotics/ivplot

# File format

Each sweep is stored as a plain-text `.dat` file with this structure.

## 1. File Header

**Line 1:**  
```
Scan <label>                 Date: <weekday>, <Mon> <D>, <YYYY> <H>:<M> <AM/PM>
```
Contains a free-form scan label and the acquisition timestamp.


## 3. Scan Table

Introduced by:
```
Scan Table
----------
```

Describes the programmed voltage sweep, e.g.:
```
<quantity> <start> <stop> <num_points> raster
<aux parameters ...>
```

## 4. SET Constants Table

Introduced by:
```
SET Constants Table
-------------------
```

Contains instrument constants or placeholders (may appear as `...`).

## 5. Channels

Introduced by:
```
Channels
--------
```

Typically lists:
```
Voltage_ChA
Current_ChA
```
(first column = swept voltage, second column = measured current)

## 6. Measurement Data

Introduced by:
```
Measurement Data
----------------
```

Followed by one row per acquired data point:
```
<voltage> <current>
```

Values use scientific notation (`E` format). The number of rows equals the sweep length defined in the Scan Table.


