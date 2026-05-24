import os
import time
import psutil
import json
import subprocess
import platform

class SystemMonitor:
    def __init__(self):
        #load configuration thresholds from the json file
        self.load_config()

        #track metric
        self.cpu_breach_count=0
        self.mem_breach_count=0

    def set_power_mode(self, mode="high"):
        """Directly modifies the Windows Power Plan using command line."""
        if platform.system() != "Windows":
            return False, "This tweak requires a Windows environment."
        
        try:
            # Official Windows OS Power Plan GUIDs
            if mode == "high":
                guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"  # High Performance
            else:
                guid = "381b4222-f694-41f0-9685-ff5bb260df2e"  # Balanced
                
            # Issue the hidden command directly to the Windows power engine
            subprocess.run(["powercfg", "/setactive", guid], check=True, capture_output=True)
            return True, f"Power plan set to {mode.upper()}"
        except Exception as e:
            return False, str(e)

    def load_config(self):
        try:
            with open("config.json","r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            #fallback just in case if the file is missing
            self.config = {
                "cpu_threshold_percentage":80.0,
                "memory_threshold_pecentage":85.0,
                "disk_threshold_percentage":90.0,
                "consecutive_cycles_required":3

            }
    def get_cpu_metrics(self):
        # interval=None tells psutil to calculate utilization since last call non-blocking
        return {
            "total_usage": psutil.cpu_percent(interval=None),
            "core_count": psutil.cpu_count(logical=True),
            "per_core_usage": psutil.cpu_percent(interval=None, percpu=True)
        }

    def get_memory_metrics(self):
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "usage_percent": mem.percent
        }

    def get_disk_metrics(self):
        # Checking root path (works across Linux/Windows defaults)
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": disk.percent
        }

    def get_network_metrics(self):
        net = psutil.net_io_counters()
        return {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
        }
    def check_thresholds(self, cpu_pct, mem_pct, disk_pct):
        alerts = []
        limit = self.config["consecutive_cycles_required"]  

        #Alert if cpu is over limit. If it drops, reset.
        if cpu_pct > self.config["cpu_threshold_percent"]:
            self.cpu_breach_count +=1
            if self.cpu_breach_count >= limit:
                alerts.append(f"🚨Critical: cpu usage sustained at {cpu_pct}% for {self.cpu_breach_count } cycles!")
        else:
            self.cpu_breach_count =0
        
        #for ram
        if mem_pct > self.config["memory_threshold_percent"]:
            self.mem_breach_count+=1
            if self.mem_breach_count >= limit:
                alerts.append(f"🚨Critical: memory usage sustained at {mem_pct}% for {self.mem_breach_count } cycles!")
        else:
            self.mem_breach_count =0



        #for disk

        if disk_pct> self.config["disk_threshold_percent"]:
            alerts.append(f"🚨Critical: low disk space ! disk utilization is at {disk_pct}%")

        return alerts



    def run_snapshot_loop(self, delay=2):
        print("🚀 System Monitor Engine Started. Press Ctrl+C to stop...\n")
        # First call initializes the CPU percent baseline
        psutil.cpu_percent(interval=None)
        time.sleep(1) 

        try:
            while True:
                # Clear terminal screen dynamically for a cleaner output
                os.system('cls' if os.name == 'nt' else 'clear')
                
                cpu = self.get_cpu_metrics()
                mem = self.get_memory_metrics()
                disk = self.get_disk_metrics()
                net = self.get_network_metrics()

                active_alerts = self.check_thresholds(cpu['total_usage'], mem['usage_percent'], disk['usage_percent'])

                print("=== [ CPU METRICS ] ===")
                print(f"Total Usage: {cpu['total_usage']}% | Cores: {cpu['core_count']}")
                print(f"Per-Core Load: {cpu['per_core_usage']}")
                
                print("\n=== [ MEMORY METRICS ] ===")
                print(f"Usage: {mem['usage_percent']}% | Used: {mem['used_gb']}GB / {mem['total_gb']}GB")
                
                print("\n=== [ DISK METRICS ] ===")
                print(f"Usage: {disk['usage_percent']}% | Free: {disk['free_gb']}GB / {disk['total_gb']}GB")
                
                print("\n=== [ NETWORK METRICS ] ===")
                print(f"Total Sent: {net['bytes_sent_mb']} MB | Total Received: {net['bytes_recv_mb']} MB")
                
                if active_alerts:
                    print("\n 🚨 Active Incidents:")
                    for alert in active_alerts:
                        print(alert)
                else:
                    print("\n 💚 System Status : Healthy")

                time.sleep(delay)
        except KeyboardInterrupt:
            print("\nShutting down monitor engine gracefully.")

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run_snapshot_loop(delay=2)
