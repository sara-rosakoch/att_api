from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import functools
import uuid

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

class Templates(db.Model):
    __tablename__ = "templates"
    template_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey("users.user_id"), nullable=False)
    template_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Templates {self.template_id}>"

class Attendance(db.Model):
    __tablename__ = "attendance"
    
    attendance_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Devices(db.Model):
    __tablename__ = "devices"
    
    device_id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

# Response Formatter Decorator
def format_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response_data, status_code = func(*args, **kwargs)
        formatted_response = {
            "id": str(uuid.uuid4()),
            "ts": datetime.utcnow().isoformat() + "Z",
            "res": response_data,
            "sig": "signature_placeholder"
        }
        return jsonify(formatted_response), status_code
    return wrapper

# Request Validator Decorator
def validate_request(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        if not data or not all(k in data for k in ["id", "ts", "pd", "sig"]):
            return {"message": "Invalid request format"}, 400
        return func(data["id"], data["ts"], data["pd"], data["sig"], *args, **kwargs)
    return wrapper

@app.route('/mark-attendance', methods=['POST'])
@validate_request
@format_response
def mark_attendance(req_id, ts, pd, sig):
    if "user_ids" not in pd or "timestamps" not in pd:
        return {"message": "Invalid payload structure"}, 400
    
    user_ids, timestamps = pd["user_ids"], pd["timestamps"]
    if len(user_ids) != len(timestamps):
        return {"message": "User IDs and timestamps must have the same length"}, 400
    
    attendance_records = []
    for user_id, timestamp in zip(user_ids, timestamps):
        if not Users.query.filter_by(user_id=user_id).first():
            return {"message": f"User {user_id} not found"}, 404
        
        db.session.add(Attendance(user_id=user_id, timestamp=datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")))
        attendance_records.append({"user_id": user_id, "timestamp": timestamp})
    
    db.session.commit()
    return {"message": "Attendance marked successfully", "records": attendance_records}, 200

@app.route('/get-users-by-tags', methods=['POST'])
@validate_request
@format_response
def get_users_by_tags(req_id, ts, pd, sig):
    tags = pd.get("tags", [])
    if not tags:
        return {"message": "Tags are required"}, 400
    
    users = Users.query.filter(Users.tags.op("@>")(db.cast(tags, JSONB))).all()
    return [{"user_id": u.user_id, "name": u.name, "tags": u.tags} for u in users] or {"message": "No users found"}, 200

@app.route('/get-attendance', methods=['POST'])
@validate_request
@format_response
def get_attendance(req_id, ts, pd, sig):
    user_ids, start_time, end_time = pd.get("user_ids"), pd.get("start_time"), pd.get("end_time")
    if not all([user_ids, start_time, end_time]):
        return {"message": "user_ids, start_time, and end_time are required"}, 400
    
    start_time, end_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ"), datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
    return {"attendance": [{"user_id": uid, "timestamps": [a.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") for a in Attendance.query.filter(Attendance.user_id == uid, Attendance.timestamp.between(start_time, end_time)).all()]} for uid in user_ids]}, 200

@app.route('/get-template', methods=['POST'])
@validate_request
@format_response
def get_template(req_id, ts, pd, sig):
    user_id = pd.get("user_id")
    if not user_id:
        return {"message": "User ID is required"}, 400  
    template = Templates.query.filter_by(user_id=user_id).first()
    return {"template": template.template_data} if template else {"message": "Template not found"}, 200

@app.route('/create-user', methods=['POST'])
@validate_request
@format_response
def create_user(req_id, ts, pd, sig):
    if "user_id" not in pd or "name" not in pd:
        return {"message": "Missing required fields"}, 400
    db.session.add(Users(user_id=pd["user_id"], name=pd["name"], tags=pd.get("tags", [])))
    db.session.commit()
    return {"message": "User created successfully"}, 201

@app.route('/enroll-user', methods=['POST'])
@validate_request
@format_response
def enroll_user(req_id, ts, pd, sig):
    if "user_id" not in pd or "template_data" not in pd:
        return {"message": "Missing required fields"}, 400
    if not Users.query.filter_by(user_id=pd["user_id"]).first():
        return {"message": "User not found"}, 404
    db.session.add(Templates(user_id=pd["user_id"], template_data=pd["template_data"]))
    db.session.commit()
    return {"message": "User enrolled successfully"}, 201

if __name__ == '__main__':
    app.run(debug=True)
