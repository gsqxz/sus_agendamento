// const API_URL = 'https://gsqxz.pythonanywhere.com'; // <-- PRODUÇÃO (Comentado)
const API_URL = 'http://127.0.0.1:5000'; // ALERTA: Mude para produção quando for subir

// --- CONTROLE DOS ALERTAS ---
function mostrarAlerta(mensagem) {
    return new Promise((resolve) => {
        const modal = document.getElementById('alerta-modal');
        const overlay = document.getElementById('alerta-overlay');
        const texto = document.getElementById('alerta-mensagem');
        const btnOk = document.getElementById('btn-alerta-ok');

        texto.innerText = mensagem;
        overlay.style.display = 'block';
        modal.style.display = 'block';

        // Remove qualquer evento anterior para não duplicar cliques
        const novoBtnOk = btnOk.cloneNode(true);
        btnOk.parentNode.replaceChild(novoBtnOk, btnOk);

        novoBtnOk.addEventListener('click', () => {
            overlay.style.display = 'none';
            modal.style.display = 'none';
            resolve(); // Só agora o código continua e permite o reload/limpeza da página
        });
    });
}

function fecharAlerta() {
    document.getElementById('alerta-overlay').style.display = 'none';
    document.getElementById('alerta-modal').style.display = 'none';
}

function mostrarConfirm(mensagem) {
    return new Promise((resolve) => {
        document.getElementById('confirm-mensagem').innerText = mensagem;
        document.getElementById('confirm-overlay').style.display = 'block';
        document.getElementById('confirm-modal').style.display = 'block';

        const btnSim = document.getElementById('btn-confirm-sim');
        const btnNao = document.getElementById('btn-confirm-nao');

        btnSim.onclick = () => { fecharConfirm(); resolve(true); };
        btnNao.onclick = () => { fecharConfirm(); resolve(false); };
    });
}

function fecharConfirm() {
    document.getElementById('confirm-overlay').style.display = 'none';
    document.getElementById('confirm-modal').style.display = 'none';
}
// ---------------------------------------

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

document.getElementById('local').addEventListener('change', gerarHorarios);
document.getElementById('especialidade').addEventListener('change', gerarHorarios);
dataInput.addEventListener('change', gerarHorarios);

async function gerarHorarios() {
    const selectHorario = document.getElementById('horario');
    const localSelecionado = document.getElementById('local').value;
    const especialidadeSelecionada = document.getElementById('especialidade').value;
    const dataSelecionada = document.getElementById('data').value;

    if (!localSelecionado || !especialidadeSelecionada || !dataSelecionada) {
        selectHorario.innerHTML = '<option value="" disabled selected>Preencha Unidade, Especialidade e Data...</option>';
        return;
    }

    selectHorario.innerHTML = '<option value="" disabled selected>Buscando horários disponíveis...</option>';

    try {
        const res = await fetch(`${API_URL}/horarios-ocupados?data=${dataSelecionada}&local=${localSelecionado}&especialidade=${especialidadeSelecionada}`);
        const ocupados = await res.json();

        selectHorario.innerHTML = '<option value="" disabled selected>Selecione o horário...</option>';
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
                    if (h < horaAtual || (h === horaAtual && m <= minAtual)) continue; 
                }

                if (ocupados.includes(horarioValor)) {
                    selectHorario.innerHTML += `<option value="${horarioValor}" disabled style="color: red;">🚫 ${horarioValor} - Ocupado</option>`;
                } else {
                    selectHorario.innerHTML += `<option value="${horarioValor}">${horarioValor}</option>`;
                }
            }
        }
    } catch (error) {
        selectHorario.innerHTML = '<option value="" disabled selected>Erro ao carregar</option>';
    }
}

document.getElementById('form-agendamento').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const dados = {
        nome: document.getElementById('nome').value,
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
            await mostrarAlerta('Consulta agendada com sucesso!'); // AWAIT força a pausa
            document.getElementById('form-agendamento').reset();
            document.getElementById('horario').innerHTML = '<option value="" disabled selected>Preencha Unidade, Especialidade e Data...</option>';
        } else {
            const errorData = await response.json();
            await mostrarAlerta(errorData.erro || 'Erro ao agendar.');
        }
    } catch (error) { 
        await mostrarAlerta('Erro de conexão com o servidor.'); 
    }
});

async function buscarAgendamentos() {
    const cpf = document.getElementById('cpf-busca').value;
    if (!cpf) {
        await mostrarAlerta("Digite um CPF válido.");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/agendamentos/${cpf}`);
        const dados = await response.json();
        const lista = document.getElementById('lista-agendamentos');
        lista.innerHTML = '';

        if (dados.length === 0) {
            lista.innerHTML = '<p style="margin-top:15px; color: #555;">Nenhum agendamento ativo encontrado.</p>';
            return;
        }

        dados.forEach(a => {
            const horarioF = a.horario.substring(0, 5);
            const dataF = a.data_consulta.split('-').reverse().join('/');
            lista.innerHTML += `
                <div class="agendamento-card">
                    <p><strong>Paciente:</strong> ${a.nome}</p>
                    <p><strong>Local:</strong> ${a.local}</p>
                    <p><strong>Especialidade:</strong> ${a.especialidade}</p>
                    <p><strong>Data/Hora:</strong> ${dataF} às ${horarioF}</p>
                    <button type="button" onclick="cancelarAgendamento(${a.id})" style="background-color: #dc3545; margin-top: 10px;">Cancelar / Liberar Vaga</button>
                </div>
            `;
        });
    } catch (error) { 
        await mostrarAlerta('Erro ao buscar os agendamentos.'); 
    }
}

async function cancelarAgendamento(id) {
    const confirmou = await mostrarConfirm("Deseja realmente cancelar? A vaga será liberada.");
    
    if (confirmou) {
        try {
            await fetch(`${API_URL}/agendamentos/${id}`, { method: 'DELETE' });
            await mostrarAlerta("Consulta cancelada com sucesso."); // AWAIT aqui também
            buscarAgendamentos(); 
        } catch (error) {
            await mostrarAlerta("Erro ao cancelar.");
        }
    }
}