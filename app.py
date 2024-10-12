from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir requisições de outros domínios

# Conexão com o MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['washup']

# Coleção de usuários
users_collection = db['users']

# Rota de teste
@app.route('/')
def home():
    return "API WashUp rodando com MongoDB Atlas!"

# Rota para criar um novo usuário
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    # Verificar se os campos obrigatórios estão presentes
    if 'name' not in data or 'email' not in data or 'cpf' not in data or 'phone' not in data:
        return jsonify({"error": "Dados obrigatórios ausentes"}), 400

    # Inserir o usuário no MongoDB
    user_id = users_collection.insert_one({
        "name": data['name'],
        "email": data['email'],
        "password": data['password'],  # Melhorar com hash de senha depois
        "cpf": data['cpf'],
        "phone": data['phone']
    }).inserted_id

    return jsonify({"message": "Usuário registrado com sucesso", "user_id": str(user_id)}), 201

# Rota para listar todos os usuários
@app.route('/users', methods=['GET'])
def get_users():
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])  # Converter ObjectId para string

    return jsonify(users), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

