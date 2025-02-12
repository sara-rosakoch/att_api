from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration (Ensure PostgreSQL credentials are correct)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ladyb:newpassword@localhost:5432/att"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define Users Model
class Users(db.Model):
    __tablename__ = "users"  # Renamed from 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Users {self.user_id}>"

# Define Templates Model
class Templates(db.Model):
    __tablename__ = "templates"  # Stores fingerprint templates

    template_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey("users.user_id"), nullable=False)
    template_data = db.Column(db.Text, nullable=False)  # Base64 encoded fingerprint
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Templates {self.template_id}>"

# Apply Changes to the Database
with app.app_context():
    db.create_all()

# Home Route
@app.route('/')
def home():
    return "Welcome to the User API!"

# Route to Get All Users
@app.route('/users', methods=['GET'])
def get_users():
    users = Users.query.all()
    result = [{
        "id": user.id,
        "user_id": user.user_id,
        "name": user.name,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for user in users]
    return jsonify(result)

# Route to Get Fingerprint Templates for Multiple Users
@app.route('/get-template', methods=['GET'])
def get_templates():
    user_ids = request.args.getlist('user_id')  # Get multiple user IDs from query params

    if not user_ids:
        return jsonify({"message": "Please provide at least one user_id"}), 400

    templates = Templates.query.filter(Templates.user_id.in_(user_ids)).all()
    
    result = [{
        "template_id": template.template_id,
        "user_id": template.user_id,
        "template_data": template.template_data
    } for template in templates]

    return jsonify(result)

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
