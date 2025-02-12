from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ladyb:newpassword@localhost:5432/att"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define Users Model
class Users(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.JSON, default=[])
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<User {self.user_id}>"

# Define Attendance Model
class Attendance(db.Model):
    __tablename__ = "attendance"
    
    attendance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Define Devices Model
class Devices(db.Model):
    __tablename__ = "devices"
    
    device_id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Apply Changes to the Database
with app.app_context():
    db.create_all()


# Mark Attendance Route
@app.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    
    if not data or 'pd' not in data or 'user_ids' not in data['pd'] or 'timestamps' not in data['pd']:
        return jsonify({"message": "Invalid payload structure"}), 400
    
    user_ids = data['pd']['user_ids']
    timestamps = data['pd']['timestamps']
    
    if len(user_ids) != len(timestamps):
        return jsonify({"message": "User IDs and timestamps must have the same length"}), 400
    
    attendance_records = []
    for user_id, timestamp in zip(user_ids, timestamps):
        user = Users.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"message": f"User {user_id} not found"}), 404
        
        attendance = Attendance(user_id=user_id, timestamp=datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ"))
        db.session.add(attendance)
        attendance_records.append({"user_id": user_id, "attendance_id": attendance.attendance_id, "timestamp": timestamp})
    
    db.session.commit()
    
    return jsonify({"message": "Attendance marked successfully", "records": attendance_records}), 200

# Get Users by Tags (Changed to GET)
@app.route('/get-users-by-tags', methods=['GET'])
def get_users_by_tags():
    tags = request.args.getlist('tags')  # Get tags from query parameters

    if not tags:
        return jsonify({"message": "Tags are required"}), 400
    
    users = Users.query.filter(Users.tags.op("?")(tags)).all()
    
    result = [{"user_id": user.user_id, "name": user.name, "tags": user.tags} for user in users]
    
    return jsonify({"users": result}), 200

# Get Attendance Data (Changed to GET)
@app.route('/get-attendance', methods=['GET'])
def get_attendance():
    user_ids = request.args.getlist('user_ids')  # Get list of user IDs from query
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not user_ids or not start_time or not end_time:
        return jsonify({"message": "user_ids, start_time, and end_time are required"}), 400

    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")

    attendance_data = []
    for user_id in user_ids:
        attendance_records = Attendance.query.filter(
            Attendance.user_id == user_id,
            Attendance.timestamp >= start_time,
            Attendance.timestamp <= end_time
        ).all()
        
        timestamps = [record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") for record in attendance_records]
        attendance_data.append({"user_id": user_id, "timestamps": timestamps})

    return jsonify({"attendance": attendance_data}), 200

# Get Fingerprint Templates (New GET Endpoint)
@app.route('/get-template', methods=['GET'])
def get_template():
    user_ids = request.args.getlist('user_ids')  # Get list of user IDs from query

    if not user_ids:
        return jsonify({"message": "user_ids are required"}), 400

    # Simulating retrieval of fingerprint templates (replace with actual implementation)
    templates = [{"user_id": user_id, "template": f"fingerprint_data_for_{user_id}"} for user_id in user_ids]
    
    return jsonify({"templates": templates}), 200
# Enroll User with Fingerprint Template
@app.route('/enroll-user', methods=['POST'])
def enroll_user():
    data = request.get_json()

    if not data or 'user_id' not in data or 'name' not in data or 'fingerprint_template' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    user_id = data['user_id']
    name = data['name']
    tags = data.get('tags', [])  # Optional field
    fingerprint_template = data['fingerprint_template']

    # Check if user already exists
    existing_user = Users.query.filter_by(user_id=user_id).first()
    if existing_user:
        return jsonify({"message": f"User {user_id} already exists"}), 400

    # Create new user
    new_user = Users(user_id=user_id, name=name, tags=tags)
    db.session.add(new_user)
    db.session.commit()

    # Store fingerprint template (Modify based on actual fingerprint storage method)
    # For now, we just simulate storing it.
    fingerprint_data = {user_id: fingerprint_template}  # In reality, use a proper database table.

    return jsonify({
        "message": "User enrolled successfully",
        "user": {
            "user_id": user_id,
            "name": name,
            "tags": tags
        }
    }), 201


# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
