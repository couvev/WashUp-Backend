from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_cors import CORS
from flask_talisman import Talisman
import os
import logging
import bcrypt

# Inicializar o app Flask
app = Flask(__name__)

# Habilitar CORS para permitir que o frontend faça requisições
CORS(app)

# Aplicar segurança com Talisman (HTTPS, CSP, etc.)
Talisman(app)

# Configurar o logger
logging.basicConfig(level=logging.INFO)

# Obter a MONGO_URI do ambiente do Render
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logging.error("Erro: MONGO_URI não encontrada nas variáveis de ambiente.")
    exit(1)

# Conectar ao MongoDB Atlas
try:
    client = MongoClient(MONGO_URI)
    db = client['washup']  # Nome do banco de dados no MongoDB Atlas
    logging.info("Conexão com MongoDB Atlas realizada com sucesso.")
except Exception as e:
    logging.error(f"Erro ao conectar ao MongoDB: {e}")
    exit(1)

# Usar a coleção `user` para armazenar dados de usuários
users_collection = db['user']

# Tratamento de erro genérico
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro no servidor: {e}")
    return jsonify({"error": "Erro no servidor", "details": str(e)}), 500

# Rota de teste para verificar se o servidor está online
@app.route('/')
def home():
    logging.info("Rota '/' acessada. Servidor está rodando.")
    return "API WashUp rodando com MongoDB Atlas!"

# Rota para criar um novo usuário (POST)
@app.route('/register', methods=['POST'])
def register_user():
    logging.info("Rota '/register' acessada.")
    try:
        data = request.get_json()
        logging.info(f"Dados recebidos: {data}")

        # Verificar se os campos obrigatórios estão presentes
        if not all(key in data for key in ('name', 'email', 'cpf', 'phone', 'password')):
            logging.warning("Dados obrigatórios ausentes.")
            return jsonify({"error": "Dados obrigatórios ausentes"}), 400

        # Verificar se o email já está registrado
        if users_collection.find_one({"email": data['email']}):
            logging.warning(f"E-mail já registrado: {data['email']}")
            return jsonify({"error": "E-mail já registrado"}), 400

        # Gerar hash da senha
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        # Inserir o novo usuário no MongoDB
        user_id = users_collection.insert_one({
            "name": data['name'],
            "email": data['email'],
            "password": hashed_password,  # Senha com hash
            "cpf": data['cpf'],
            "phone": data['phone']
        }).inserted_id

        logging.info(f"Usuário criado com sucesso. ID: {user_id}")
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
    logging.info("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
