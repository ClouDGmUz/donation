from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
import sqlite3
import os
from datetime import datetime
import urllib.parse

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'your-secret-key-change-this'

# Configure static files for production
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache

# Configuration
CRYPTO_ADDRESS = 'TLLjsnXvTKheaDBRMf7Y5NPhZ5v8kb627k'  # USDT TRC20 address
DATABASE = 'donations.db'

# Manual donation tracking - Update these values manually when you receive donations
RAISED_AMOUNT = 0.0      # Total amount raised so far
GOAL_AMOUNT = 3500.0     # Target goal amount
REMAINING_AMOUNT = 3500.0  # Remaining amount needed (GOAL_AMOUNT - RAISED_AMOUNT)

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create components table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            status TEXT DEFAULT 'needed',
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create donations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            donor_name TEXT,
            message TEXT,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default components if table is empty
    cursor.execute('SELECT COUNT(*) FROM components')
    if cursor.fetchone()[0] == 0:
        default_components = [
            ('AMD Ryzen 9 7900X', 'High-performance 12-core processor for gaming and productivity', 549.99, 'needed', '/static/images/cpu.jpg'),
            ('ASUS ROG Strix X670E-E', 'Premium motherboard with WiFi 6E and PCIe 5.0 support', 499.99, 'needed', '/static/images/motherboard.jpg'),
            ('NVIDIA RTX 4080 Super', 'Flagship graphics card for 4K gaming and content creation', 999.99, 'needed', '/static/images/gpu.jpg'),
            ('32GB DDR5-5600 RAM', 'High-speed memory for smooth multitasking', 299.99, 'needed', '/static/images/ram.jpg'),
            ('2TB NVMe SSD', 'Ultra-fast storage for games and applications', 199.99, 'needed', '/static/images/ssd.jpg'),
            ('850W 80+ Gold PSU', 'Reliable power supply with modular cables', 149.99, 'needed', '/static/images/psu.jpg'),
            ('Fractal Define 7', 'Silent and spacious PC case with excellent airflow', 179.99, 'needed', '/static/images/case.jpg'),
            ('Noctua NH-D15', 'Premium air cooler for optimal CPU temperatures', 99.99, 'needed', '/static/images/cooler.jpg'),
            ('ASUS ROG Swift PG32UQX', '32" 4K 144Hz HDR gaming monitor with G-Sync Ultimate', 2999.99, 'needed', '/static/images/monitor.jpg'),
            ('Logitech G Pro X Superlight', 'Ultra-lightweight wireless gaming mouse with HERO sensor', 149.99, 'needed', '/static/images/mice.jpg'),
            ('SteelSeries Arctis Pro Wireless', 'Premium wireless gaming headset with Hi-Res audio', 329.99, 'needed', '/static/images/headset.jpg')
        ]
        
        cursor.executemany(
            'INSERT INTO components (name, description, price, status, image_url) VALUES (?, ?, ?, ?, ?)',
            default_components
        )
    
    conn.commit()
    conn.close()

def get_total_donations():
    """Get total raised amount (manually updated)"""
    return RAISED_AMOUNT

def get_total_goal():
    """Get target goal amount (manually set)"""
    return GOAL_AMOUNT

def get_remaining_amount():
    """Get remaining amount needed (manually updated)"""
    return REMAINING_AMOUNT

def get_progress_percentage():
    """Calculate funding progress percentage"""
    if GOAL_AMOUNT > 0:
        return min((RAISED_AMOUNT / GOAL_AMOUNT) * 100, 100)
    return 0

def get_components():
    """Get all components from database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM components ORDER BY id')
    components = cursor.fetchall()
    conn.close()
    
    return [{
        'id': comp[0],
        'name': comp[1],
        'description': comp[2],
        'price': comp[3],
        'status': comp[4],
        'image_url': comp[5],
        'created_at': comp[6]
    } for comp in components]

def get_recent_donations(limit=5):
    """Get recent donations from database (kept for template compatibility)"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM donations ORDER BY created_at DESC LIMIT ?', (limit,))
    donations = cursor.fetchall()
    conn.close()
    
    return [{
        'id': don[0],
        'amount': don[1],
        'donor_name': don[2],
        'message': don[3],
        'status': don[4],
        'created_at': don[5]
    } for don in donations]

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files directly through Flask as fallback"""
    return send_from_directory(app.static_folder, filename)

@app.route('/qr-code')
def generate_qr_code():
    """Generate QR code dynamically using QR Code Monkey API"""
    # QR Code Monkey API configuration
    qr_config = {
        "body": "square",
        "eye": "frame0",
        "eyeBall": "ball0",
        "erf1": [],
        "erf2": [],
        "erf3": [],
        "brf1": [],
        "brf2": [],
        "brf3": [],
        "bodyColor": "#000000",
        "bgColor": "#FFFFFF",
        "eye1Color": "#000000",
        "eye2Color": "#000000",
        "eye3Color": "#000000",
        "eyeBall1Color": "#000000",
        "eyeBall2Color": "#000000",
        "eyeBall3Color": "#000000",
        "gradientColor1": "",
        "gradientColor2": "",
        "gradientType": "linear",
        "gradientOnEyes": "true",
        "logo": "",
        "logoMode": "default"
    }
    
    # Convert config to JSON string and URL encode it
    import json
    config_json = json.dumps(qr_config)
    config_encoded = urllib.parse.quote(config_json)
    
    # Build the QR Code Monkey API URL
    qr_url = f"https://api.qrcode-monkey.com/qr/custom?download=true&file=png&data={CRYPTO_ADDRESS}&size=300&config={config_encoded}"
    
    # Redirect to the QR code image
    return redirect(qr_url)

@app.route('/')
def index():
    """Main page displaying donation progress and components"""
    total_donations = get_total_donations()
    total_goal = get_total_goal()
    progress = get_progress_percentage()
    components = get_components()
    recent_donations = get_recent_donations()
    
    return render_template('index.html', 
                         total_donations=total_donations,
                         target_amount=total_goal,
                         progress=progress,
                         components=components,
                         recent_donations=recent_donations,
                         crypto_address=CRYPTO_ADDRESS,
                         remaining_amount=get_remaining_amount())

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    """Handle donation form submission"""
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            donor_name = request.form.get('donor_name', 'Anonymous')
            message = request.form.get('message', '')
            
            flash(f'Thank you {donor_name} for your ${amount:.2f} donation! Please send the payment to the provided USDT address.', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Please enter a valid amount.', 'error')
    
    # Get data for template
    total_donations = get_total_donations()
    total_goal = get_total_goal()
    progress = get_progress_percentage()
    recent_donations = get_recent_donations()
    
    return render_template('donate.html', 
                         crypto_address=CRYPTO_ADDRESS,
                         total_donations=total_donations,
                         target_amount=total_goal,
                         progress=progress,
                         recent_donations=recent_donations,
                         remaining_amount=get_remaining_amount())

@app.route('/components')
def components():
    """Display all PC components and their status"""
    components = get_components()
    
    # Calculate component status counts
    purchased_count = sum(1 for comp in components if comp['status'] == 'purchased')
    ordered_count = sum(1 for comp in components if comp['status'] == 'ordered')
    needed_count = sum(1 for comp in components if comp['status'] == 'needed')
    
    # Get progress data
    total_donations = get_total_donations()
    total_goal = get_total_goal()
    progress = get_progress_percentage()
    
    return render_template('components.html', 
                         components=components,
                         purchased_count=purchased_count,
                         ordered_count=ordered_count,
                         needed_count=needed_count,
                         total_donations=total_donations,
                         target_amount=total_goal,
                         progress=progress,
                         remaining_amount=get_remaining_amount())





@app.route('/api/progress')
def api_progress():
    """API endpoint for real-time progress updates"""
    return jsonify({
        'total_donations': get_total_donations(),
        'target_amount': get_total_goal(),
        'progress_percentage': get_progress_percentage()
    })

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)