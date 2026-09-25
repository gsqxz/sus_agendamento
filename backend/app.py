from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Caminho absoluto para garantir que o arquivo banco.db seja criado na mesma pasta do app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'banco.db')

def conectar_banco():
    # check_same_thread=False é necessário para o Flask trabalhar bem com SQLite
    conexao = sqlite3.connect(DB_PATH, check_same_thread=False)
    conexao.row_factory = sqlite3.Row # Permite acessar as colunas pelo nome (como um dicionário)
    return conexao

def inicializar_banco():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    # Cria a tabela de ADMIN
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')
    
    # Cria a tabela de Agendamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT NOT NULL,
            local TEXT NOT NULL,
            especialidade TEXT NOT NULL,
            data_consulta TEXT NOT NULL,
            horario TEXT NOT NULL,
            status TEXT DEFAULT 'Ativo',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insere o usuário admin de teste se ele não existir
    cursor.execute("SELECT id FROM admin WHERE usuario = 'controlador_sus'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admin (usuario, senha) VALUES ('controlador_sus', 'admin123')")
        
    conexao.commit()
    conexao.close()

# Inicializa o banco assim que o script roda
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
    else:
        return jsonify({"erro": "Credenciais inválidas"}), 401

@app.route('/agendar', methods=['POST'])
def agendar_consulta():
    dados = request.json
    conexao = conectar_banco()
    cursor = conexao.cursor()
    
    try:
        # 1. Validação de Data/Hora passada
        data_hora_consulta = datetime.strptime(f"{dados['data']} {dados['horario']}", '%Y-%m-%d %H:%M')
        if data_hora_consulta < datetime.now():
            return jsonify({"erro": "Não é possível agendar em datas ou horários passados."}), 400

        # 2. Validação de Conflito (Duplo Agendamento)
        query_conflito = """SELECT id FROM agendamentos 
                            WHERE local = ? AND especialidade = ? 
                            AND data_consulta = ? AND horario = ? AND status = 'Ativo'"""
        cursor.execute(query_conflito, (dados['local'], dados['especialidade'], dados['data'], dados['horario']))
        
        if cursor.fetchone():
            return jsonify({"erro": "Este horário já está ocupado para esta especialidade nesta unidade."}), 409

        # 3. Inserção
        query_inserir = """INSERT INTO agendamentos (cpf, local, especialidade, data_consulta, horario) 
                           VALUES (?, ?, ?, ?, ?)"""
        cursor.execute(query_inserir, (dados['cpf'], dados['local'], dados['especialidade'], dados['data'], dados['horario']))
        conexao.commit()
        
        return jsonify({"mensagem": "Agendamento criado com sucesso", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        conexao.close()

@app.route('/agendamentos/<cpf>', methods=['GET'])
def buscar_por_cpf(cpf):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM agendamentos WHERE cpf = ? AND status = 'Ativo'", (cpf,))
    resultados = cursor.fetchall()
    conexao.close()
    
    # Converte os resultados para dicionário
    return jsonify([dict(linha) for linha in resultados]), 200

@app.route('/agendamentos/<int:id_agendamento>', methods=['DELETE'])
def cancelar_agendamento(id_agendamento):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("UPDATE agendamentos SET status = 'Cancelado' WHERE id = ?", (id_agendamento,))
    conexao.commit()
    linhas_afetadas = cursor.rowcount
    conexao.close()
    
    if linhas_afetadas > 0:
        return jsonify({"mensagem": "Agendamento cancelado com sucesso"}), 200
    else:
        return jsonify({"erro": "Agendamento não encontrado"}), 404

@app.route('/admin/todos', methods=['GET'])
def listar_todos():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM agendamentos ORDER BY data_consulta DESC, horario DESC")
    resultados = cursor.fetchall()
    conexao.close()
    
    return jsonify([dict(linha) for linha in resultados]), 200

if __name__ == '__main__':
    app.run(debug=True)