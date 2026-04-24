# Bot Automatizador de Certidões (100% Gratuito)

Este projeto consiste em um sistema de automação robusto para a emissão de certidões negativas em diversos portais judiciais e governamentais brasileiros. Construído com arquitetura modular, o robô opera com motores baseados em Chromium e possui um sistema local de resolução de CAPTCHAs via OCR (Optical Character Recognition), garantindo funcionamento 100% gratuito sem dependência de APIs externas de terceiros para contorno de desafios.

O sistema dispõe de uma interface gráfica interativa via Streamlit para emissão individual, bem como suporte à execução em lote via CLI (arquivos JSON), atendendo desde demandas pontuais até processos de alto volume.

## 🚀 Funcionalidades

- **Emissão Automatizada**: Navegação headless/stealth e submissão automatizada de formulários.
- **Resolução de CAPTCHA Local**: Integração com OCR offline (`ddddocr`) com pré-processamento de imagens para máxima precisão, sem custos por requisição.
- **Interface Gráfica e Modo Batch**: Opção de uso via Dashboard interativo (Streamlit) ou via linha de comando para processamento massivo.
- **Tratamento de Download Inteligente**: Espera assíncrona por downloads de PDFs e renomeação padronizada dos artefatos coletados.
- **Fallback Manual**: Sistema projetado com pausa seletiva para lidar com reCAPTCHA/hCaptcha em instâncias onde OCR simples não é aplicável.

## 🏢 Portais Suportados

A arquitetura modular facilita a inclusão de novos bots. Os módulos suportados atualmente incluem:
- **CJF** - Justiça Federal Unificada (Certidão Cível)
- **TRT2** - Trabalhista (PJe e Processos Físicos)
- **TST** - Débitos Trabalhistas (CNDT)
- **TRF3** - Certidão Regional
- **Receita Federal** - Comprovante de Situação Cadastral no CPF
- **TJSP** - e-SAJ (Certidão Cível/Criminal)

## 🛠 Tecnologias Utilizadas

- **Linguagem Principal**: Python 3.8+
- **Automação Web**: Playwright (`playwright-python`) e Stealth Plugins
- **Processamento de Imagens**: Pillow (PIL)
- **OCR e Quebra de CAPTCHAs**: `ddddocr`
- **Interface Gráfica**: Streamlit
- **Manipulação de Dados**: Pandas

## ⚙️ Instalação

### Pré-requisitos
- Python 3.8 ou superior instalado e configurado no PATH.

### Passos

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/certidao-automatizada.git
   cd certidao-automatizada
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Instale os navegadores do Playwright:
   ```bash
   playwright install chromium
   ```

## 🖥 Uso

Você pode utilizar o sistema de duas formas: através da interface gráfica amigável ou via terminal.

### 1. Interface Gráfica (Dashboard Streamlit)
Para iniciar a interface web, execute:
```bash
streamlit run interface.py
```
Isso abrirá uma janela no seu navegador com a tela "Emissor de Certidões Automático", onde você poderá inserir os dados do pesquisado, selecionar os portais desejados e acompanhar os logs em tempo real.

### 2. Linha de Comando (CLI - Modo Lote/Batch)
Ideal para integração com outros sistemas ou processamento massivo.

Exemplo de uso passando um JSON contendo a tarefa (você deve estruturar as configurações em um arquivo como `task.json`):
```bash
python main.py --input-json task.json --output-json output/process_results.json
```

O arquivo `task.json` deve conter os dados do usuário e os robôs a serem ativados:
```json
{
  "user_data": {
    "cpf_cnpj": "123.456.789-00",
    "cpf": "12345678900",
    "nome": "Nome do Pesquisado",
    "rg": "123456789",
    "genero": "Masculino",
    "data_nascimento": "01/01/1980",
    "email": "contato@exemplo.com"
  },
  "selected_bots": ["TSTBot", "TRT2Bot"],
  "headless": true
}
```

## 📂 Estrutura de Diretórios e Saída
Todas as certidões baixadas (PDFs) e comprovantes capturados (PNGs) são salvos por padrão no diretório local `output/`, seguindo o padrão de nomenclatura com o portal, documento e timestamp (ex: `TJSP_12345678900_1710000000.pdf`).

## ⚠️ Isenção de Responsabilidade
Esta ferramenta foi desenvolvida com o intuito de facilitar a automação de buscas públicas e de cunho burocrático. Recomenda-se usá-la em conformidade com as diretrizes de acesso, limites de taxa e termos de serviço de cada portal.

---
*Desenvolvido como projeto de portfólio.*
