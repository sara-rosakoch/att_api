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

# Get Users by Tags
@app.route('/get-users-by-tags', methods=['POST'])
def get_users_by_tags():
    data = request.get_json()
    
    if not data or 'tags' not in data:
        return jsonify({"message": "Tags are required"}), 400
    
    tags = data['tags']
    users = Users.query.filter(Users.tags.op("?") (tags)).all()
    
    result = [{"user_id": user.user_id, "name": user.name, "tags": user.tags} for user in users]
    
    return jsonify({"users": result}), 200

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
