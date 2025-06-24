import time
import psutil

def monitor_ram_and_swap_usage():    
    memory_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()
    
    total_memory = memory_info.total
    used_memory = memory_info.used
    available_memory = memory_info.available
    memory_percent = memory_info.percent
    
    total_swap = swap_info.total
    used_swap = swap_info.used
    free_swap = swap_info.free
    swap_percent = swap_info.percent
    
    return { "total memory" : total_memory, "used memory": used_memory, "available memory" : available_memory, "memory percentage": memory_percent, "total swap" : total_swap, "used swap" : used_swap, "free swap" : free_swap, "swap percentage" : swap_percent }

def main(N=-1):
    interval = 1 #seconds    
    start = time.time()
    if N <= 0:
        counter = 0        
        while True:
            while time.time() - start < interval*counter:
                time.sleep(1e-2)
            print(monitor_ram_and_swap_usage())
            counter = counter + 1
    else:
        for i in range (N//interval + 1):
            while time.time() - start < interval*i:
                time.sleep(1e-2)
            print(monitor_ram_and_swap_usage())

if __name__=="__main__":
    main()