import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai  # Import Gemini API
from flask_migrate import Migrate  # Import Flask-Migrate
from ultralytics import YOLO  # Import YOLOv8
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, template_folder='client/templates', static_folder='client/static')

# Set the secret key
app.secret_key = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6'

# Get the absolute path to the instance folder
basedir = os.path.abspath(os.path.dirname(__file__))

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "farmers.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)  # Add this line after initializing db

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Load from .env
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Load from .env
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')  # Load from .env

mail = Mail(app)

# Configure Gemini API
GEMINI_API_KEY = 'AIzaSyCz1HueJ6QPaDXbRLNpuGWqyWZdgZsKW-4'  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model_name = 'models/gemini-1.5-flash-latest'  # Use the supported model
model = genai.GenerativeModel(model_name)

# Load the YOLOv8 model for disease detection
yolo_model = YOLO("models/best (1).pt")  # Path to your trained YOLOv8 model

# Define the upload folder for images
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Database Model for Farmers
class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password

# Database Model for Products
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_name = db.Column(db.String(100), nullable=False)
    farmer_email = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    market_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    quality = db.Column(db.String(50), nullable=False)
    expected_price = db.Column(db.Float, nullable=False)
    merchant_email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)

# Create tables
with app.app_context():
    db.create_all()

# Helper functions
def validate_email(email):
    """Validate email format."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_phone(phone):
    """Validate phone number format (10 digits)."""
    return re.match(r"^\d{10}$", phone)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/farmer-register', methods=['GET', 'POST'])
def farmer_register():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('farmer_register'))

        # Check if email already exists
        existing_farmer = Farmer.query.filter_by(email=email).first()
        if existing_farmer:
            flash('Email already registered!', 'error')
            return redirect(url_for('farmer_register'))

        # Hash the password
        hashed_password = generate_password_hash(password)  # Use default hashing method

        # Create new farmer
        new_farmer = Farmer(name=name, email=email, password=hashed_password)
        db.session.add(new_farmer)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('farmer_login'))

    return render_template('farmer_register.html')

@app.route('/farmer-login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        # Get form data
        email = request.form['email']
        password = request.form['password']

        # Check if farmer exists
        farmer = Farmer.query.filter_by(email=email).first()
        if farmer and check_password_hash(farmer.password, password):
            # Set session for logged-in farmer
            session['farmer_id'] = farmer.id
            session['farmer_email'] = farmer.email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash('Invalid email or password!', 'error')
            return redirect(url_for('farmer_login'))

    return render_template('farmer_login.html')

@app.route('/dashboard')
def dashboard():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('farmer_login'))

    return render_template('dashboard.html')

@app.route('/ask-ai')
def ask_ai():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the chatbot.', 'error')
        return redirect(url_for('farmer_login'))

    return render_template('ask-ai.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Get the user's message from the request
    user_message = request.json.get('message')

    try:
        # Send the user's message to the Gemini API
        response = model.generate_content(user_message)
        bot_response = response.text

        # Return the bot's response as JSON
        return jsonify({'response': bot_response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': 'Sorry, something went wrong. Please try again.'})

@app.route('/farmer-logout')
def farmer_logout():
    # Clear the session
    session.pop('farmer_id', None)
    session.pop('farmer_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/farmer-merchant')
def farmer_merchant():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the merchant place.', 'error')
        return redirect(url_for('farmer_login'))

    return render_template('farmer-merchant.html')

@app.route('/organic-form')
def organic_form():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the form.', 'error')
        return redirect(url_for('farmer_login'))

    return render_template('organic_form.html')

@app.route('/chemical-form')
def chemical_form():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the form.', 'error')
        return redirect(url_for('farmer_login'))

    return render_template('chemical_form.html')

@app.route('/submit-organic-form', methods=['POST'])
def submit_organic_form():
    try:
        # Get form data
        farmer_name = request.form['farmer_name']
        farmer_email = request.form['farmer_email']
        product_name = request.form['product_name']
        address = request.form['address']
        contact_number = request.form['contact_number']
        market_price = request.form['market_price']
        quantity = request.form['quantity']
        quality = request.form['quality']
        expected_price = request.form['expected_price']
        merchant_email = request.form['merchant_email']
        message = request.form['message']

        # Validate required fields
        if not all([farmer_name, farmer_email, product_name, address, contact_number, market_price, quantity, quality, expected_price, merchant_email]):
            flash('Please fill out all required fields.', 'error')
            return redirect(url_for('organic_form'))

        # Validate email and phone number
        if not validate_email(farmer_email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('organic_form'))

        if not validate_phone(contact_number):
            flash('Invalid phone number. Please enter a 10-digit number.', 'error')
            return redirect(url_for('organic_form'))

        # Save product to database
        new_product = Product(
            farmer_name=farmer_name,
            farmer_email=farmer_email,
            product_name=product_name,
            address=address,
            contact_number=contact_number,
            market_price=market_price,
            quantity=quantity,
            quality=quality,
            expected_price=expected_price,
            merchant_email=merchant_email,
            message=message
        )
        db.session.add(new_product)
        db.session.commit()

        # Create email content
        email_body = f"""
        Farmer Name: {farmer_name}
        Farmer Email: {farmer_email}
        Product Name: {product_name}
        Address: {address}
        Contact Number: {contact_number}
        Market Price: {market_price} per unit
        Quantity Available: {quantity}
        Quality / Grade: {quality}
        Expected Price per Unit: {expected_price}
        Additional Message: {message}
        """

        # Send email to the selected merchant
        msg = Message(
            subject="New Organic Product Sale Request",
            recipients=[merchant_email],
            body=email_body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)

        # Notify the farmer
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Error: {e}")
        flash('Sorry, something went wrong. Please try again.', 'error')
        return redirect(url_for('organic_form'))

@app.route('/submit-chemical-form', methods=['POST'])
def submit_chemical_form():
    try:
        # Get form data
        farmer_name = request.form['farmer_name']
        farmer_email = request.form['farmer_email']
        product_name = request.form['product_name']
        address = request.form['address']
        contact_number = request.form['contact_number']
        market_price = request.form['market_price']
        quantity = request.form['quantity']
        quality = request.form['quality']
        expected_price = request.form['expected_price']
        merchant_email = request.form['merchant_email']
        message = request.form['message']

        # Validate required fields
        if not all([farmer_name, farmer_email, product_name, address, contact_number, market_price, quantity, quality, expected_price, merchant_email]):
            flash('Please fill out all required fields.', 'error')
            return redirect(url_for('chemical_form'))

        # Validate email and phone number
        if not validate_email(farmer_email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('chemical_form'))

        if not validate_phone(contact_number):
            flash('Invalid phone number. Please enter a 10-digit number.', 'error')
            return redirect(url_for('chemical_form'))

        # Save product to database
        new_product = Product(
            farmer_name=farmer_name,
            farmer_email=farmer_email,
            product_name=product_name,
            address=address,
            contact_number=contact_number,
            market_price=market_price,
            quantity=quantity,
            quality=quality,
            expected_price=expected_price,
            merchant_email=merchant_email,
            message=message
        )
        db.session.add(new_product)
        db.session.commit()

        # Create email content
        email_body = f"""
        Farmer Name: {farmer_name}
        Farmer Email: {farmer_email}
        Product Name: {product_name}
        Address: {address}
        Contact Number: {contact_number}
        Market Price: {market_price} per unit
        Quantity Available: {quantity}
        Quality / Grade: {quality}
        Expected Price per Unit: {expected_price}
        Additional Message: {message}
        """

        # Send email to the selected merchant
        msg = Message(
            subject="New Normal Product Sale Request",
            recipients=[merchant_email],
            body=email_body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)

        # Notify the farmer
        flash('Your application has been submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Error: {e}")
        flash('Sorry, something went wrong. Please try again.', 'error')
        return redirect(url_for('chemical_form'))

# Disease Detection Route
@app.route('/disease-detection', methods=['GET', 'POST'])
def disease_detection():
    # Check if farmer is logged in
    if 'farmer_id' not in session:
        flash('Please log in to access the disease detection feature.', 'error')
        return redirect(url_for('farmer_login'))

    if request.method == 'POST':
        # Check if an image file was uploaded
        if 'file' not in request.files:
            flash('No file uploaded!', 'error')
            return redirect(url_for('disease_detection'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(url_for('disease_detection'))

        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Run the YOLOv8 model on the uploaded image
        try:
            results = yolo_model(file_path)
            print(f"Model results: {results}")  # Debugging statement
        except Exception as e:
            print(f"Error running YOLOv8 model: {e}")
            flash('Error processing the image. Please try again.', 'error')
            return redirect(url_for('disease_detection'))

        # Extract predictions
        predictions = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls)  # Class ID
                class_name = yolo_model.names[class_id]  # Class name
                confidence = float(box.conf)  # Confidence score
                predictions.append({
                    "class_name": class_name,
                    "confidence": confidence
                })
        print(f"Predictions: {predictions}")  # Debugging statement

        # Render the results on the disease detection page
        return render_template('disease_detection.html', predictions=predictions, image_path=filename)

    return render_template('disease_detection.html')

# Route for Organic Cultivation Guidance Page
@app.route('/organic-guidance')
def organic_guidance():
    return render_template('organic_guidance.html')

# Route for Crop Yield Optimization Page
@app.route('/yield-optimization')
def yield_optimization():
    return render_template('yield_optimization.html')

# Route to handle Organic Cultivation Guidance form submission
@app.route('/get-organic-guidance', methods=['POST'])
def get_organic_guidance():
    data = request.json
    crop = data.get('crop', 'unknown crop')

    try:
        # Generate organic cultivation guide using Gemini API
        prompt = f"""Provide a detailed step-by-step guide for organic cultivation of {crop}. Include the following:
        1. Soil Preparation: How to prepare the soil for {crop}.
        2. Seed Selection: How to choose the best seeds for {crop}.
        3. Planting: Step-by-step instructions for planting {crop}.
        4. Fertilization: Organic fertilizers and how to apply them for {crop}.
        5. Pest Control: Organic methods to control pests for {crop}.
        6. Harvesting: When and how to harvest {crop}.
        Provide clear and detailed instructions for each step. Use ** for headings and * for bullet points."""
        response = model.generate_content(prompt)
        guide = response.text
        return jsonify({'guide': guide})
    except Exception as e:
        print(f"Error generating organic guide: {e}")
        return jsonify({'guide': 'Sorry, something went wrong. Please try again.'})

@app.route('/get-yield-optimization', methods=['POST'])
def get_yield_optimization():
    data = request.json
    crop = data.get('crop', 'unknown crop')

    try:
        # Generate yield optimization guide using Gemini API
        prompt = f"""Provide a detailed guide to maximize the yield of {crop}. Include the following:
        1. Soil Health: How to test and improve soil health for {crop}.
        2. Irrigation: Best practices for watering {crop}.
        3. Pest Management: Organic and sustainable methods to control pests for {crop}.
        4. Harvesting: Optimal harvesting techniques for {crop}.
        5. Post-Harvest Care: How to store and handle {crop} after harvesting.
        Provide clear and detailed instructions for each step. Use ** for headings and * for bullet points."""
        response = model.generate_content(prompt)
        guide = response.text
        return jsonify({'guide': guide})
    except Exception as e:
        print(f"Error generating yield optimization guide: {e}")
        return jsonify({'guide': 'Sorry, something went wrong. Please try again.'})

# Route to handle Disease Solution request
@app.route('/get-disease-solution', methods=['POST'])
def get_disease_solution():
    data = request.json
    disease = data.get('disease', 'unknown disease')

    try:
        # Generate disease solution using Gemini API
        prompt = f"""Provide a detailed solution for managing and treating {disease} in crops. Include the following:
        1. Symptoms: Key symptoms of {disease}.
        2. Causes: Common causes of {disease}.
        3. Prevention: Methods to prevent {disease}.
        4. Treatment: Effective treatments for {disease}.
        5. Organic Remedies: Organic methods to control {disease}.
        Provide clear and detailed instructions for each step."""
        response = model.generate_content(prompt)
        solution = response.text
        return jsonify({'solution': solution})
    except Exception as e:
        print(f"Error generating disease solution: {e}")
        return jsonify({'solution': 'Sorry, something went wrong. Please try again.'})

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)