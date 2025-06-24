import psutil
import time

def get_high_precision_cpu_usage(interval=0.05):
    cpu_usages = psutil.cpu_percent(interval=interval, percpu=True)
    formatted_usages = {f"CPU {i}" : f"{cpu_usage:.1f}%" for i, cpu_usage in enumerate(cpu_usages)}
    return formatted_usages

def main(N=-1):
    interval = 1 #second    
    start = time.time()
    if N <= 0:
        counter = 0        
        while True:
            while time.time() - start < interval*counter:
                time.sleep(1e-2)
            print(get_high_precision_cpu_usage(interval))
            counter = counter + 1
    else:
        padding = 120 # 1 extra Minute
        #padding = interval
        for i in range (N//interval + 1 + padding//interval):
            while time.time() - start < interval*i:
                time.sleep(1e-2)
            print(get_high_precision_cpu_usage(interval))

if __name__=="__main__":
    main()
