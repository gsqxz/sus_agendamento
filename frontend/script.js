const API_URL = 'http://127.0.0.1:5000'; // Altere para a URL da nuvem no futuro

// Máscara simples para CPF
document.getElementById('cpf').addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    e.target.value = value;
});

// Envio do formulário
document.getElementById('form-agendamento').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const dados = {
        cpf: document.getElementById('cpf').value,
        local: document.getElementById('local').value,
        especialidade: document.getElementById('especialidade').value,
        data: document.getElementById('data').value,
        horario: document.getElementById('horario').value
    };

    try {
        const response = await fetch(`${API_URL}/agendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        
        if (response.ok) {
            alert('Consulta agendada com sucesso!');
            document.getElementById('form-agendamento').reset();
        } else {
            alert('Erro ao agendar consulta. Verifique os dados.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão com o servidor.');
    }
});

// Busca de agendamentos por CPF
async function buscarAgendamentos() {
    const cpf = document.getElementById('cpf-busca').value;
    if (!cpf) return alert("Digite um CPF.");

    try {
        const response = await fetch(`${API_URL}/agendamentos/${cpf}`);
        const dados = await response.json();
        
        const lista = document.getElementById('lista-agendamentos');
        lista.innerHTML = '';

        if (dados.length === 0) {
            lista.innerHTML = '<p>Nenhum agendamento encontrado.</p>';
            return;
        }

        dados.forEach(agendamento => {
            lista.innerHTML += `
                <div class="agendamento-card">
                    <p><strong>Local:</strong> ${agendamento.local}</p>
                    <p><strong>Especialidade:</strong> ${agendamento.especialidade}</p>
                    <p><strong>Data/Hora:</strong> ${agendamento.data} às ${agendamento.horario}</p>
                    <button onclick="cancelarAgendamento(${agendamento.id})" style="background-color: #dc3545; margin-top: 10px;">Cancelar / Liberar Vaga</button>
                </div>
            `;
        });
    } catch (error) {
        alert('Erro ao buscar agendamentos.');
    }
}

async function cancelarAgendamento(id) {
    if(confirm("Deseja realmente cancelar esta consulta?")) {
        await fetch(`${API_URL}/agendamentos/${id}`, { method: 'DELETE' });
        buscarAgendamentos(); // Recarrega a lista
    }
}