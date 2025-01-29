#!/usr/bin/env python
# Requirements:
# pip install flask
# pip install flask-cors

import os
import json
import uuid
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

class NetworkClipboard:
    def __init__(self, storage_file='clipboard_data.json'):
        """
        Initialize the network clipboard with persistent JSON storage.
        
        Args:
            storage_file (str): Path to JSON file for storing clipboard entries
        """
        self.storage_file = storage_file
        self.data = self.load_data()

    def load_data(self):
        """
        Load clipboard data from JSON file.
        Creates file if it doesn't exist.
        
        Returns:
            dict: Stored clipboard entries
        """
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_data(self):
        """
        Save clipboard data to JSON file.
        """
        with open(self.storage_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def create_entry(self, content):
        """
        Create a new clipboard entry with a unique ID.
        
        Args:
            content (str): Text to be shared
        
        Returns:
            str: Generated unique ID
        """
        entry_id = str(uuid.uuid4())[:8]  # Short unique ID
        self.data[entry_id] = {
            'content': content,
            'timestamp': str(uuid.uuid1())  # For potential future use
        }
        self.save_data()
        return entry_id

    def get_entry(self, entry_id):
        """
        Retrieve clipboard entry by ID.
        
        Args:
            entry_id (str): Unique identifier for the entry
        
        Returns:
            dict or None: Clipboard entry details or None if not found
        """
        return self.data.get(entry_id)

# HTML Template for the Frontend
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Network Clipboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
            background-color: #f0f0f0;
        }
        textarea {
            width: 100%;
            height: 150px;
            margin-bottom: 10px;
            padding: 10px;
            resize: vertical;
        }
        input {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
        }
        button {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        #result {
            margin-top: 20px;
            padding: 10px;
            background-color: #e0e0e0;
        }
    </style>
</head>
<body>
    <h1>Network Clipboard</h1>
    
    <div id="create-section">
        <h2>Create New Clipboard Entry</h2>
        <textarea id="content" placeholder="Enter your text to share"></textarea>
        <button onclick="createEntry()">Create Entry</button>
        <div id="create-result"></div>
    </div>

    <div id="retrieve-section">
        <h2>Retrieve Clipboard Entry</h2>
        <input type="text" id="entry-id" placeholder="Enter Entry ID">
        <button onclick="retrieveEntry()">Retrieve</button>
        <div id="result"></div>
    </div>

    <script>
        function createEntry() {
            const content = document.getElementById('content').value;
            if (!content) {
                alert('Please enter some content');
                return;
            }

            fetch('/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('create-result').innerHTML = 
                    `Entry created! ID: <strong>${data.id}</strong>`;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to create entry');
            });
        }

        function retrieveEntry() {
            const entryId = document.getElementById('entry-id').value;
            if (!entryId) {
                alert('Please enter an Entry ID');
                return;
            }

            fetch(`/get/${entryId}`)
            .then(response => response.json())
            .then(data => {
                if (data.content) {
                    document.getElementById('result').innerHTML = 
                        `<strong>Retrieved Content:</strong><br>${data.content}`;
                } else {
                    document.getElementById('result').innerHTML = 
                        'Entry not found or invalid ID';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to retrieve entry');
            });
        }
    </script>
</body>
</html>
'''

# Flask Application Setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
clipboard = NetworkClipboard()

@app.route('/')
def index():
    """
    Render the main HTML page for clipboard interaction.
    """
    return render_template_string(HTML_TEMPLATE)

@app.route('/create', methods=['POST'])
def create_clipboard_entry():
    """
    Endpoint to create a new clipboard entry.
    
    Expects JSON with 'content' field.
    Returns generated unique ID.
    """
    data = request.json
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required"}), 400
    
    entry_id = clipboard.create_entry(data['content'])
    return jsonify({"id": entry_id})

@app.route('/get/<entry_id>', methods=['GET'])
def get_clipboard_entry(entry_id):
    """
    Endpoint to retrieve clipboard entry by ID.
    
    Returns entry content or 404 if not found.
    """
    entry = clipboard.get_entry(entry_id)
    if entry:
        return jsonify(entry)
    return jsonify({"error": "Entry not found"}), 404

def get_local_ip():
    """
    Utility function to get local IP address.
    
    Returns:
        str: Local network IP address
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send packets
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def main():
    """
    Main function to start the Flask server.
    """
    local_ip = get_local_ip()
    print(f"Network Clipboard Server running on http://{local_ip}:5000")
    print(f"Open this URL in any browser on the local network")
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
