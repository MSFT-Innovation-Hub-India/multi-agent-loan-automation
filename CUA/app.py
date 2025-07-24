from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
import time
import queue
import json
import sys
import io
import contextlib
import re
import os

app = Flask(__name__)
CORS(app)

# Store active lookup sessions
active_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start-lookup', methods=['POST'])
def start_lookup():
    try:
        data = request.json
        customer_id = data.get('customer_id', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not customer_id or not username or not password:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Create a unique session ID
        session_id = f"session_{int(time.time())}"
        
        # Create queues for communication
        status_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # Store session info
        active_sessions[session_id] = {
            'status_queue': status_queue,
            'result_queue': result_queue,
            'customer_id': customer_id,
            'username': username,
            'password': password
        }
        
        # Start the agent in a separate thread
        agent_thread = threading.Thread(
            target=run_agent_with_session,
            args=(session_id, customer_id, username, password, status_queue, result_queue)
        )
        agent_thread.daemon = True
        agent_thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    try:
        if session_id not in active_sessions:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        session = active_sessions[session_id]
        status_queue = session['status_queue']
        result_queue = session['result_queue']
        
        # Check for results first
        try:
            result = result_queue.get_nowait()
            # Clean up session
            del active_sessions[session_id]
            return jsonify({
                'success': True,
                'status': 'completed',
                'result': result
            })
        except queue.Empty:
            pass
        
        # Check for status updates
        try:
            status = status_queue.get_nowait()
            return jsonify({
                'success': True,
                'status': 'processing',
                'message': status
            })
        except queue.Empty:
            return jsonify({
                'success': True,
                'status': 'processing',
                'message': 'Agent is working...'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

class StatusCapture:
    """Capture print statements and status updates from the agent"""
    def __init__(self, status_queue):
        self.status_queue = status_queue
        self.output = []
    
    def write(self, text):
        if text.strip():
            self.status_queue.put(text.strip())
            self.output.append(text.strip())
        sys.__stdout__.write(text)
    
    def flush(self):
        sys.__stdout__.flush()

def run_agent_with_session(session_id, customer_id, username, password, status_queue, result_queue):
    """Run the entire agent.py main() function with captured output"""
    original_input = None
    try:
        status_queue.put("Starting agent...")
        
        # Import the agent module
        import agent
        import builtins
        
        # Monkey patch the input function to provide our values automatically
        original_input = builtins.input
        
        input_responses = [customer_id, username, password]
        input_index = 0
        
        def mock_input(prompt=""):
            nonlocal input_index
            if input_index < len(input_responses):
                response = input_responses[input_index]
                input_index += 1
                status_queue.put(f"Input: {prompt} -> {response}")
                return response
            return original_input(prompt)
        
        # Replace input function
        builtins.input = mock_input
        
        # Capture stdout to monitor agent progress
        status_capture = StatusCapture(status_queue)
        
        with contextlib.redirect_stdout(status_capture):
            # Run the agent's main function
            agent.main()
        
        # Restore original input
        builtins.input = original_input
        
        # Extract CRM reference from the captured output
        full_output = ' '.join(status_capture.output)
        
        # The extraction should happen in agent_modified.py, but we'll have a simple fallback here
        crm_ref = None
        
        # Simple fallback patterns for any missed cases
        simple_patterns = [
            r'GTBCRM[0-9]{6,}',
            r'[A-Z]{3,}CRM[0-9]{6,}',
            r'["\']([A-Z0-9]{8,})["\']'
        ]
        
        status_queue.put(f"Checking for CRM reference in agent output...")
        status_queue.put(f"Output preview: {full_output[:300]}...")
        
        for pattern in simple_patterns:
            match = re.search(pattern, full_output, re.IGNORECASE)
            if match:
                potential_ref = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if len(potential_ref) >= 8 and re.match(r'^[A-Z0-9]+$', potential_ref):
                    crm_ref = potential_ref.strip()
                    status_queue.put(f"Fallback extraction found: {crm_ref}")
                    break
        
        if crm_ref:
            status_queue.put(f"Successfully extracted CRM Reference: {crm_ref}")
            result_queue.put({
                'customer_id': customer_id,
                'crm_ref': crm_ref
            })
        else:
            status_queue.put("Could not extract CRM reference from agent output")
            status_queue.put(f"Full captured output: {full_output}")
            result_queue.put({
                'error': 'Could not find CRM reference number in agent output',
                'debug_output': full_output[:500]  # First 500 chars for debugging
            })
            
    except Exception as e:
        status_queue.put(f"Agent error: {str(e)}")
        result_queue.put({
            'error': f'Agent error: {str(e)}'
        })
    finally:
        # Restore original input if something went wrong
        if original_input is not None:
            import builtins
            builtins.input = original_input

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8080)
