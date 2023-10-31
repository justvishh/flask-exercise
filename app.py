import subprocess
import json
from flask import Flask, Blueprint, request, jsonify
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

#Creating a blueprint for the application 'app.py'
mod_ip = Blueprint('mod_ip',__name__)

#Create a function called as 'run_cmd' take input params as 'cmd'
#Use the subprocess module
def run_cmd(cmd):
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr

#Create a function 'parse_ping_putput' take params as 'output'
def parse_ping_output(output):
    lines = output.split('\n')
    # Extracting the necessary information from ping output
    transmitted = received = min_latency = max_latency = 0
    for line in lines:
        if "packets transmitted" in line:
            transmitted = int(line.split()[0])
            received = int(line.split()[3])
        if "rtt min/avg/max/mdev" in line:
            parts = line.split('/')
            min_latency = parts[3]
            max_latency = parts[4]
    packet_loss = ((transmitted - received) / transmitted) * 100 if transmitted > 0 else 0
    parsed_data = {
        "ip-address": request.json["ip-address"],
        "count": request.json["count"],
        "transmitted": transmitted,
        "received": received,
        "Packet-loss": f"{packet_loss:.2f}%",
        "latency": {
            "min": min_latency,
            "max": max_latency
        }
    }
    return parsed_data

@mod_ip.route('/api/v1/ip-address/test', methods=['POST'])

#create a function called as 'do_ping' take 2 params 'ip','count'
def do_ping():
    try:
        data = request.get_json()
        ip_address = data["ip-address"]
        count = data["count"]
        cmd = f"ping {ip_address} -c {count}"
        raw_output = run_cmd(cmd)
        parsed_output = parse_ping_output(raw_output)
        app.logger.info(f"Ping test results for {ip_address}:{parsed_output}")
        return jsonify(parsed_output)
    except (json.JSONDecodeError, subprocess.CalledProcessError) as e:
        app.logger.error(f"Error during ping test: {str(e)}")
        return jsonify({"error": "Error occurred"})

#configure logging
log_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
app.logger.addHandler(console_handler)

# Register the mod_ip blueprint
app.register_blueprint(mod_ip)

if __name__ == '__main__':
    app.run(debug=True)


