from flask import Flask, render_template, request, session, flash, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, logout_user, login_manager, LoginManager, login_required, current_user
from datetime import datetime
from flask_mail import Mail
import json
import pickle
import numpy as np
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'super-secret-key'

# Load configuration from JSON
config_path = os.path.join(os.path.dirname(__file__), "config.json")  # Ensure correct path
try:
    with open(config_path, "r") as f:
        config = json.load(f)
        params = config['params']
except FileNotFoundError:
    print("Error: 'config.json' file not found. Please ensure it's in the correct directory.")
    exit(1)
except json.JSONDecodeError:
    print("Error: 'config.json' is not properly formatted.")
    exit(1)



# Configure Mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params.get('gmail-user', ''),
    MAIL_PASSWORD=params.get('gmail-password', '')
)
mail = Mail(app)

# Determine whether to use local or production settings for the database
if params.get('local_server', False):
    app.config['SQLALCHEMY_DATABASE_URI'] = params.get('local_uri', '')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params.get('prod_uri', '')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define the database model

class Addagroproducts(db.Model):
    username=db.Column(db.String(50))
    email=db.Column(db.String(50))
    contact_num=db.Column(db.String(20))
    farmadd=db.Column(db.String(300))
    pid=db.Column(db.Integer,primary_key=True)
    productname=db.Column(db.String(100))
    productdesc=db.Column(db.String(300))
    price=db.Column(db.Integer)
    unit=db.Column(db.String(20)) 

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))

# Routes

@app.route("/")
def home():
    return render_template('index.html')


@app.route('/mlmodel', methods=['GET', 'POST'])
def mlmodel():
    if request.method == 'POST':
        try:
            # Get user input values from the form
            temperature = float(request.form['temperature'])
            humidity = float(request.form['humidity'])
            ph = float(request.form['ph'])
            rainfall = float(request.form['rainfall'])

            # Check for invalid conditions
            if (
                temperature > 55 or humidity > 100 or ph > 9 or rainfall > 3000 or
                temperature < 0 or humidity < 0 or ph < 0 or rainfall < 0
            ):
                flash("Invalid input! Ensure values are within range: Temperature (0-55°C), Humidity (0-100%), pH (0-9), Rainfall (0-3000mm).", "danger")
                return redirect(url_for('mlmodel'))

            # Prepare the input data for prediction
            input_data = np.array([[temperature, humidity, ph, rainfall]])

            # Predict the crop and treatment plan using the models
            predicted_crop = model_crop.predict(input_data)[0]
            predicted_treatment = model_treatment.predict(input_data)[0]

            # Split treatment into readable format
            treatment_parts = predicted_treatment.split('###')
            treatment_details = "\n".join(treatment_parts).strip()

            # Render the prediction result
            return render_template(
                'mlmodel.html',
                crop=predicted_crop,
                treatment=treatment_details
            )

        except Exception as e:
            return jsonify({'error': str(e)})

    return render_template('mlmodel.html')


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Send mail
        mail.send_message(
            'New message from ' + name,
            sender=email,
            recipients=[params.get('gmail-user', '')],
            body=message + "\n" + phone
        )
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# Route to add a new agro product
@app.route('/addagroproduct', methods=['GET', 'POST'])
@login_required
def addagroproduct():
    if request.method == 'POST':
        # Get form data
        username = current_user.username
        email = request.form.get('email')
        contact_num = request.form.get('contact_num')
        farmadd = request.form.get('farmadd')
        productname = request.form.get('productname')
        productdesc = request.form.get('productdesc')
        price = request.form.get('price')
        unit = request.form.get('unit')

        # Add the product to the database
        product = Addagroproducts(
            username=username,
            email=email,
            contact_num=contact_num,
            farmadd=farmadd,
            productname=productname,
            productdesc=productdesc,
            price=price,
            unit=unit
        )
        try:
            db.session.add(product)
            db.session.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for('agroproducts'))
        except:
            db.session.rollback()
            flash("Error adding product. Please try again.", "danger")

    return render_template('addagroproducts.html')   
    # If user is not logged in, show flash message and redirect to login page
    flash("Please log in to add a product", "warning")
    return redirect(url_for('login'))

@app.route('/my_products')
@login_required
def my_products():
    products = Addagroproducts.query.filter_by(username=current_user.username).all()
    return render_template('my_products.html', products=products)

# Route to edit a product
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Addagroproducts.query.get_or_404(product_id)
    if product.username != current_user.username:
        flash("You are not authorized to edit this product.", "danger")
        return redirect(url_for('my_products'))

    if request.method == 'POST':
        product.productname = request.form.get('productname')
        product.productdesc = request.form.get('productdesc')
        product.price = request.form.get('price')
        product.contact_num = request.form.get('contact_num')
        product.farmadd = request.form.get('farmadd')
        product.unit = request.form.get('unit')
        try:
            db.session.commit()
            flash("Product updated successfully!", "success")
            return redirect(url_for('my_products'))
        except:
            db.session.rollback()
            flash("Error updating product. Please try again.", "danger")
    
    return render_template('edit_product.html', product=product)

# Route to delete a product
@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Addagroproducts.query.get_or_404(product_id)
    if product.username != current_user.username:
        flash("You are not authorized to delete this product.", "danger")
        return redirect(url_for('my_products'))

    try:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully!", "success")
    except:
        db.session.rollback()
        flash("Error deleting product. Please try again.", "danger")

    return redirect(url_for('my_products'))

@app.route('/agroproduct')
def agroproducts():
    # query=db.engine.execute(f"SELECT * FROM `addagroproducts`") 
    query=Addagroproducts.query.all()
    return render_template('agroproducts.html',query=query)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        # Hash password and save new user
        encpassword = generate_password_hash(password)
        new_user = User(username=username, email=email, password=encpassword)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Signup Success! Please Login", "success")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user from database
        user = User.query.filter_by(email=email).first()

        # Check password
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful", "primary")
            return redirect(url_for('home'))
        else:
            flash("Invalid Credentials", "warning")
            return render_template('index.html')  # Ensure this is the login template
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful", "warning")
    return redirect(url_for('login'))

@app.route('/change_user_credentials', methods=['GET', 'POST'])
@login_required
def change_user_credentials():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        # Update username and/or password
        current_user.username = new_username or current_user.username
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Credentials updated successfully!", "success")
        return redirect(url_for('home'))

    return render_template('change_user_credentials.html')




if __name__ == "__main__":
    app.run(host='localhost', port=5004, debug=True)
