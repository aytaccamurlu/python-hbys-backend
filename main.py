from bson import ObjectId
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import jwt
import datetime
import os

app = Flask(__name__)

# En geniş kapsamlı CORS ayarı (PUT ve DELETE dahil)
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "supports_credentials": True
}})

SECRET_KEY = "gizli_anahtar_123"
MONGO_URI = "mongodb+srv://aytaccamurlu26_db_user:3HwWLyyOSY1Stvaj@cluster0.vg96nxd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client.hastane_db

# --- KULLANICI ROTALARI ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if db.users.find_one({"username": data.get('username')}):
        return jsonify({"error": "Bu kullanıcı zaten mevcut"}), 400
    
    hashed_password = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt())
    db.users.insert_one({
        "username": data.get('username'),
        "password": hashed_password,
        "role": data.get('role', 'user')
    })
    return jsonify({"message": "Kayıt başarılı"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = db.users.find_one({"username": data.get('username')})
    if user and bcrypt.checkpw(data.get('password').encode('utf-8'), user['password']):
        token = jwt.encode({
            'user': user['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token, "username": user['username']}), 200
    return jsonify({"error": "Hatalı giriş"}), 401

# --- HASTA ROTALARI ---

@app.route('/api/patients', methods=['GET'])
def get_patients():
    patients = list(db.patients.find())
    for p in patients:
        p['_id'] = str(p['_id'])
    return jsonify(patients), 200

@app.route('/api/patients', methods=['POST'])
def add_patient():
    data = request.json
    result = db.patients.insert_one({
        "name": data.get('name'),
        "surname": data.get('surname'),
        "tc_no": data.get('tc_no'),
        "phone": data.get('phone')
    })
    return jsonify({"message": "Hasta eklendi", "id": str(result.inserted_id)}), 201

@app.route('/api/patients/<id>', methods=['DELETE', 'OPTIONS'])
def delete_patient(id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Gelen ID'nin geçerli bir ObjectId olup olmadığını kontrol et
        if not ObjectId.is_valid(id):
            return jsonify({"error": "Geçersiz ID formatı"}), 400
            
        result = db.patients.delete_one({"_id": ObjectId(id)})
        
        if result.deleted_count > 0:
            return jsonify({"message": "Hasta başarıyla silindi"}), 200
        else:
            return jsonify({"error": "Hasta bulunamadı"}), 404
    except Exception as e:
        print(f"Silme Hatası: {str(e)}") # Terminalde hatayı görmek için
        return jsonify({"error": str(e)}), 500  
if __name__ == "__main__":
      print("--- Flask Sunucusu Başlatılıyor ---")
      app.run(host='0.0.0.0', port=5000, debug=True)
