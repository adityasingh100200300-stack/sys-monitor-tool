import customtkinter as ctk
import time
import threading

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from monitor import SystemMonitor

class MonitorDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.monitor = SystemMonitor()
        self.stop_event = threading.Event()
        # 1. Expand telemetry data to hold disk and network
        self.telemetry_data = {
            "cpu_pct": 0.0, "cpu_cycles": 0,
            "mem_pct": 0.0, "mem_used": 0.0, "mem_total": 0.0,
            "disk_pct": 0.0, "disk_free": 0.0,
            "net_sent": 0.0, "net_recv": 0.0,
            "alerts": []
        }

        self.title("Aeris System Monitor")
        self.geometry("600x650") # Made the window a little taller to fit the new row!
        ctk.set_appearance_mode("Dark")       
        ctk.set_default_color_theme("blue")    

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.label_title = ctk.CTkLabel(self, text="Real-Time System Dashboard", font=("Arial", 20, "bold"))
        self.label_title.grid(row=0, column=0, columnspan=2, pady=15)

        # --- ROW 1: CPU & RAM ---
        self.frame_cpu = ctk.CTkFrame(self)
        self.frame_cpu.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.label_cpu_title = ctk.CTkLabel(self.frame_cpu, text="CPU Usage", font=("Arial", 16, "bold"))
        self.label_cpu_title.pack(pady=5)
        self.pb_cpu = ctk.CTkProgressBar(self.frame_cpu)
        self.pb_cpu.pack(pady=10, padx=20)
        self.pb_cpu.set(0)
        self.label_cpu_stats = ctk.CTkLabel(self.frame_cpu, text="0.0% | Cycles: 0", font=("Arial", 12))
        self.label_cpu_stats.pack(pady=5)
        
        # --- The Boost Mode Switch ---
        self.switch_boost = ctk.CTkSwitch(
            self.frame_cpu, 
            text="Boost Mode (Balanced)", 
            command=self.toggle_boost,
            progress_color="#e74c3c" # Turns crimson red when active
        )
        self.switch_boost.pack(pady=(10, 5))

        self.frame_ram = ctk.CTkFrame(self)
        self.frame_ram.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.label_ram_title = ctk.CTkLabel(self.frame_ram, text="RAM Usage", font=("Arial", 16, "bold"))
        self.label_ram_title.pack(pady=5)
        # self.pb_ram = ctk.CTkProgressBar(self.frame_ram)
        # self.pb_ram.pack(pady=10, padx=20)
        # self.pb_ram.set(0)
        
        self.fig_ram , self.ax_ram = plt.subplots(figsize=(3,2.5),facecolor = "#2b2b2b")
        self.fig_ram.subplots_adjust(left=0,right=1,top=1,bottom=0)

        self.canvas_ram = FigureCanvasTkAgg(self.fig_ram, master=self.frame_ram)
        self.canvas_ram.get_tk_widget().pack(pady=5)

        self.label_ram_stats = ctk.CTkLabel(self.frame_ram, text="0.0% / 0.0GB", font=("Arial", 12))
        self.label_ram_stats.pack(pady=5)

        # --- ROW 2: DISK & NETWORK ---
        self.frame_disk = ctk.CTkFrame(self)
        self.frame_disk.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.label_disk_title = ctk.CTkLabel(self.frame_disk, text="Disk C Storage", font=("Arial", 16, "bold"))
        self.label_disk_title.pack(pady=5)
        self.pb_disk = ctk.CTkProgressBar(self.frame_disk)
        self.pb_disk.pack(pady=10, padx=20)
        self.pb_disk.set(0)
        self.label_disk_stats = ctk.CTkLabel(self.frame_disk, text="0.0% | Free: 0.0GB", font=("Arial", 12))
        self.label_disk_stats.pack(pady=5)

        self.frame_net = ctk.CTkFrame(self)
        self.frame_net.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.label_net_title = ctk.CTkLabel(self.frame_net, text="Network Traffic", font=("Arial", 16, "bold"))
        self.label_net_title.pack(pady=10)
        # Network doesn't have a max limit for a progress bar, so we just use a text readout!
        self.label_net_stats = ctk.CTkLabel(self.frame_net, text="Sent: 0 MB\nRecv: 0 MB", font=("Arial", 13))
        self.label_net_stats.pack(pady=10)

        # --- ROW 3: INCIDENT CENTER ---
        self.label_alert_title = ctk.CTkLabel(self, text="Incident Center", font=("Arial", 14, "bold"))
        self.label_alert_title.grid(row=3, column=0, columnspan=2, pady=(15, 5))
        self.textbox_alerts = ctk.CTkTextbox(self, width=520, height=100)
        self.textbox_alerts.grid(row=4, column=0, columnspan=2, padx=20, pady=10)
        self.textbox_alerts.insert("0.0", "🟢 System Status: Healthy")

        self.start_backend_thread()
        self.update_gui_loop() 

    def toggle_boost(self):
        """Triggers immediately when the user clicks the Boost toggle switch."""
        if self.switch_boost.get() == 1:
            # Switch turned ON -> Force Performance
            success, msg = self.monitor.set_power_mode("high")
            if success:
                self.switch_boost.configure(text="Boost Mode (ACTIVE)", text_color="#e74c3c")
                self.textbox_alerts.insert("0.0", "🚀 SYSTEM TWEAK: CPU set to High Performance Plan.\n")
        else:
            # Switch turned OFF -> Return to normal
            success, msg = self.monitor.set_power_mode("balanced")
            if success:
                self.switch_boost.configure(text="Boost Mode (Balanced)", text_color="white")
                self.textbox_alerts.insert("0.0", "♻️ SYSTEM TWEAK: CPU returned to Balanced power profile.\n")

    def backend_data_collector(self):
        self.monitor.get_cpu_metrics()
        while not self.stop_event.is_set():
            cpu = self.monitor.get_cpu_metrics()
            mem = self.monitor.get_memory_metrics()
            disk = self.monitor.get_disk_metrics()
            net = self.monitor.get_network_metrics() # <-- Fetching network data
            
            active_alerts = self.monitor.check_thresholds(
                cpu['total_usage'], mem['usage_percent'], disk['usage_percent']
            )

            # Update Dictionary
            self.telemetry_data["cpu_pct"] = cpu['total_usage']
            self.telemetry_data["cpu_cycles"] = self.monitor.cpu_breach_count
            self.telemetry_data["mem_pct"] = mem['usage_percent']
            self.telemetry_data["mem_used"] = mem['used_gb']
            self.telemetry_data["mem_total"] = mem['total_gb']
            self.telemetry_data["disk_pct"] = disk['usage_percent']
            self.telemetry_data["disk_free"] = disk['free_gb']
            self.telemetry_data["net_sent"] = net['bytes_sent_mb']
            self.telemetry_data["net_recv"] = net['bytes_recv_mb']
            self.telemetry_data["alerts"] = active_alerts

            time.sleep(1.5) 

    def update_gui_loop(self):
        data = self.telemetry_data
        
        # Update Row 1
        self.pb_cpu.set(data["cpu_pct"] / 100)
        # self.pb_ram.set(data["mem_pct"] / 100)
        self.label_cpu_stats.configure(text=f"{data['cpu_pct']}% | Cycles: {data['cpu_cycles']}")
        self.label_ram_stats.configure(text=f"{data['mem_pct']}% | {data['mem_used']}GB / {data['mem_total']}GB")

        used_gb = data['mem_used']
        available_gb = data['mem_total'] - used_gb
        
        # Clear the old chart frame and draw the new one
        self.ax_ram.clear()
        self.ax_ram.pie(
            [used_gb, available_gb], 
            labels=['Used', 'Available'], 
            colors=['#e74c3c', '#2ecc71'], # Red for used, Green for available
            autopct='%1.1f%%', 
            startangle=90,
            textprops={'color': "white", 'fontsize': 10, 'weight': 'bold'}
        )
        self.canvas_ram.draw()

        if data['cpu_cycles'] > 0:
            self.pb_cpu.configure(progress_color="#e67e22") 
        else:
            self.pb_cpu.configure(progress_color="#3498db") 

        # Update Row 2 (Disk & Network)
        self.pb_disk.set(data["disk_pct"] / 100)
        self.label_disk_stats.configure(text=f"{data['disk_pct']}% | Free: {data['disk_free']}GB")
        self.label_net_stats.configure(text=f"Total Sent: {data['net_sent']} MB\nTotal Recv: {data['net_recv']} MB")

        # Update Incident Center
        self.textbox_alerts.delete("0.0", "end")
        if data['alerts']:
            self.textbox_alerts.insert("0.0", "\n".join(data['alerts']))
        else:
            self.textbox_alerts.insert("0.0", "🟢 System Status: Active & Healthy")

        self.after(1000, self.update_gui_loop)
    
    def start_backend_thread(self):
        self.backend_thread = threading.Thread(target=self.backend_data_collector, daemon=True)
        self.backend_thread.start()

    def on_closing(self):
        self.stop_event.set()
        self.destroy()
        
        
if __name__ == "__main__":
    app = MonitorDashboard()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
