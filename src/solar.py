"""

TODO:
    * Implement multiple inputs and outputs for LCOE.
    * Modify Tracking method selection
"""

from __future__ import division, print_function
"""
Solar database
Example:
    Example of usage goes here

Attributes:
    module_level_variabless: None for the moment

"""
import pandas as pd
import sys

#if sys.version_info >= (3, 0):
#    sys.stdout.write("Sorry, requires Python 2.x, not Python 3.x\n")
#    sys.exit(1)


def lcoe(AEP, Tracking=None, *args, **kwargs):
    """LCOE cost estimation for solar PV plants
    Args:
        AEP: Annual energy production (pd.Series or Float)
        fixed: Fixed tilt (Boolean)
        Tracking: Tracking (Boolean)
        CapEx: Capital Expenditures [$/MW]
        OpEx: Operational expenditures [$/MW-y]
        d: Discount rate (%)
        n: Years of operation
        T: Tax rate [%]
        Pvdep: Depresation present value [%]

    Return:
        LCOE value in $/MW.
    """
    AEP = AEP/1000
    if Tracking == 0:
        CapEx = 1500000
        OpEx = 10000
    elif Tracking == 1:
        CapEx = 1620000
        OpEx = 10440
    elif Tracking == 2:
        CapEx = 2400000
        OpEx = 12000
    else:
        print ('No tracking informatio given')
    d = 0.06 
    n = 25.
    T = 0.3
    Pvdep = 0.8
    FCR = ((d*(1 + d)**n) / (d*(1 + d)**n) - 1) *((1 - (T*Pvdep))/(1 - T))
    LCOE = ((CapEx * FCR) + OpEx ) / AEP
    return (LCOE)

if __name__ == "__main__":
    print (lcoe(287116.310894))
