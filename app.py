from flask import Flask, render_template, redirect, url_for, request, jsonify, session
import secrets
import json
from hydraulics.diagram_handler import run_solver

app = Flask(__name__)

app.secret_key = secrets.token_urlsafe(16)

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/draw')
def draw():
    return render_template("draw.html")

@app.route('/solve', methods=['GET', 'POST'])
def solve():
    if request.method == 'POST':
        try:
            diagram = request.get_json(silent=True)
            session['diagram'] = diagram
            status, message, result = run_solver(diagram)
            session['status'] = status
            session['result'] = result
            return jsonify({'status': status,
                            'message': message,
                            'result': result})
        except json.JSONDecodeError:
            return jsonify(data={'status': 'error', 'message': 'Invalid JSON'},
                           statusCode=400)
    else:
        return jsonify({'status': session.get('status'),
                        'diagram': session.get('diagram'),
                        'result': session.get('result')})

