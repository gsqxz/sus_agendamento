from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

# Configuração de conexão com o MySQL
def conectar_banco():
    try:
        conexao = mysql.connector.connect(
            host='localhost',
            database='sus_agendamentos',
            user='root',         # Substitua pelo seu usuário do MySQL
            password=''          # Substitua pela sua senha do MySQL
        )
        return conexao
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

@app.route('/agendar', methods=['POST'])
def agendar_consulta():
    dados = request.json
    conexao = conectar_banco()
    
    if conexao:
        try:
            cursor = conexao.cursor()
            query = """INSERT INTO agendamentos (cpf, local, especialidade, data_consulta, horario) 
                       VALUES (%s, %s, %s, %s, %s)"""
            valores = (dados['cpf'], dados['local'], dados['especialidade'], dados['data'], dados['horario'])
            cursor.execute(query, valores)
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
            # Retorna apenas os agendamentos ativos
            query = "SELECT * FROM agendamentos WHERE cpf = %s AND status = 'Ativo'"
            cursor.execute(query, (cpf,))
            resultados = cursor.fetchall()
            
            # Formatação de datas e horários (timedelta) para formato legível no JSON
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
            # Atualiza o status em vez de excluir a linha, mantendo o histórico
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
            cursor.execute("SELECT * FROM agendamentos")
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