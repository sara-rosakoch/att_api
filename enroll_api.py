from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from datetime import datetime

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ladyb:newpassword@localhost:5432/att"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.JSON, default=[])
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    fingerprint_template = db.Column(db.Text, nullable=False)  # Base64 encoded fingerprint template

    def __repr__(self):
        return f"<User {self.user_id}>"

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables: {e}")

@app.route('/')
def home():
    return "Welcome to the Fingerprint Enrollment API!"

# Enroll a user with fingerprint template data
@app.route('/enroll', methods=['POST'])
def enroll_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON body"}), 400

    device_id = data.get("id")
    timestamp = data.get("ts")
    payload = data.get("pd")
    signature = data.get("sig")

    if not payload or not all(k in payload for k in ("user_id", "template_data")):
        return jsonify({"message": "Invalid payload structure"}), 400

    user_id = payload["user_id"]
    template_data = payload["template_data"]

    if Users.query.filter_by(user_id=user_id).first():
        return jsonify({"message": "User ID already exists"}), 400

    new_user = Users(user_id=user_id, name="Unknown", fingerprint_template=template_data)
    db.session.add(new_user)
    db.session.commit()

    response = {
        "id": device_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        "res": {"status": "success"},
        "sig": "signature_placeholder"
    }
    return jsonify(response), 200

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
