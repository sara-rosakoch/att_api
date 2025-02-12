from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

# Database Configuration (Ensure PostgreSQL credentials are correct)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ladyb:newpassword@localhost:5432/att"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define User Model
class User(db.Model):
    __tablename__ = "user"  # Explicitly define table name

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)  # Ensure it exists
    name = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.JSON, default=[])  # JSONB format for PostgreSQL
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    fingerprint_template = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<User {self.user_id}>"

# Apply Changes to the Database
with app.app_context():
    db.create_all()

    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables: {e}")

# Home Route
@app.route('/')
def home():
    return "Welcome to the User API!"

# Route to Create a New User
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400
    
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({"message": "Username and email are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    new_user = User(username=username, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "created_at": new_user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }}), 201

# Route to Get All Users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = [{
        "id": user.id, 
        "username": user.username, 
        "email": user.email, 
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for user in users]
    return jsonify(result)

# Route to Get a Specific User by ID
@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({
        "id": user.id, 
        "username": user.username, 
        "email": user.email, 
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

# Route to Update a User by ID
@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400

    if 'username' in data:
        if User.query.filter(User.username == data['username'], User.id != id).first():
            return jsonify({"message": "Username already exists"}), 400
        user.username = data['username']

    if 'email' in data:
        if User.query.filter(User.email == data['email'], User.id != id).first():
            return jsonify({"message": "Email already exists"}), 400
        user.email = data['email']

    db.session.commit()
    return jsonify({"message": "User updated successfully", "user": {
        "id": user.id, 
        "username": user.username, 
        "email": user.email,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }})

# Route to Delete a User by ID
@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"})

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
