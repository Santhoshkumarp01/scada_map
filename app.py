from flask import Flask, render_template
import pandas as pd
import networkx as nx
import json
import time

app = Flask(__name__)

# Function to process a single row of syslog data
def process_syslog_row(row, authorized_hosts, anomalies, G):
    hostname = row['host name']
    timestamp = row['timestamp']
    message = row['message']

    if "Neighbor" in message:
        neighbor_ip_start = message.find("Neighbor ") + len("Neighbor ")
        neighbor_ip_end = message.find(" ", neighbor_ip_start)
        neighbor_ip = message[neighbor_ip_start:neighbor_ip_end]

        # Add nodes and edge to the graph
        G.add_node(hostname, color='blue')
        if neighbor_ip in authorized_hosts:
            G.add_node(neighbor_ip, color='blue')
        else:
            G.add_node(neighbor_ip, color='red')
            anomalies.append({
                "timestamp": timestamp,
                "host_router": hostname,
                "anomaly_ip": neighbor_ip
            })

        G.add_edge(hostname, neighbor_ip)

# Function to create the graph for topology rendering
def create_graph_data(G):
    nodes = [{"id": node, "color": G.nodes[node]['color']} for node in G.nodes]
    edges = [{"source": edge[0], "target": edge[1]} for edge in G.edges]
    return {"nodes": nodes, "edges": edges}

# Read the Excel file
EXCEL_FILE = r"C:\Users\Santhosh kumar P\OneDrive\Desktop\Scada_3rd\dataset large.xlsx" # Update the path
try:
    df = pd.read_excel(EXCEL_FILE)

    # Normalize column names
    df.columns = [col.strip().lower() for col in df.columns]

    # Map user-provided column names to expected names
    column_mapping = {
        "time": "timestamp",
        "host name": "host name",
        "message": "message"
    }
    df.rename(columns=column_mapping, inplace=True)

    # Ensure the required columns exist
    required_columns = ["timestamp", "host name", "message"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Excel file must contain 'Time', 'Host Name', and 'Message' columns.")
except Exception as e:
    print(f"Error reading the Excel file: {e}")
    exit()

# Get the list of unique authorized hosts from the Excel data
authorized_hosts = df['host name'].unique()

# Initialize the graph and anomalies list
G = nx.Graph()
anomalies = []

# Flask route to display topology and anomaly table
@app.route('/')
def index():
    for _, row in df.iterrows():
        process_syslog_row(row, authorized_hosts, anomalies, G)
        time.sleep(0.5)  # Simulate real-time row-by-row processing

    topology_data = create_graph_data(G)
    return render_template('index.html',
                           topology_data=json.dumps(topology_data),
                           anomalies=anomalies)

if __name__ == '__main__':
    app.run(debug=True)
