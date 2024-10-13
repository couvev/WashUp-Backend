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

# Usar as coleções para armazenar dados de usuários e lava jatos
users_collection = db['user']
car_washes_collection = db['car_washes']
bookings_collection = db['bookings']

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

# Rota para login (POST)
@app.route('/login', methods=['POST'])
def login_user():
    logging.info("Rota '/login' acessada.")
    try:
        data = request.get_json()
        logging.info(f"Dados recebidos: {data}")

        # Verificar se os campos obrigatórios estão presentes
        if not all(key in data for key in ('email', 'password')):
            logging.warning("Dados obrigatórios ausentes.")
            return jsonify({"error": "Por favor, preencha todos os campos."}), 400

        # Verificar se o usuário existe
        user = users_collection.find_one({"email": data['email']})
        if not user:
            logging.warning("E-mail não encontrado.")
            return jsonify({"error": "E-mail não encontrado. Verifique o e-mail informado."}), 404

        # Verificar a senha
        if bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            logging.info("Login bem-sucedido.")
            return jsonify({"status": "success", "message": "Login bem-sucedido!"}), 200
        else:
            logging.warning("Senha incorreta.")
            return jsonify({"error": "Senha incorreta. Verifique a senha e tente novamente."}), 401

    except Exception as e:
        logging.error(f"Erro ao fazer login: {e}")
        return jsonify({"error": "Erro ao fazer login"}), 500

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

# Rota para cadastrar lava jatos (POST)
@app.route('/car_washes/register', methods=['POST'])
def register_car_wash():
    logging.info("Rota '/car_washes/register' acessada.")
    try:
        data = request.get_json()
        logging.info(f"Dados recebidos: {data}")

        # Verificar se os campos obrigatórios estão presentes
        required_fields = ['name', 'address', 'phone', 'average_price', 'working_hours', 'description', 'services']
        if not all(field in data for field in required_fields):
            logging.warning("Dados obrigatórios ausentes.")
            return jsonify({"error": "Dados obrigatórios ausentes"}), 400

        # Inserir o lava jato no MongoDB
        car_wash_id = car_washes_collection.insert_one({
            "name": data['name'],
            "address": data['address'],
            "phone": data['phone'],
            "average_price": data['average_price'],
            "working_hours": data['working_hours'],
            "description": data['description'],
            "services": data['services']  # Serviços oferecidos pelo lava jato
        }).inserted_id

        logging.info(f"Lava jato registrado com sucesso. ID: {car_wash_id}")
        return jsonify({"message": "Lava jato registrado com sucesso", "car_wash_id": str(car_wash_id)}), 201

    except Exception as e:
        logging.error(f"Erro ao registrar lava jato: {e}")
        return jsonify({"error": "Erro ao registrar lava jato"}), 500

@app.route('/car_washes/<car_wash_id>', methods=['GET'])
def get_car_wash_details(car_wash_id):
    try:
        car_wash = car_washes_collection.find_one({"_id": ObjectId(car_wash_id)})
        if car_wash:
            car_wash['_id'] = str(car_wash['_id'])  # Converter ObjectId para string
            return jsonify(car_wash), 200
        else:
            return jsonify({"error": "Lava jato não encontrado"}), 404
    except Exception as e:
        logging.error(f"Erro ao buscar lava jato: {e}")
        return jsonify({"error": "Erro ao buscar lava jato"}), 500


# Rota para obter horários disponíveis (GET)
@app.route('/bookings/available', methods=['GET'])
def get_available_slots():
    logging.info("Rota '/bookings/available' acessada.")
    try:
        car_wash_id = request.args.get('car_wash_id')
        date = request.args.get('date')

        # Verificar se os parâmetros obrigatórios foram fornecidos
        if not car_wash_id or not date:
            logging.warning("Parâmetros obrigatórios ausentes.")
            return jsonify({"error": "Parâmetros obrigatórios ausentes"}), 400

        # Buscar os horários disponíveis para o lava jato e data fornecidos
        booking = bookings_collection.find_one({"car_wash_id": ObjectId(car_wash_id), "date": date})

        if not booking:
            logging.info("Nenhum horário disponível para esta data.")
            return jsonify({"available_slots": []}), 200

        logging.info(f"Horários disponíveis encontrados: {booking['available_slots']}")
        return jsonify({"available_slots": booking['available_slots']}), 200

    except Exception as e:
        logging.error(f"Erro ao buscar horários disponíveis: {e}")
        return jsonify({"error": "Erro ao buscar horários disponíveis"}), 500


# Rota para agendar um horário (POST)
@app.route('/bookings', methods=['POST'])
def book_slot():
    logging.info("Rota '/bookings' acessada.")
    try:
        data = request.get_json()

        # Verificar se os campos obrigatórios estão presentes
        required_fields = ['car_wash_id', 'date', 'time', 'service', 'user_id']
        if not all(field in data for field in required_fields):
            logging.warning("Dados obrigatórios ausentes.")
            return jsonify({"error": "Dados obrigatórios ausentes"}), 400

        # Verificar se o horário está disponível
        booking = bookings_collection.find_one({"car_wash_id": ObjectId(data['car_wash_id']), "date": data['date']})
        if not booking:
            logging.warning("Nenhum horário disponível para esta data.")
            return jsonify({"error": "Nenhum horário disponível para esta data."}), 400

        # Verificar o status do horário selecionado
        for slot in booking['available_slots']:
            if slot['time'] == data['time']:
                if slot['status'] == 'booked':
                    logging.warning("Horário já reservado.")
                    return jsonify({"error": "Horário já reservado."}), 400
                else:
                    slot['status'] = 'booked'
                    slot['user_id'] = ObjectId(data['user_id'])
                    slot['service'] = data['service']
                    break

        # Atualizar o horário no banco de dados
        bookings_collection.update_one({"_id": booking['_id']}, {"$set": {"available_slots": booking['available_slots']}})
        logging.info("Horário reservado com sucesso.")
        return jsonify({"message": "Horário reservado com sucesso."}), 200

    except Exception as e:
        logging.error(f"Erro ao reservar horário: {e}")
        return jsonify({"error": "Erro ao reservar horário"}), 500

# Rota para cancelar uma reserva (DELETE)
@app.route('/bookings/<booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    logging.info(f"Rota '/bookings/{booking_id}' acessada para cancelamento.")
    try:
        # Cancelar o agendamento e liberar o horário
        result = bookings_collection.update_one(
            {"available_slots._id": ObjectId(booking_id)},
            {"$set": {"available_slots.$.status": "available", "available_slots.$.user_id": None, "available_slots.$.service": None}}
        )

        if result.modified_count == 0:
            logging.warning("Horário não encontrado para cancelamento.")
            return jsonify({"error": "Horário não encontrado para cancelamento."}), 404

        logging.info("Reserva cancelada com sucesso.")
        return jsonify({"message": "Reserva cancelada com sucesso."}), 200

    except Exception as e:
        logging.error(f"Erro ao cancelar reserva: {e}")
        return jsonify({"error": "Erro ao cancelar reserva"}), 500
    
# Rota para listar lava jatos (GET)
@app.route('/car_washes', methods=['GET'])
def get_car_washes():
    logging.info("Rota '/car_washes' acessada.")
    try:
        # Buscar todos os lava jatos no MongoDB
        car_washes = list(car_washes_collection.find())

        # Converter ObjectId para string antes de retornar
        for car_wash in car_washes:
            car_wash['_id'] = str(car_wash['_id'])

        logging.info(f"Total de lava jatos encontrados: {len(car_washes)}")
        return jsonify(car_washes), 200

    except Exception as e:
        logging.error(f"Erro ao buscar lava jatos: {e}")
        return jsonify({"error": "Erro ao buscar lava jatos"}), 500

    
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erro no servidor: {e}")
    return jsonify({"error": "Erro no servidor", "details": str(e)}), 500


if __name__ == '__main__':
    logging.info("Iniciando o servidor Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
