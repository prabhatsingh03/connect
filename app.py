from flask import Flask, render_template, request, jsonify, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))  # Load from .env
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.urandom(24))  # Load from .env
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token expires in 24 hours

jwt = JWTManager(app)

# Load admin credentials from environment variables
USERS = {
    os.getenv('ADMIN_USERNAME', 'admin@simonindia.ai'): os.getenv('ADMIN_PASSWORD', 'admin123')
}


@app.route('/')
def landing():
    """Main landing page"""
    return render_template('landing.html')


@app.route('/Application')
def Application():
    """Application page - public access"""
    return render_template('Application.html')


@app.route('/employee-corner')
def employee_corner():
    """Employee Corner - Coming Soon page"""
    return render_template('employee_corner.html')


@app.route('/forms')
def forms():
    """Forms page - requires login"""
    return render_template('forms.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint"""
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        
        # Validate credentials
        if username in USERS and USERS[username] == password:
            # Create JWT token
            access_token = create_access_token(identity=username)
            session['access_token'] = access_token
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful', 'token': access_token})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.pop('access_token', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
