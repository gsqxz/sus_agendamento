from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Configurando o Flask para procurar o Front-end nas pastas corretas
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configuração de conexão com o MySQL
# Nota: Quando subir para nuvem, substitua o host, user e password pelas credenciais do seu banco online
def conectar_banco():
    try:
        conexao = mysql.connector.connect(
            host='localhost',
            database='sus_agendamentos',
            user='root',         
            password='admin123'  
        )
        return conexao
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

# Rotas do Front-end (Entregam as telas do site)
@app.route('/')
def pagina_inicial():
    return render_template('index.html')

@app.route('/admin')
def pagina_admin():
    return render_template('admin.html')

# Rotas da API (Back-end)
@app.route('/login', methods=['POST'])
def login_admin():
    dados = request.json
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT id FROM admin WHERE usuario = %s AND senha = %s", (dados['usuario'], dados['senha']))
            usuario = cursor.fetchone()
            if usuario:
                return jsonify({"mensagem": "Login aprovado"}), 200
            else:
                return jsonify({"erro": "Credenciais inválidas"}), 401
        finally:
            cursor.close()
            conexao.close()
    return jsonify({"erro": "Erro no banco"}), 500

@app.route('/agendar', methods=['POST'])
def agendar_consulta():
    dados = request.json
    conexao = conectar_banco()
    
    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            
            data_hora_consulta = datetime.strptime(f"{dados['data']} {dados['horario']}", '%Y-%m-%d %H:%M')
            if data_hora_consulta < datetime.now():
                return jsonify({"erro": "Não é possível agendar em datas ou horários passados."}), 400

            query_conflito = """SELECT id FROM agendamentos 
                                WHERE local = %s AND especialidade = %s 
                                AND data_consulta = %s AND horario = %s AND status = 'Ativo'"""
            cursor.execute(query_conflito, (dados['local'], dados['especialidade'], dados['data'], dados['horario']))
            
            if cursor.fetchone():
                return jsonify({"erro": "Este horário já está ocupado para esta especialidade nesta unidade."}), 409

            query_inserir = """INSERT INTO agendamentos (cpf, local, especialidade, data_consulta, horario) 
                               VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(query_inserir, (dados['cpf'], dados['local'], dados['especialidade'], dados['data'], dados['horario']))
            conexao.commit()
            
            novo_id = cursor.lastrowid
            return jsonify({"mensagem": "Agendamento criado com sucesso", "id": novo_id}), 201
            
        except Error as e:
            return jsonify({"erro": str(e)}), 500
        finally:
            cursor.close()
            conexao.close()
            
    return jsonify({"erro": "Falha na conexão com o banco"}), 500

@app.route('/agendamentos/<cpf>', methods=['GET'])
def buscar_por_cpf(cpf):
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            query = "SELECT * FROM agendamentos WHERE cpf = %s AND status = 'Ativo'"
            cursor.execute(query, (cpf,))
            resultados = cursor.fetchall()
            
            for linha in resultados:
                linha['data_consulta'] = linha['data_consulta'].strftime('%Y-%m-%d')
                linha['horario'] = str(linha['horario'])
                
            return jsonify(resultados), 200
        finally:
            cursor.close()
            conexao.close()
    return jsonify({"erro": "Falha na conexão"}), 500

@app.route('/agendamentos/<int:id_agendamento>', methods=['DELETE'])
def cancelar_agendamento(id_agendamento):
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "UPDATE agendamentos SET status = 'Cancelado' WHERE id = %s"
            cursor.execute(query, (id_agendamento,))
            conexao.commit()
            
            if cursor.rowcount > 0:
                return jsonify({"mensagem": "Agendamento cancelado com sucesso"}), 200
            else:
                return jsonify({"erro": "Agendamento não encontrado"}), 404
        finally:
            cursor.close()
            conexao.close()
    return jsonify({"erro": "Falha na conexão"}), 500

@app.route('/admin/todos', methods=['GET'])
def listar_todos():
    conexao = conectar_banco()
    if conexao:
        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM agendamentos ORDER BY data_consulta DESC, horario DESC")
            resultados = cursor.fetchall()
            
            for linha in resultados:
                linha['data_consulta'] = linha['data_consulta'].strftime('%Y-%m-%d')
                linha['horario'] = str(linha['horario'])
                linha['criado_em'] = linha['criado_em'].strftime('%Y-%m-%d %H:%M:%S')
                
            return jsonify(resultados), 200
        finally:
            cursor.close()
            conexao.close()
    return jsonify({"erro": "Falha na conexão"}), 500

if __name__ == '__main__':
    app.run(debug=True)