from flask import Flask, render_template, request, jsonify, session, send_from_directory, Response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
from dotenv import load_dotenv
import os
import sqlite3
from werkzeug.utils import secure_filename
import uuid
import csv
import io

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.urandom(24))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

jwt = JWTManager(app)

# Load admin credentials from environment variables
USERS = {
    os.getenv('ADMIN_USERNAME'): os.getenv('ADMIN_PASSWORD')
}

# SQLite database setup
DB_FILE = 'news_posts.db'
REFERRALS_DB_FILE = 'referrals.db'

def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            author TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_referrals_db():
    """Initialize the referrals database"""
    conn = sqlite3.connect(REFERRALS_DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            candidate_email TEXT NOT NULL,
            candidate_mobile TEXT NOT NULL,
            position TEXT NOT NULL,
            department TEXT NOT NULL,
            experience TEXT NOT NULL,
            current_company TEXT NOT NULL,
            current_location TEXT NOT NULL,
            notice_period TEXT NOT NULL,
            cv_link TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_referrals_db():
    """Get database connection for referrals"""
    conn = sqlite3.connect(REFERRALS_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize databases and create upload folder
init_db()
init_referrals_db()
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


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
    """Employee Corner page"""
    return render_template('employee_corner.html')


@app.route('/forms')
def forms():
    """Forms page - requires login"""
    return render_template('forms.html')


@app.route('/login', methods=['POST'])
def login():
    """Login endpoint - API only"""
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


@app.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.pop('access_token', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/news', methods=['GET', 'POST'])
def news_posts():
    """Handle news posts - GET all posts, POST new post"""
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news_posts ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        posts = [dict(row) for row in rows]
        return jsonify({'success': True, 'posts': posts})
    
    elif request.method == 'POST':
        # Check if user is authenticated
        if 'username' not in session or 'access_token' not in session:
            return jsonify({'success': False, 'message': 'Authentication required. Please login first.'}), 401
        
        try:
            title = request.form.get('title', '').strip()
            category = request.form.get('category', 'General')
            content = request.form.get('content', '').strip()
            
            if not title or not content:
                return jsonify({'success': False, 'message': 'Title and content are required'}), 400
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    # Generate unique filename
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}.{ext}"
                    filename = secure_filename(unique_filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_path = f"uploads/images/{filename}"
            
            # Insert into database
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO news_posts (title, category, content, image_path, author, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, category, content, image_path, session.get('username', 'HR Team'), datetime.now().isoformat()))
            conn.commit()
            post_id = cursor.lastrowid
            conn.close()
            
            return jsonify({'success': True, 'message': 'Post created successfully', 'post_id': post_id})
        
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/news/<int:post_id>', methods=['PUT', 'DELETE'])
def news_post_operations(post_id):
    """Update or delete a news post - requires authentication"""
    # Check if user is authenticated
    if 'username' not in session or 'access_token' not in session:
        return jsonify({'success': False, 'message': 'Authentication required. Please login first.'}), 401
    
    try:
        if request.method == 'PUT':
            # Update post
            title = request.form.get('title', '').strip()
            category = request.form.get('category', 'General')
            content = request.form.get('content', '').strip()
            
            if not title or not content:
                return jsonify({'success': False, 'message': 'Title and content are required'}), 400
            
            conn = get_db()
            cursor = conn.cursor()
            
            # Handle image upload if provided
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    # Get old image path
                    cursor.execute('SELECT image_path FROM news_posts WHERE id = ?', (post_id,))
                    old_row = cursor.fetchone()
                    
                    # Delete old image if exists
                    if old_row and old_row['image_path'] and os.path.exists(old_row['image_path']):
                        os.remove(old_row['image_path'])
                    
                    # Save new image
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}.{ext}"
                    filename = secure_filename(unique_filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_path = f"uploads/images/{filename}"
            
            # Update database
            if image_path:
                cursor.execute('''
                    UPDATE news_posts 
                    SET title = ?, category = ?, content = ?, image_path = ?, timestamp = ?
                    WHERE id = ?
                ''', (title, category, content, image_path, datetime.now().isoformat(), post_id))
            else:
                cursor.execute('''
                    UPDATE news_posts 
                    SET title = ?, category = ?, content = ?, timestamp = ?
                    WHERE id = ?
                ''', (title, category, content, datetime.now().isoformat(), post_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Post updated successfully'})
        
        elif request.method == 'DELETE':
            # Delete post
            conn = get_db()
            cursor = conn.cursor()
            
            # Get image path if exists
            cursor.execute('SELECT image_path FROM news_posts WHERE id = ?', (post_id,))
            row = cursor.fetchone()
            
            if row and row['image_path']:
                # Delete image file
                image_path = row['image_path']
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            # Delete from database
            cursor.execute('DELETE FROM news_posts WHERE id = ?', (post_id,))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Post deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'username' in session and 'access_token' in session:
        return jsonify({'success': True, 'authenticated': True, 'username': session.get('username')})
    else:
        return jsonify({'success': True, 'authenticated': False})


@app.route('/uploads/images/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/referrals', methods=['GET', 'POST'])
def referrals():
    """Handle referrals - GET all referrals (admin only), POST new referral"""
    if request.method == 'GET':
        # Check if user is authenticated (admin only)
        if 'username' not in session or 'access_token' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        conn = get_referrals_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM referrals ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        referrals_list = [dict(row) for row in rows]
        return jsonify({'success': True, 'referrals': referrals_list})
    
    elif request.method == 'POST':
        try:
            data = request.json
            conn = get_referrals_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO referrals (
                    employee_name, employee_id, candidate_name, candidate_email, 
                    candidate_mobile, position, department, experience, 
                    current_company, current_location, notice_period, cv_link, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('employeeName', ''),
                data.get('employeeId', ''),
                data.get('candidateName', ''),
                data.get('candidateEmail', ''),
                data.get('candidateMobile', ''),
                data.get('position', ''),
                data.get('department', ''),
                data.get('experience', ''),
                data.get('currentCompany', ''),
                data.get('currentLocation', ''),
                data.get('noticePeriod', ''),
                data.get('cvLink', ''),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Referral submitted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/referrals/export-excel')
def export_referrals_excel():
    """Export referrals as Excel (CSV format) - admin only"""
    # Check if user is authenticated
    if 'username' not in session or 'access_token' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    try:
        conn = get_referrals_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM referrals ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Employee Name', 'Employee ID', 'Candidate Name', 'Candidate Email',
            'Candidate Mobile', 'Position', 'Department', 'Years of Experience',
            'Current Company', 'Current Location', 'Notice Period', 'CV Link'
        ])
        
        # Write data
        for row in rows:
            writer.writerow([
                row['timestamp'],
                row['employee_name'],
                row['employee_id'],
                row['candidate_name'],
                row['candidate_email'],
                row['candidate_mobile'],
                row['position'],
                row['department'],
                row['experience'],
                row['current_company'],
                row['current_location'],
                row['notice_period'],
                row['cv_link'] or ''
            ])
        
        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        # Create response
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=referrals_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
        return response
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

