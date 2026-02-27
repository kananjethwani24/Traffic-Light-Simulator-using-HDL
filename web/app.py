from flask import Flask, render_template, jsonify, request, send_file
import time
import threading
import subprocess
import os
import shutil

app = Flask(__name__)

# --- FSM STATE ---
class TrafficLightFSM:
    def __init__(self):
        # Constants matching Verilog
        self.S_NS_GREEN  = 0
        self.S_NS_YELLOW = 1
        self.S_EW_GREEN  = 2
        self.S_EW_YELLOW = 3
        self.S_EMERG_NS  = 4
        self.S_EMERG_EW  = 5

        # Initial Timing (modifiable)
        self.time_green_ns = 10
        self.time_green_ew = 10
        self.TIME_YELLOW = 3

        self.current_state = self.S_NS_GREEN
        self.timer = 0
        self.last_update = time.time()
        self.emerg_north = False
        self.emerg_south = False
        self.emerg_east = False
        self.emerg_west = False
        
        # Analytics Data
        self.emergency_log = []
        self.total_cycles = 0
        self.signal_history = []

    def update(self):
        now = time.time()
        if now - self.last_update >= 1.0:
            self.timer += 1
            self.last_update = now
            self._transition()
            self._log_signals()

    def _log_signals(self):
        # Capture digital state of signals for waveform
        current_time = time.strftime("%H:%M:%S")
        
        # Determine signals
        lights = self.get_lights() # Returns {'N': 'GREEN', ...}
        
        # Map to 0/1
        sig_data = {
            'time': current_time,
            'ns_g': 1 if lights['N'] == 'GREEN' else 0,
            'ns_y': 1 if lights['N'] == 'YELLOW' else 0,
            'ns_r': 1 if lights['N'] == 'RED' else 0,
            'ew_g': 1 if lights['E'] == 'GREEN' else 0,
            'ew_y': 1 if lights['E'] == 'YELLOW' else 0,
            'ew_r': 1 if lights['E'] == 'RED' else 0,
            'emerg': 1 if (self.emerg_north or self.emerg_south or self.emerg_east or self.emerg_west) else 0
        }
        
        self.signal_history.append(sig_data)
        if len(self.signal_history) > 50:
            self.signal_history.pop(0)

    def _transition(self):
        next_state = self.current_state
        
        # Determine Current Green Time based on state
        current_green_limit = self.time_green_ns if self.current_state == self.S_NS_GREEN else self.time_green_ew

        # Emergency Logic
        if self.emerg_north or self.emerg_south:
            if self.current_state == self.S_EW_GREEN:
                next_state = self.S_EW_YELLOW
            elif self.current_state == self.S_EW_YELLOW:
                if self.timer >= self.TIME_YELLOW:
                    next_state = self.S_EMERG_NS
                    self.timer = 0
            elif self.current_state in [self.S_NS_GREEN, self.S_NS_YELLOW]:
                 next_state = self.S_EMERG_NS
                 self.timer = 0
            elif self.current_state == self.S_EMERG_EW:
                 next_state = self.S_EW_YELLOW 
                 self.timer = 0
            elif self.current_state == self.S_EMERG_NS:
                 pass 
            else:
                 next_state = self.S_EMERG_NS
                 self.timer = 0
        
        elif self.emerg_east or self.emerg_west:
             if self.current_state == self.S_NS_GREEN:
                next_state = self.S_NS_YELLOW
             elif self.current_state == self.S_NS_YELLOW:
                if self.timer >= self.TIME_YELLOW:
                    next_state = self.S_EMERG_EW
                    self.timer = 0
             elif self.current_state in [self.S_EW_GREEN, self.S_EW_YELLOW]:
                 next_state = self.S_EMERG_EW
                 self.timer = 0
             elif self.current_state == self.S_EMERG_NS:
                 next_state = self.S_NS_YELLOW
                 self.timer = 0
             elif self.current_state == self.S_EMERG_EW:
                 pass
             else:
                 next_state = self.S_EMERG_EW
                 self.timer = 0

        else:
            # Normal Operation
            if self.current_state == self.S_NS_GREEN and self.timer >= self.time_green_ns:
                next_state = self.S_NS_YELLOW
                self.timer = 0
            elif self.current_state == self.S_NS_YELLOW and self.timer >= self.TIME_YELLOW:
                next_state = self.S_EW_GREEN
                self.timer = 0
            elif self.current_state == self.S_EW_GREEN and self.timer >= self.time_green_ew:
                next_state = self.S_EW_YELLOW
                self.timer = 0
            elif self.current_state == self.S_EW_YELLOW and self.timer >= self.TIME_YELLOW:
                next_state = self.S_NS_GREEN
                self.timer = 0
            elif self.current_state == self.S_EMERG_NS:
                next_state = self.S_NS_GREEN 
                self.timer = 0
            elif self.current_state == self.S_EMERG_EW:
                next_state = self.S_EW_GREEN 
                self.timer = 0

        self.current_state = next_state

    def get_lights(self):
        lights = {'N': 'RED', 'S': 'RED', 'E': 'RED', 'W': 'RED'}
        if self.current_state in [self.S_NS_GREEN, self.S_EMERG_NS]:
            lights['N'] = 'GREEN'; lights['S'] = 'GREEN'
        elif self.current_state == self.S_NS_YELLOW:
            lights['N'] = 'YELLOW'; lights['S'] = 'YELLOW'
        elif self.current_state in [self.S_EW_GREEN, self.S_EMERG_EW]:
            lights['E'] = 'GREEN'; lights['W'] = 'GREEN'
        elif self.current_state == self.S_EW_YELLOW:
            lights['E'] = 'YELLOW'; lights['W'] = 'YELLOW'
        return lights

    def get_wait_times(self):
        # Calculate time until Green for each direction
        # Note: simplistic calculation assuming no emergency overrides
        
        ns_wait = 0
        ew_wait = 0
        
        # NS Wait
        if self.current_state == self.S_NS_GREEN: ns_wait = 0
        elif self.current_state == self.S_NS_YELLOW: ns_wait = self.TIME_YELLOW + self.time_green_ew + self.TIME_YELLOW 
        elif self.current_state == self.S_EW_GREEN: ns_wait = (self.time_green_ew - self.timer) + self.TIME_YELLOW
        elif self.current_state == self.S_EW_YELLOW: ns_wait = (self.TIME_YELLOW - self.timer)
        
        # EW Wait
        if self.current_state == self.S_EW_GREEN: ew_wait = 0
        elif self.current_state == self.S_EW_YELLOW: ew_wait = self.TIME_YELLOW + self.time_green_ns + self.TIME_YELLOW
        elif self.current_state == self.S_NS_GREEN: ew_wait = (self.time_green_ns - self.timer) + self.TIME_YELLOW
        elif self.current_state == self.S_NS_YELLOW: ew_wait = (self.TIME_YELLOW - self.timer)
        
        return {'ns': max(0, ns_wait), 'ew': max(0, ew_wait)}

fsm = TrafficLightFSM()

# Background thread to run FSM
def run_fsm():
    while True:
        fsm.update()
        time.sleep(0.1)

t = threading.Thread(target=run_fsm, daemon=True)
t.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/status')
def status():
    return jsonify({
        'lights': fsm.get_lights(),
        'timer': fsm.timer,
        'state': fsm.current_state,
        'waits': fsm.get_wait_times(),
        'config': {'green_ns': fsm.time_green_ns, 'green_ew': fsm.time_green_ew},
        'emerg_status': {
            'N': fsm.emerg_north,
            'S': fsm.emerg_south,
            'E': fsm.emerg_east,
            'W': fsm.emerg_west
        }
    })

@app.route('/config', methods=['POST'])
def config():
    data = request.json
    if 'green_ns' in data: fsm.time_green_ns = int(data['green_ns'])
    if 'green_ew' in data: fsm.time_green_ew = int(data['green_ew'])
    return jsonify({'status': 'ok'})

@app.route('/emergency', methods=['POST'])
def emergency():
    data = request.json
    direction = data.get('direction')
    active = data.get('active', True)
    
    # Log event if activating
    if active:
        timestamp = time.strftime("%H:%M:%S")
        fsm.emergency_log.insert(0, {'time': timestamp, 'dir': direction.upper(), 'type': 'Override'})
        # Keep log size manageable
        if len(fsm.emergency_log) > 20: fsm.emergency_log.pop()

    if direction == 'north': fsm.emerg_north = active
    elif direction == 'south': fsm.emerg_south = active
    elif direction == 'east': fsm.emerg_east = active
    elif direction == 'west': fsm.emerg_west = active
    
    return jsonify({'status': 'ok'})

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/history')
def history():
    # Return dummy data for now, real logging would go here
    return jsonify({
        'emergency_log': fsm.emergency_log if hasattr(fsm, 'emergency_log') else [],
        'total_cycles': fsm.total_cycles if hasattr(fsm, 'total_cycles') else 0,
        'avg_wait': 12.5, # Mock data
        'waveform': fsm.signal_history if hasattr(fsm, 'signal_history') else []
    })

@app.route('/simulation')
def simulation():
    return render_template('simulation.html')

@app.route('/api/verilog/code')
def get_verilog_code():
    try:
        with open('traffic_light_controller.v', 'r') as f:
            controller_code = f.read()
        with open('tb_traffic_light_controller.v', 'r') as f:
            tb_code = f.read()
        return jsonify({'controller': controller_code, 'testbench': tb_code})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verilog/run', methods=['POST'])
def run_verilog():
    try:
        # Using absolute paths for Windows since they aren't in System PATH
        iverilog_path = r'C:\iverilog\bin\iverilog.exe'
        vvp_path = r'C:\iverilog\bin\vvp.exe'

        # Check if paths exist
        if not os.path.exists(iverilog_path):
             return jsonify({'success': False, 'output': "Icarus Verilog not found at C:\\iverilog\\bin\\. Please install it or update app.py paths."})

        # Run iverilog
        compile_process = subprocess.run(
            [iverilog_path, '-o', 'traffic_light_sim', 'traffic_light_controller.v', 'tb_traffic_light_controller.v'],
            capture_output=True, text=True
        )
        if compile_process.returncode != 0:
            return jsonify({'success': False, 'output': f"Compilation Error:\n{compile_process.stderr}"})

        # Run vvp
        sim_process = subprocess.run(
            [vvp_path, 'traffic_light_sim'],
            capture_output=True, text=True
        )
        return jsonify({'success': True, 'output': sim_process.stdout})
    except Exception as e:
        return jsonify({'success': False, 'output': f"Execution Error: {str(e)}"})

@app.route('/api/verilog/gtkwave', methods=['POST'])
def launch_gtkwave():
    try:
        # Launch VS Code with the VCD file using Windows 'code' command
        subprocess.Popen(['code', 'traffic_light.vcd'], shell=True)
        return jsonify({'success': True, 'message': 'Launched VS Code (Wavetrace)'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to launch VS Code: {str(e)}"})

@app.route('/download/vcd')
def download_vcd():
    try:
        # Assuming run from root dir, file is in root
        if os.path.exists('traffic_light.vcd'):
             return send_file('../traffic_light.vcd', as_attachment=True)
        return "File not found. Run simulation first.", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=False, port=5001, host='0.0.0.0')
