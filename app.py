import os
import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "esports_club_key"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL BELOW:
# -------------------------------------------------------------
GOOGLE_SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbx_E1UTPZs-wc7zMCOLNWxVDpUv8IEM9UCjYR9hxSf4rI1KEcPy62s0I-tnRlsm1d5Y/exec"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route 1: Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Route 2: Dedicated registration pages for BGMI and Free Fire
@app.route('/register/<game_type>')
def register_page(game_type):
    game_type = game_type.lower()
    if game_type == 'bgmi':
        game_title = "BGMI (Battlegrounds Mobile India)"
        bg_class = "bgmi-bg"
    elif game_type in ['freefire', 'free-fire']:
        game_title = "Free Fire MAX"
        bg_class = "ff-bg"
    else:
        return redirect(url_for('home'))
        
    return render_template('register.html', game_title=game_title, bg_class=bg_class, game_slug=game_type)

# Route 3: Form submission handler (Sends data directly to Google Sheets)
@app.route('/submit-registration', methods=['POST'])
def submit_registration():
    game = request.form.get('game')
    team_name = request.form.get('team_name')
    full_name = request.form.get('name')
    admission_no = request.form.get('admission_no')
    branch = request.form.get('branch')
    in_game_id = request.form.get('in_game_id')
    contact = request.form.get('contact')
    utr_id = request.form.get('utr_id')
    game_slug = request.form.get('game_slug', 'freefire')

    # Save payment screenshot locally
    file = request.files.get('payment_screenshot')
    if not file or file.filename == '' or not allowed_file(file.filename):
        flash("Invalid file format. Please upload JPG, PNG, or PDF.")
        return redirect(url_for('register_page', game_type=game_slug))

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = secure_filename(file.filename)
    filename = f"{admission_no}_{timestamp_str}_{safe_name}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare data payload for Google Sheets
    payload = {
        "timestamp": timestamp,
        "game": game,
        "team_name": team_name,
        "full_name": full_name,
        "admission_no": admission_no,
        "branch": branch,
        "in_game_id": in_game_id,
        "contact": contact,
        "utr_id": utr_id,
        "screenshot_filename": filename
    }

    # Send data to Google Apps Script Web App
    try:
        response = requests.post(GOOGLE_SHEET_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            flash(f"Slot registered successfully for {game}!")
        else:
            flash("Registered, but cloud sync failed. Please contact admin.")
    except Exception as e:
        print(f"Error syncing to Google Sheets: {e}")
        flash("Server error during registration sync.")

    return redirect(url_for('register_page', game_type=game_slug))

if __name__ == '__main__':
    app.run(debug=True, port=5000)