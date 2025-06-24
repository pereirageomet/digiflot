try:
    from libs import trackCPUusage
    from libs import trackRAMusage
    from libs import trackTraffic
    from libs import trackTemperature
    from libs import trackMAC
except:
    from . import trackCPUusage
    from . import trackRAMusage
    from . import trackTraffic
    from . import trackTemperature
    from . import trackMAC
 
def provideHardwareState():
    dct = {}
    dct.update(trackCPUusage.get_high_precision_cpu_usage())
    dct.update(trackRAMusage.monitor_ram_and_swap_usage())
    dct.update(trackTraffic.getRxAndTxByteRate())
    dct.update(trackTemperature.getTemperature())
    return dct

def provideHardwareConfig():
    dct = trackMAC.getMACdict()
    return dct

if __name__ == "__main__": 
    import time
    ts = time.time()
    a = provideHardwareState()
    b = provideHardwareConfig()
    print("Delay: ", time.time() - ts)

    ts = time.time()
    dct = {}
    dct.update(trackCPUusage.get_high_precision_cpu_usage())
    print("Delay CPU: ", time.time() - ts)
    dct.update(trackRAMusage.monitor_ram_and_swap_usage())
    print("Delay +RAM: ", time.time() - ts)
    dct.update(trackTraffic.getRxAndTxByteRate())
    print("Delay +Traffic: ", time.time() - ts)
    dct.update(trackTemperature.getTemperature())
    print("Delay +Temperature: ", time.time() - ts)
    dct = trackMAC.getMACdict()
    print("Delay +MAC: ", time.time() - ts)
