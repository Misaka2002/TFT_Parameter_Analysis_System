#################################################################################################################

# Package import 

#################################################################################################################

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from glob import glob
import matplotlib as mpl
from scipy.constants import constants

#import sys
#savePlot = True

#################################################################################################################

# Plot design, figure size, font size, font style, etc.

#################################################################################################################

cm = 1/2.54
#plt.figure(figsize= (7.5*cm,5*cm),dpi=300)
plt.figure(dpi=300)
settings = {"xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "font.size": 12,
            "legend.fontsize": 9,
            "font.family":['Arial']
            }
mpl.rcParams.update(settings)

#################################################################################################################

# Definition linear fit function

#################################################################################################################

def linear(x, a, b):
            '''Allgemeine Gerade fuer Tangente'''
            return a * x + b
  
#################################################################################################################

# Calculation Gate-oxide capacity

#################################################################################################################
    
e0 = constants.epsilon_0
er = 4
d = 130 * 10 ** (-9)
W = 10 * 10 ** (-6)
L = 10 * 10 ** (-6)
C = e0 * er / d
    
files = sorted(glob("./YO1_*.txt"))
files2 =  sorted(glob("./YO5_*.txt"))
files3 =  sorted(glob("./YO8_*.txt"))
files4 =  sorted(glob("./YO10_*.txt"))
files5 =  sorted(glob("./YO12_*.txt"))

thickness = [32.9,61.7,92.2,122.6,151.8]
UgateBG = []
IdrainBG = []

UgateBG2 = []
IdrainBG2 = []

UgateBG3 = []
IdrainBG3 = []

UgateBG4 = []
IdrainBG4 = []

UgateBG5 = []
IdrainBG5 = []

mobility = []
mobility2 = []
mobility3 = []
mobility4 = []
mobility5 = []
mobilityend = []

#################################################################################################################

# Data import, evaluation and plotting

#################################################################################################################

for f in files:
    #print(f)
    UgateYS1,IdrainYS111 = np.genfromtxt(f,delimiter= '\t', unpack = True)
    UgateBG.append(UgateYS1)
    IdrainBG.append(IdrainYS111)
     # Tangente
    

for i in range(len(UgateBG)):
   # plt.plot(UgateBG[i],np.abs(IdrainBG[i]),'b')    
    difx = np.diff(UgateBG[i])
    dify = np.diff(np.sqrt(np.abs(IdrainBG[i])))
    steigung = np.divide(dify, difx)
    maxV = np.max(steigung)
    maxvalue = np.argmax(steigung)
    a = [UgateBG[i][maxvalue], UgateBG[i][maxvalue + 1]]
    b = [np.sqrt(np.abs(IdrainBG[i][maxvalue])), np.sqrt(np.abs(IdrainBG[i][maxvalue + 1]))]

    popt, _ = curve_fit(linear, a, b)

        # Calc U_Th
    U_TH = -popt[1] / popt[0]
        # Calc Mobility
    Mobility = 2 * IdrainBG[i][maxvalue] / (UgateBG[i][maxvalue] - U_TH) ** 2 * L / (C * W) * 10000

        # Arrays fuer spaeteren Plot
    mobility.append(Mobility)
plt.plot(UgateBG[0],np.abs(IdrainBG[0]),'b',label = '$h = 32.9 \,\mathrm{nm}$')    
#print(mobility)
#print(np.mean(mobility))
mobilityend.append(np.mean(mobility))
#sys.exit()
#print(files2)
 
for f in files2:
    #print(f)
    UgateYS1,IdrainYS111 = np.genfromtxt(f,delimiter= '\t', unpack = True)
    UgateBG2.append(UgateYS1)
    IdrainBG2.append(IdrainYS111)
    

for i in range(len(UgateBG2)):
    #plt.plot(UgateBG2[0],np.abs(IdrainBG2[0]),'r')    
    difx = np.diff(UgateBG2[i])
    dify = np.diff(np.sqrt(np.abs(IdrainBG2[i])))
    steigung = np.divide(dify, difx)
    maxV = np.max(steigung)
    maxvalue = np.argmax(steigung)
    a = [UgateBG2[i][maxvalue], UgateBG2[i][maxvalue + 1]]
    b = [np.sqrt(np.abs(IdrainBG2[i][maxvalue])), np.sqrt(np.abs(IdrainBG2[i][maxvalue + 1]))]

    popt, _ = curve_fit(linear, a, b)

        # Calc U_Th
    U_TH = -popt[1] / popt[0]
        # Calc Mobility
    Mobility2 = 2 * IdrainBG2[i][maxvalue] / (UgateBG2[i][maxvalue] - U_TH) ** 2 * L / (C * W) * 10000

        # Arrays fuer spaeteren Plot
    mobility2.append(Mobility2)
#plt.plot(UgateBG[0],np.abs(IdrainBG[0]),'b',label = '$h = 32.9 \,\mathrm{nm}$')    
#print(mobility2)
#print(np.mean(mobility2))
mobilityend.append(np.mean(mobility2))
#sys.exit()
plt.plot(UgateBG2[0],np.abs(IdrainBG2[0]),'r',label = '$h = 61.7 \,\mathrm{nm}$')    

for f in files3:
    #print(f)
    UgateYS1,IdrainYS111 = np.genfromtxt(f,delimiter= '\t', unpack = True)
    UgateBG3.append(UgateYS1)
    IdrainBG3.append(IdrainYS111)
    

for i in range(len(UgateBG3)):
    #plt.plot(UgateBG3[2],np.abs(IdrainBG3[2]),'g')    
    difx = np.diff(UgateBG3[i])
    dify = np.diff(np.sqrt(np.abs(IdrainBG3[i])))
    steigung = np.divide(dify, difx)
    maxV = np.max(steigung)
    maxvalue = np.argmax(steigung)
    a = [UgateBG3[i][maxvalue], UgateBG3[i][maxvalue + 1]]
    b = [np.sqrt(np.abs(IdrainBG3[i][maxvalue])), np.sqrt(np.abs(IdrainBG3[i][maxvalue + 1]))]

    popt, _ = curve_fit(linear, a, b)

        # Calc U_Th
    U_TH = -popt[1] / popt[0]
        # Calc Mobility
    Mobility3 = 2 * IdrainBG3[i][maxvalue] / (UgateBG3[i][maxvalue] - U_TH) ** 2 * L / (C * W) * 10000

        # Arrays fuer spaeteren Plot
    mobility3.append(Mobility3)
    
#print(mobility3)
#print(np.mean(mobility3))
mobilityend.append(np.mean(mobility3))
plt.plot(UgateBG3[2],np.abs(IdrainBG3[2]),'g',label = '$h = 92.2 \,\mathrm{nm}$') 

for f in files4:
    #print(f)
    UgateYS1,IdrainYS111 = np.genfromtxt(f,delimiter= '\t', unpack = True)
    UgateBG4.append(UgateYS1)
    IdrainBG4.append(IdrainYS111)
   


for i in range(len(UgateBG4)):
    #plt.plot(UgateBG4[0],np.abs(IdrainBG4[0]),'black')  
    
    difx = np.diff(UgateBG4[i])
    dify = np.diff(np.sqrt(np.abs(IdrainBG4[i])))
    steigung = np.divide(dify, difx)
    maxV = np.max(steigung)
    maxvalue = np.argmax(steigung)
    a = [UgateBG4[i][maxvalue], UgateBG4[i][maxvalue + 1]]
    b = [np.sqrt(np.abs(IdrainBG4[i][maxvalue])), np.sqrt(np.abs(IdrainBG4[i][maxvalue + 1]))]

    popt, _ = curve_fit(linear, a, b)

        # Calc U_Th
    U_TH = -popt[1] / popt[0]
        # Calc Mobility
    Mobility4 = 2 * IdrainBG4[i][maxvalue] / (UgateBG4[i][maxvalue] - U_TH) ** 2 * L / (C * W) * 10000

        # Arrays fuer spaeteren Plot
    mobility4.append(Mobility4)
#plt.plot(UgateBG[0],np.abs(IdrainBG[0]),'b',label = '$h = 32.9 \,\mathrm{nm}$')    
#print(mobility4)
#print(np.mean(mobility4))
mobilityend.append(np.mean(mobility4))
plt.plot(UgateBG4[0],np.abs(IdrainBG4[0]),'black',label = '$h = 122.6 \,\mathrm{nm}$') 

for f in files5:
    #print(f)
    UgateYS1,IdrainYS111 = np.genfromtxt(f,delimiter= '\t', unpack = True)
    UgateBG5.append(UgateYS1)
    IdrainBG5.append(IdrainYS111)
    
    

for i in range(len(UgateBG4)):
   # plt.plot(UgateBG5[1],np.abs(IdrainBG5[1]),'y')    
    difx = np.diff(UgateBG5[i])
    dify = np.diff(np.sqrt(np.abs(IdrainBG5[i])))
    steigung = np.divide(dify, difx)
    maxV = np.max(steigung)
    maxvalue = np.argmax(steigung)
    a = [UgateBG5[i][maxvalue], UgateBG5[i][maxvalue + 1]]
    b = [np.sqrt(np.abs(IdrainBG5[i][maxvalue])), np.sqrt(np.abs(IdrainBG5[i][maxvalue + 1]))]

    popt, _ = curve_fit(linear, a, b)

        # Calc U_Th
    U_TH = -popt[1] / popt[0]
        # Calc Mobility
    Mobility5 = 2 * IdrainBG5[i][maxvalue] / (UgateBG5[i][maxvalue] - U_TH) ** 2 * L / (C * W) * 10000

        # Arrays fuer spaeteren Plot
    mobility5.append(Mobility5)

#print(mobility5)
#print(np.mean(mobility5))
mobilityend.append(np.mean(mobility5))
plt.plot(UgateBG5[1],np.abs(IdrainBG5[1]),'y',label = '$h = 151.8 \,\mathrm{nm}$') 
plt.legend()  
plt.xlim(-20.1,20.1)  

plt.xlabel('Gate voltage $U_\mathrm{G}$ (V)')
plt.ylabel('Drain current $I_\mathrm{D}$ (A)')
plt.yscale("logit")
#plt.ylim(10**(-20),10**(-4))
plt.tight_layout()
plt.savefig('test.png',dpi=300)

#show('Kennlinielog')
#sys.exit()

# plt.plot(thickness,mobilityend,'x')
# plt.xlabel('Thickness $h$ (nm)')
# plt.ylabel('mobility $\mu$ (cm^2/Vs)')
#plt.savefig('mobility.png')