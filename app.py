from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
import os
import logging

# Inicializar o app Flask
app = Flask(__name__)

# Habilitar CORS para permitir que o frontend (React Native) faça requisições
CORS(app)

# Configurar o logger
logging.basicConfig(level=logging.INFO)


MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['washup']

# Coleção de usuários
users_collection = db['users']

# Rota de teste para verificar se o servidor está online
@app.route('/')
def home():
    logging.info("Rota '/' acessada. Servidor está rodando.")
    return "API WashUp rodando com MongoDB Atlas!"

@app.route('/teste')
def teste():
    logging.info("Rota '/' acessada. Servidor está rodando.")
    return "Teste"

# Rota para criar um novo usuário (POST)
@app.route('/register', methods=['POST'])
def register_user():
    logging.info("Rota '/register' acessada.")
    data = request.get_json()

    # Logar os dados recebidos
    logging.info(f"Dados recebidos: {data}")

    # Verificar se todos os campos obrigatórios estão presentes
    if not all(key in data for key in ('name', 'email', 'cpf', 'phone', 'password')):
        logging.warning("Dados obrigatórios ausentes.")
        return jsonify({"error": "Dados obrigatórios ausentes"}), 400

    # Verificar se o email já está registrado
    if users_collection.find_one({"email": data['email']}):
        logging.warning(f"E-mail já registrado: {data['email']}")
        return jsonify({"error": "E-mail já registrado"}), 400

    try:
        # Inserir o novo usuário no MongoDB
        user_id = users_collection.insert_one({
            "name": data['name'],
            "email": data['email'],
            "password": data['password'],  # Você pode adicionar hash de senha aqui para segurança
            "cpf": data['cpf'],
            "phone": data['phone']
        }).inserted_id

        # Logar o sucesso da criação do usuário
        logging.info(f"Usuário criado com sucesso. ID: {user_id}")

        # Retornar a resposta com o ID do novo usuário
        return jsonify({"message": "Usuário registrado com sucesso", "user_id": str(user_id)}), 201

    except Exception as e:
        logging.error(f"Erro ao registrar o usuário: {e}")
        return jsonify({"error": "Erro ao registrar o usuário"}), 500

# Rota para listar todos os usuários (GET)
@app.route('/users', methods=['GET'])
def get_users():
    logging.info("Rota '/users' acessada.")
    
    try:
        users = list(users_collection.find())
        for user in users:
            user['_id'] = str(user['_id'])  # Converter ObjectId para string

        logging.info(f"Total de usuários encontrados: {len(users)}")
        return jsonify(users), 200

    except Exception as e:
        logging.error(f"Erro ao buscar os usuários: {e}")
        return jsonify({"error": "Erro ao buscar os usuários"}), 500

if __name__ == '__main__':
    # O Flask rodará no host 0.0.0.0 e usará a porta definida pelo Render
    logging.info("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))