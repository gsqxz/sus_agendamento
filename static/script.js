// A API_URL agora é vazia, pois o front e o back estão no mesmo domínio
const API_URL = ''; 

function mascararCPF(evento) {
    let value = evento.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    evento.target.value = value;
}

document.getElementById('cpf').addEventListener('input', mascararCPF);
document.getElementById('cpf-busca').addEventListener('input', mascararCPF);

const dataInput = document.getElementById('data');
const hoje = new Date().toISOString().split('T')[0];
dataInput.setAttribute('min', hoje);

dataInput.addEventListener('change', gerarHorarios);

function gerarHorarios() {
    const selectHorario = document.getElementById('horario');
    selectHorario.innerHTML = '<option value="" disabled selected>Selecione...</option>';
    
    const dataSelecionada = document.getElementById('data').value;
    if (!dataSelecionada) return;

    const agora = new Date();
    const ehHoje = (dataSelecionada === hoje);

    for (let h = 8; h <= 16; h++) {
        if (h === 12) continue; 
        
        for (let m = 0; m < 60; m += 15) {
            let horaStr = h.toString().padStart(2, '0');
            let minStr = m.toString().padStart(2, '0');
            let horarioValor = `${horaStr}:${minStr}`;

            if (ehHoje) {
                let horaAtual = agora.getHours();
                let minAtual = agora.getMinutes();
                if (h < horaAtual || (h === horaAtual && m <= minAtual)) {
                    continue; 
                }
            }
            selectHorario.innerHTML += `<option value="${horarioValor}">${horarioValor}</option>`;
        }
    }
}

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
            document.getElementById('horario').innerHTML = '<option value="" disabled selected>Selecione a data primeiro...</option>';
        } else {
            const errorData = await response.json();
            alert(errorData.erro || 'Erro ao agendar consulta. Verifique os dados.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão com o servidor.');
    }
});

async function buscarAgendamentos() {
    const cpf = document.getElementById('cpf-busca').value;
    if (!cpf) return alert("Digite um CPF válido.");

    try {
        const response = await fetch(`${API_URL}/agendamentos/${cpf}`);
        const dados = await response.json();
        
        const lista = document.getElementById('lista-agendamentos');
        lista.innerHTML = '';

        if (dados.length === 0) {
            lista.innerHTML = '<p style="margin-top:15px; color: #555;">Nenhum agendamento ativo encontrado para este CPF.</p>';
            return;
        }

        dados.forEach(agendamento => {
            const horarioFormatado = agendamento.horario.substring(0, 5);
            const dataFormatada = agendamento.data_consulta.split('-').reverse().join('/');

            lista.innerHTML += `
                <div class="agendamento-card">
                    <p><strong>Local:</strong> ${agendamento.local}</p>
                    <p><strong>Especialidade:</strong> ${agendamento.especialidade}</p>
                    <p><strong>Data/Hora:</strong> ${dataFormatada} às ${horarioFormatado}</p>
                    <button onclick="cancelarAgendamento(${agendamento.id})" style="background-color: #dc3545; margin-top: 10px;">Cancelar / Liberar Vaga</button>
                </div>
            `;
        });
    } catch (error) {
        alert('Erro ao buscar agendamentos.');
    }
}

async function cancelarAgendamento(id) {
    if(confirm("Deseja realmente cancelar esta consulta? A vaga será liberada para outro paciente.")) {
        await fetch(`${API_URL}/agendamentos/${id}`, { method: 'DELETE' });
        buscarAgendamentos(); 
    }
}