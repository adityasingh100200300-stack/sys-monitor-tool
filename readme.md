# Aeris: Real-Time System Monitor

A modern, lightweight desktop GUI dashboard built with Python that monitors low-level operating system hardware metrics, temperatures, and tracks sustained resource anomalies using multithreading.

## Features
* **Asynchronous Telemetry:** Utilizes Python threading to sample hardware metrics without freezing the interface.
* **Live Visualizations:** Renders real-time Matplotlib pie charts for dynamic memory allocation.
* **Per-Core Tracking:** Dynamically generates scrollable UI frames to track individual logical processor workloads.
* **Modern GUI:** Built using CustomTkinter featuring native high-DPI scaling and automated dark mode integration.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/adityasingh100200300-stack/sys-monitor-tool.git
   cd sys-monitor-tool.git

Create and activate a virtual environment:

   python -m venv venv
venv\Scripts\activate

Install required libraries:

pip install -r requirements.txt


Run the application:

python dashboard_app.py


