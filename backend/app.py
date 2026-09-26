from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'banco.db')

def conectar_banco():
    conexao = sqlite3.connect(DB_PATH, check_same_thread=False)
    conexao.row_factory = sqlite3.Row 
    return conexao

def inicializar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT NOT NULL UNIQUE, senha TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (cpf TEXT PRIMARY KEY, nome TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, cpf TEXT NOT NULL, local TEXT NOT NULL, especialidade TEXT NOT NULL, data_consulta TEXT NOT NULL, horario TEXT NOT NULL, status TEXT DEFAULT 'Ativo', criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (cpf) REFERENCES pacientes(cpf))''')
    cursor.execute("SELECT id FROM admin WHERE usuario = 'controlador_sus'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admin (usuario, senha) VALUES ('controlador_sus', 'admin123')")
    conexao.commit()
    conexao.close()

inicializar_banco()

@app.route('/login', methods=['POST'])
def login_admin():
    dados = request.json
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM admin WHERE usuario = ? AND senha = ?", (dados['usuario'], dados['senha']))
    usuario = cursor.fetchone()
    conexao.close()
    if usuario:
        return jsonify({"mensagem": "Login aprovado"}), 200
    return jsonify({"erro": "Credenciais inválidas"}), 401

@app.route('/horarios-ocupados', methods=['GET'])
def horarios_ocupados():
    data = request.args.get('data')
    local = request.args.get('local')
    especialidade = request.args.get('especialidade')
    if not data or not local or not especialidade:
        return jsonify([]), 200
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""SELECT horario FROM agendamentos 
                      WHERE data_consulta = ? AND local = ? AND especialidade = ? AND status = 'Ativo'""", 
                   (data, local, especialidade))
    resultados = cursor.fetchall()
    conexao.close()
    return jsonify([linha['horario'] for linha in resultados]), 200

@app.route('/agendar', methods=['POST'])
def agendar_consulta():
    dados = request.json
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        cpf = dados['cpf']
        nome = dados['nome'].strip().upper()
        cursor.execute("SELECT nome FROM pacientes WHERE cpf = ?", (cpf,))
        paciente = cursor.fetchone()
        if paciente:
            if paciente['nome'] != nome:
                return jsonify({"erro": f"Este CPF já está cadastrado no sistema sob o nome de {paciente['nome']}."}), 400
        else:
            cursor.execute("INSERT INTO pacientes (cpf, nome) VALUES (?, ?)", (cpf, nome))

        data_hora_consulta = datetime.strptime(f"{dados['data']} {dados['horario']}", '%Y-%m-%d %H:%M')
        if data_hora_consulta < datetime.now():
            return jsonify({"erro": "Não é possível agendar em datas passadas."}), 400

        cursor.execute("""SELECT id FROM agendamentos 
                          WHERE local = ? AND especialidade = ? AND data_consulta = ? AND horario = ? AND status = 'Ativo'""", 
                       (dados['local'], dados['especialidade'], dados['data'], dados['horario']))
        if cursor.fetchone():
            return jsonify({"erro": "Este horário já está ocupado."}), 409

        cursor.execute("""INSERT INTO agendamentos (cpf, local, especialidade, data_consulta, horario) 
                          VALUES (?, ?, ?, ?, ?)""", 
                       (cpf, dados['local'], dados['especialidade'], dados['data'], dados['horario']))
        conexao.commit()
        return jsonify({"mensagem": "Agendamento criado com sucesso", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        conexao.close()

@app.route('/admin/agendamentos/<int:id_agendamento>/remarcar', methods=['PUT'])
def remarcar_agendamento(id_agendamento):
    dados = request.json
    conexao = conectar_banco()
    cursor = conexao.cursor()
    try:
        nova_data = dados['data']
        novo_horario = dados['horario']
        data_hora_consulta = datetime.strptime(f"{nova_data} {novo_horario}", '%Y-%m-%d %H:%M')
        if data_hora_consulta < datetime.now():
            return jsonify({"erro": "Não é possível remarcar para o passado."}), 400

        cursor.execute("SELECT local, especialidade FROM agendamentos WHERE id = ?", (id_agendamento,))
        agendamento = cursor.fetchone()
        if not agendamento:
            return jsonify({"erro": "Agendamento não encontrado."}), 404

        cursor.execute("""SELECT id FROM agendamentos 
                          WHERE local = ? AND especialidade = ? AND data_consulta = ? AND horario = ? AND status = 'Ativo' AND id != ?""", 
                       (agendamento['local'], agendamento['especialidade'], nova_data, novo_horario, id_agendamento))
        if cursor.fetchone():
            return jsonify({"erro": "O novo horário já está ocupado."}), 409

        cursor.execute("UPDATE agendamentos SET data_consulta = ?, horario = ?, status = 'Ativo' WHERE id = ?", 
                       (nova_data, novo_horario, id_agendamento))
        conexao.commit()
        return jsonify({"mensagem": "Agendamento remarcado com sucesso"}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        conexao.close()

@app.route('/agendamentos/<cpf>', methods=['GET'])
def buscar_por_cpf(cpf):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""SELECT a.*, p.nome FROM agendamentos a JOIN pacientes p ON a.cpf = p.cpf WHERE a.cpf = ? AND a.status = 'Ativo'""", (cpf,))
    resultados = cursor.fetchall()
    conexao.close()
    return jsonify([dict(linha) for linha in resultados]), 200

@app.route('/agendamentos/<int:id_agendamento>', methods=['DELETE'])
def cancelar_agendamento(id_agendamento):
    # SOFT DELETE: Apenas altera o status para Cancelado
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("UPDATE agendamentos SET status = 'Cancelado' WHERE id = ?", (id_agendamento,))
    conexao.commit()
    linhas = cursor.rowcount
    conexao.close()
    if linhas > 0:
        return jsonify({"mensagem": "Cancelado"}), 200
    return jsonify({"erro": "Não encontrado"}), 404

# NOVA ROTA: HARD DELETE (Apaga o registro permanentemente do banco de dados)
@app.route('/admin/agendamentos/<int:id_agendamento>/limpar', methods=['DELETE'])
def limpar_registro(id_agendamento):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    # Apenas permite apagar se já estiver com o status 'Cancelado' por segurança
    cursor.execute("DELETE FROM agendamentos WHERE id = ? AND status = 'Cancelado'", (id_agendamento,))
    conexao.commit()
    linhas = cursor.rowcount
    conexao.close()
    
    if linhas > 0:
        return jsonify({"mensagem": "Registro apagado definitivamente"}), 200
    return jsonify({"erro": "Registro não encontrado ou não está cancelado"}), 404

@app.route('/admin/todos', methods=['GET'])
def listar_todos():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("""SELECT a.*, p.nome FROM agendamentos a JOIN pacientes p ON a.cpf = p.cpf ORDER BY a.data_consulta DESC, a.horario DESC""")
    resultados = cursor.fetchall()
    conexao.close()
    return jsonify([dict(linha) for linha in resultados]), 200

if __name__ == '__main__':
    app.run(debug=True)