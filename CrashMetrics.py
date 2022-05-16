# Crash Metrics Function (API)

# Input is a json string form the crash vis json that is output by the crash detector when a crash is detected.  

# Output is a json string with a set of metrics.  The key ones are:

# 2022 0210
# Estimated AIS or Abbreviated Injury Score.  This one will need a bit more work over the weekend.  
# Expected Compensation Cost.   These will eventually be estimated from our claims data.



# crashvis_dict:
#  dict_keys(['time100Hz', 'ax100Hz', 'ay100Hz', 'az100Hz', 'obdSpeed100Hz', 'time20Hz', 'obdSpeed20Hz', 
# 'gpsSpeed20Hz', 'gpsLon20Hz', 'gpsLat20Hz', 'indexImpact100Hz', 'timeImpact100Hz', 'indexImpact20Hz', 
# 'timeImpact20Hz', 'indexZeroSpeed20Hz', 'timeZeroSpeed20Hz', 'indexZeroSpeed100Hz', 'timeZeroSpeed100Hz', 
# 'impactGForceForwardBack', 'impactGForceLeftRight', 'filename', 'pdf_accel_flnm', 'pdf_gps_flnm'])

import json
import numpy as np

# With DEBUG False, matplotlib is not needed.  Otherwise it should also be imported.  

def CrashMetrics(crashvis_json_string):
    
    # Additions VIN needs to be transferred from impact json into crash vis json.   
    
    crashvis_dict = json.loads(crashvis_json_string);
    
    DEBUG = False;
    
    crashmetrics_dict = {};
    crashmetrics_dict['impactGForceForwardBack'] = crashvis_dict['impactGForceForwardBack']
    crashmetrics_dict['impactGForceLeftRight'] = crashvis_dict['impactGForceLeftRight']
    
    
    crashmetrics_dict['impactGForceTotal'] = np.sqrt(np.square(crashvis_dict['impactGForceForwardBack']) + \
                                                    np.square(crashvis_dict['impactGForceLeftRight']))
    
    # Estimate the duration of the crash. 
    
    v = crashvis_dict['obdSpeed100Hz'];
    ax = crashvis_dict['ax100Hz'];
    ay = crashvis_dict['ay100Hz'];
    az = crashvis_dict['az100Hz'];
    axyz = np.sqrt(np.square(ax)+np.square(ay)+np.square(az));
    # Portion over 1g.  
    # Start at the impact index and walk down until 15% of the peak value over 1g has been reached.  
    i0 = crashvis_dict['indexImpact100Hz'];   
    N = len(axyz);
    mx = axyz[i0];
    g = 9.8;
    
    i = i0;
    i1 = i0;
    i2 = i0;
    fac = 0.1;
    for i in np.arange(i0,0,-1):
        if (axyz[i] < (fac * mx + (1-fac) * g)):
            i1 = i+1;
            break;
    for i in np.arange(i0,N,+1):
        if (axyz[i] < (fac * mx + (1-fac) * g)):
            i2 = i-1;
            break;
    # Add 20ms to each side.
    i1 = i1 - 2;
    i2 = i2 + 2;
    
    Ts = 1.0/100.0; # 100Hz signal
    ImpactDuration = (i2-i1+1)*Ts; 
    
       
    crashmetrics_dict['ImpactDuration'] = ImpactDuration;
        
    # Estimate the surrogate speed change.
    DeltaV_fromAccelX = 0.0;
    DeltaV_fromAccelY = 0.0;
    DeltaV_fromAccelZ = 0.0;
#     for i in np.arange(i1,i2+1):
#         DeltaV_fromAccelX += ax[i] * Ts;
#         DeltaV_fromAccelY += ay[i] * Ts;
#         DeltaV_fromAccelZ += az[i] * Ts;
    for i in np.arange(i1,i2+1):
        DeltaV_fromAccelX += np.abs(ax[i]) * Ts;
        DeltaV_fromAccelY += np.abs(ay[i]) * Ts;
        DeltaV_fromAccelZ += np.abs(az[i]) * Ts;
    
    DeltaV_fromAccel = np.sqrt(np.square(DeltaV_fromAccelX) + np.square(DeltaV_fromAccelY) + \
                               np.square(DeltaV_fromAccelZ-g))
    
    
    DeltaV_fromAccelXYZ = 0.0;
    for i in np.arange(i1,i2+1):
        DeltaV_fromAccelXYZ += axyz[i] * Ts;
    
    # The OBD response is slower and therefore the speeds chosen are 250ms before and after impact.  
    maxV = np.max(v[i1-3:i2+101]); # 30ms before to 1000ms after.  
    minV = np.min(v[i1-3:i2+101]);
    DeltaV_fromOBD = np.abs(maxV - minV); 
    
    # Establish a DeltaV that is the maximum of DeltaV_fromOBD and the DeltaV_fromAccel 
    
#     DeltaV = np.max([DeltaV_fromOBD,DeltaV_fromAccel]); # Seems to cause very large AIS
    DeltaV = DeltaV_fromAccel
    mps2kph = 3.6;
    DeltaVkph = mps2kph * DeltaV;
    crashmetrics_dict['DeltaV_KPH'] = DeltaVkph;
    
    # Abbreviated Injury Severity
    # This initial estimate comes from Fig8 of Neal-Sturgess, 2002 which I then fit to a 3rd order polynomial.
    # This is an estimate of the front impact belted drivers all injuries.
    x = DeltaVkph;
    EstimatedAIS = np.round(0.001*(0.0218*np.power(x,3) + 0.1514*np.power(x,2) - 3.7705*np.power(x,1)),1);
    crashmetrics_dict['EstimatedAIS'] = EstimatedAIS;
    
    # Maximum Abbreviated Injury Severity
#     EstimatedMAIS = 0.0;
#     crashmetrics_dict['EstimatedMAIS'] = EstimatedMAIS;
    
    # Expected compensation cost frin table 8 of Harmon, et al., 2018.
    
    x_mais = [0,1,2,3,4,5,6];
    y_cost = [2843 ,17810 ,55741 ,181927 ,394608 ,1001089 ,1398916 ];
    
    ExpectedCompensationCost = np.interp(EstimatedAIS, x_mais, y_cost)  # In dollars.  
    crashmetrics_dict['ExpectedCompensationCost'] = ExpectedCompensationCost;
    
    if (DEBUG):
        
        print('mx',mx)
        print('impactGForceTotal',crashmetrics_dict['impactGForceTotal'])
        
        print('ImpactDuration',ImpactDuration)
        
        print('DeltaV_fromAccel',DeltaV_fromAccel)
        print('DeltaV_fromAccelXYZ',DeltaV_fromAccelXYZ)
        
        print('DeltaV_fromOBD',DeltaV_fromOBD)
        print('DeltaV',DeltaV)
        print('DeltaVkph',DeltaVkph)
        print('EstimatedAIS',EstimatedAIS)
        print('ExpectedCompensationCost',ExpectedCompensationCost)

        
        # Plot the signals
        fig = plt.figure(1,figsize=(18, 12))
        plt.clf();
        axi = fig.add_subplot(111)
        axi.grid()
        plt.plot(ax,'r',linewidth=2,label='AX');
        plt.plot(ay,'b',linewidth=2,label='AY');
        plt.plot(az,'g',linewidth=2,label='AY');
        plt.plot(v,'c',linewidth=2,label='V');
        plt.plot(axyz,'k',linewidth=2,label='AXY');
        plt.plot(i0,axyz[i0],'rd');
        plt.plot(np.arange(i1,i2+1),axyz[i1:i2+1],'m',linewidth=5);
        
        
        print(crashmetrics_dict.keys())
        
    crashmetrics_json_string = json.dumps(crashmetrics_dict)
    return(crashmetrics_json_string)
