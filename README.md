# CertidaoGuaru

Protótipo em Python para organizar consultas e downloads de certidões em portais públicos. O projeto possui uma interface Streamlit, execução por linha de comando e módulos separados por fonte.

## Situação do projeto

Os portais automatizados mudam com frequência. Cada módulo precisa ser validado no momento do uso e pode exigir intervenção manual, especialmente quando houver CAPTCHA, autenticação ou alteração de formulário. O projeto não promete emissão automática, disponibilidade contínua nem resultado jurídico.

## Estrutura

- `interface.py`: interface local em Streamlit;
- `main.py`: orquestração por linha de comando;
- `modules/`: adaptadores experimentais por portal;
- `utils/captcha_solver.py`: tentativa local de OCR para imagens simples.

## Tecnologias

- Python;
- Playwright;
- Streamlit;
- Pillow e `ddddocr`;
- Pandas.

## Instalação

```bash
python -m venv .venv
```

No Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m streamlit run interface.py
```

## Uso responsável

Use somente com autorização e para finalidades legítimas. Respeite limites de acesso, termos de uso e mecanismos de proteção dos portais. CAPTCHAs não devem ser tratados como uma garantia de automação: quando o portal exigir interação humana, o fluxo deve parar para conferência. Certidões e dados pessoais devem ser protegidos e revisados na fonte oficial.
