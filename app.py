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

# Rota de teste para verificar se o servidor está online
@app.route('/')
def home():
    return "API WashUp rodando com MongoDB Atlas!"

# Rota para criar um novo usuário (POST)
@app.route('/register', methods=['POST'])
def register_user():
    # Pegar os dados JSON enviados na requisição
    data = request.get_json()

    # Verificar se todos os campos obrigatórios estão presentes
    if not all(key in data for key in ('name', 'email', 'cpf', 'phone', 'password')):
        return jsonify({"error": "Dados obrigatórios ausentes"}), 400

    # Verificar se o email já está registrado
    if users_collection.find_one({"email": data['email']}):
        return jsonify({"error": "E-mail já registrado"}), 400

    # Inserir o novo usuário no MongoDB
    user_id = users_collection.insert_one({
        "name": data['name'],
        "email": data['email'],
        "password": data['password'],  # Você pode adicionar hash de senha aqui para segurança
        "cpf": data['cpf'],
        "phone": data['phone']
    }).inserted_id

    # Retornar a resposta com o ID do novo usuário
    return jsonify({"message": "Usuário registrado com sucesso", "user_id": str(user_id)}), 201

# Rota para listar todos os usuários (GET)
@app.route('/users', methods=['GET'])
def get_users():
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])  # Converter ObjectId para string

    return jsonify(users), 200

if __name__ == '__main__':
    # O Flask rodará no host 0.0.0.0 e usará a porta definida pelo Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))