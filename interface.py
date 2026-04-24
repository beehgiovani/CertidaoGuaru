import streamlit as st
import pandas as pd
import json
import time
import os
import sys
import subprocess
from main import process_request # Mantido para batch (tab2)

st.set_page_config(
    page_title="Emissor de Certidões Automático",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .stButton>button:hover {
        border-color: #1e88e5;
        color: #1e88e5;
    }
    .log-box {
        height: 400px;
        overflow-y: scroll;
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 14px;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #ddd;
        white-space: pre-wrap;
        box-shadow: inset 0 0 5px rgba(0,0,0,0.05);
    }
    .status-active {
        color: #e67e22;
        font-weight: bold;
    }
    .status-done {
        color: #27ae60;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">⚖️ Emissor de Certidões Automático</h1>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Configurações")
st.sidebar.info("Este sistema utiliza automação de navegador (Playwright) e OCR local. O robô roda em segundo plano para garantir estabilidade.")

if st.sidebar.button("🧹 Limpar Estado / Destravar", help="Use isso se a interface parecer travada ou confusa"):
    st.session_state.pid = None
    st.session_state.processed_results = {}
    st.session_state.generated_files = []
    st.rerun()

# Inicializa estado
if 'processed_results' not in st.session_state:
    st.session_state.processed_results = {}
if 'generated_files' not in st.session_state:
    st.session_state.generated_files = []
if 'pid' not in st.session_state:
    st.session_state.pid = None

# Tabs
tab1, tab2 = st.tabs(["📄 Emissão Individual", "📁 Emissão em Lote (JSON)"])

def check_pid(pid):
    """Verifica se o processo ainda está rodando"""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Dados do Pesquisado")
        cpf_cnpj = st.text_input("CPF ou CNPJ (apenas números)", max_chars=18, help="Ex: 123.456.789-00")
        cpf_clean = "".join([c for c in cpf_cnpj if c.isdigit()])
        
        nome = st.text_input("Nome Completo / Razão Social")
        rg = st.text_input("RG (Opcional - Exigido p/ TJSP)")
        genero = st.selectbox("Gênero (Opcional - Exigido p/ TJSP)", ["Masculino", "Feminino"])
        data_nasc = st.text_input("Data de Nascimento", help="DD/MM/AAAA")
        email = st.text_input("E-mail (Opcional)")
        
        st.subheader("Certidões Desejadas")
        bots_available = {
            "TSTBot": "TST - Débitos Trabalhistas (CNDT)",
            "TRT2Bot": "TRT2 - Trabalhista (PJe e Físico)",
            "TJSPBot": "TJSP - Cível/Criminal",
            "TRF3Bot": "TRF3 - Regional",
            "ReceitaBot": "Receita Federal (Situação Cadastral)",
            "CJFBot": "CJF - Unificada"
        }
        
        selected_bots = []
        for bot_id, bot_label in bots_available.items():
            if st.checkbox(bot_label, value=True):
                selected_bots.append(bot_id)
        
        headless_mode = st.checkbox("Modo Invisível (Headless)", value=True)
        
        # Botão Iniciar (Desabilitado se já rodando)
        is_running = st.session_state.pid is not None and check_pid(st.session_state.pid)
        start_btn = st.button("🚀 Iniciar Emissão", disabled=is_running)

    with col2:
        st.subheader("Console de Execução")
        
        # Container de logs
        log_container = st.empty()
        
        # Lógica de Inicialização
        if start_btn:
            if not cpf_cnpj or not nome:
                st.error("Preencha CPF e Nome!")
            else:
                user_data = {
                    'cpf_cnpj': cpf_cnpj, 'cpf': cpf_clean, 'nome': nome,
                    'rg': rg, 'genero': genero, 'data_nascimento': data_nasc, 'email': email
                }
                
                # Salva tarefa
                task_data = {"user_data": user_data, "selected_bots": selected_bots, "headless": headless_mode}
                with open("temp_task.json", "w") as f:
                    json.dump(task_data, f)
                
                # Limpa logs antigos
                with open("output.log", "w") as f: f.write("Iniciando processo...\n")
                if os.path.exists("output/captcha_request.json"): os.remove("output/captcha_request.json")
                if os.path.exists("output/process_results.json"): os.remove("output/process_results.json")

                # Inicia Subprocesso
                log_file = open("output.log", "a")
                proc = subprocess.Popen(
                    [sys.executable, "-u", "main.py", "--input-json", "temp_task.json"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
                st.session_state.pid = proc.pid
                st.rerun()

        # Lógica de Monitoramento (Estado Ativo)
        if st.session_state.pid:
            if check_pid(st.session_state.pid):
                st.markdown('<p class="status-active">🔄 Robô em execução...</p>', unsafe_allow_html=True)
                
                # Ler e Mostrar Logs
                if os.path.exists("output.log"):
                    with open("output.log", "r") as f:
                        logs = f.read()
                        log_container.markdown(f'<div class="log-box">{logs[-3000:]}</div>', unsafe_allow_html=True)

                # Checar Captcha
                req_file = "output/captcha_request.json"
                if os.path.exists(req_file):
                    st.warning("⚠️ **ATENÇÃO:** O Robô precisa que você resolva um Captcha!")
                    try:
                        with open(req_file, 'r') as f:
                            req = json.load(f)
                        
                        st.image(req['image_path'], caption="Digite os caracteres da imagem")
                        
                        # Form para não recarregar a página a cada tecla
                        with st.form(key="captcha_form"):
                            captcha_code = st.text_input("Código do Captcha:")
                            submit_captcha = st.form_submit_button("Enviar Captcha")
                        
                        if submit_captcha and captcha_code:
                            with open("output/captcha_response.json", "w") as f:
                                json.dump({"text": captcha_code}, f)
                            st.success("Enviado! Aguarde o robô processar...")
                            os.remove(req_file) # Limpa para evitar duplo processamento visual
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao ler pedido de captcha: {e}")
                
                else:
                    # Se não tem captcha, auto-refresh para ver logs
                    time.sleep(2)
                    st.rerun()
            
            else:
                # Processo terminou (PID não existe mais)
                st.session_state.pid = None
                st.success("🏁 Processamento Finalizado!")
                
                # Carregar logs finais
                if os.path.exists("output.log"):
                    with open("output.log", "r") as f:
                        logs = f.read()
                        log_container.markdown(f'<div class="log-box">{logs[-3000:]}</div>', unsafe_allow_html=True)

                # Carregar Resultados JSON
                if os.path.exists("output/process_results.json"):
                    try:
                        with open("output/process_results.json", "r") as f:
                            st.session_state.processed_results = json.load(f)
                    except:
                        st.error("Erro ao ler arquivo de resultados.")
                
                # Listar Arquivos
                output_dir = "output"
                if os.path.exists(output_dir):
                    st.session_state.generated_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf") or f.endswith(".png")]
                
                st.rerun() # Refresh final para mostrar resultados limpos

        # Exibição de Resultados (Persistente)
        if st.session_state.processed_results:
            st.write("---")
            st.subheader("📊 Relatório Final")
            
            # Resultados por Bot
            for bot_name, status_msg in st.session_state.processed_results.items():
                if "Sucesso" in status_msg:
                    st.success(f"**{bot_name}**: {status_msg}")
                elif "Atenção" in status_msg:
                    st.warning(f"**{bot_name}**: {status_msg}")
                else:
                    st.error(f"**{bot_name}**: {status_msg}")

            # Downloads
            if st.session_state.generated_files:
                st.write("### 📂 Arquivos para Download")
                for f in st.session_state.generated_files:
                     path = os.path.join("output", f)
                     with open(path, "rb") as file:
                        st.download_button(f"⬇️ {f}", file.read(), file_name=f, mime="application/octet-stream")

# Mantido Tab2 simples (síncrona para simplificar)
with tab2:
    st.header("Emissão em Lote (JSON)")
    uploaded_file = st.file_uploader("Arquivo JSON", type=["json"])
    if uploaded_file:
        data = json.load(uploaded_file)
        if st.button("Processar Lote"):
            st.info("Processando lote de forma sequencial... (Logs no terminal)")
            results = []
            progress = st.progress(0)
            for i, item in enumerate(data):
                res = process_request(item, ['TSTBot', 'TRT2Bot'], log_callback=lambda x: None)
                item['resultado'] = res
                results.append(item)
                progress.progress((i+1)/len(data))
            st.success("Concluído!")
            st.json(results)
