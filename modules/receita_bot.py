from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

class ReceitaBot(BaseBot):
    def run(self, data):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get('headless', True),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certificate-errors',
                    '--disable-web-security'
                ]
            )
            # Use um contexto com viewport realista
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Aplica stealth se disponível
            page = context.new_page()
            if stealth_sync:
                stealth_sync(page)
            
            print("Acessando Receita Federal...")
            try:
                # Aumentando timeout e alterando wait condition
                page.goto("https://servicos.receita.fazenda.gov.br/servicos/cpf/consultasituacao/consultapublica.asp", wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"Erro ao acessar Receita Federal: {e}")
                # Tenta reload se falhar
                try:
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                except:
                    browser.close()
                    return {"status": "error", "message": f"Erro de conexão Receita: {e}", "files": []}
            
            # Preencher dados
            cpf_limpo = data['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '')
            
            try:
                page.wait_for_selector("input[id='txtCPF']", state='visible', timeout=15000)
                page.fill("input[id='txtCPF']", cpf_limpo)
                page.fill("input[id='txtDataNascimento']", data['data_nascimento'])
            except Exception as e:
                print(f"Erro ao preencher dados iniciais: {e}")
            print("Verificando hCaptcha (aguardando carregamento)...")
            try:
                # Aguarda iframe do hCaptcha
                page.wait_for_selector("iframe[title*='hCaptcha'], iframe[title*='vidget']", timeout=20000)
                
                # Checkbox
                frame = page.frame_locator("iframe[title*='hCaptcha'], iframe[title*='vidget']").first
                if frame.locator("#checkbox").is_visible():
                    print("Clicando no checkbox...")
                    frame.locator("#checkbox").click()
                    time.sleep(2) # Tempo para animação/verificação
                    
                    # Verifica se pediu desafio
                    if page.locator("iframe[title*='desafio hCaptcha']").is_visible():
                         print("Desafio visual detectado.")
            except Exception as e:
                print(f"Aviso hCaptcha: {e}")
                pass

            # Se estiver em modo não-headless, o usuário pode resolver.
            if not self.config.get('headless', True):
                print("MODO INTERATIVO: Por favor, resolva o hCaptcha no navegador.")
                # Aguarda até 90 segundos pela resolução manual
                try:
                    page.wait_for_selector("text=Comprovante de Situação Cadastral", timeout=90000)
                except:
                    pass
            else:
                 # Em headless, só podemos torcer ou esperar que o stealth tenha funcionado para não exibir captcha complexo
                 time.sleep(2)

            # Tentar clicar em Consultar
            try:
                if page.locator("input[id='id_submit']").is_visible():
                    page.click("input[id='id_submit']", timeout=5000)
                elif page.locator("input[value='Consultar']").is_visible():
                    page.click("input[value='Consultar']", timeout=5000)
            except:
                print("Não foi possível clicar no botão Consultar.")

            # Verificar resultado
            try:
                # Esperar resultado (página de comprovante)
                page.wait_for_selector("text=Comprovante de Situação Cadastral", timeout=30000)
                
                # Ocultar botão de imprimir para sair limpo no print
                page.evaluate("document.getElementById('imgPrintWrapper').style.display = 'none';") 
                
                # Salvar Screenshot do Comprovante
                sanitized_cpf = cpf_limpo
                screenshot_path = os.path.join(self.output_dir, f"RFB_SitCad_{sanitized_cpf}_{int(time.time())}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"Situação Cadastral salva em {screenshot_path}")
                
                browser.close()
                return {
                    "status": "success",
                    "message": "Consulta Receita realizada com sucesso.",
                    "files": [screenshot_path]
                }
                
            except Exception as e:
                print(f"Não foi possível obter o comprovante da Receita: {e}")
                
                # Salvar print do erro/captcha para diagnóstico
                sanitized_cpf = cpf_limpo
                error_screenshot = os.path.join(self.output_dir, f"RFB_Erro_{sanitized_cpf}_{int(time.time())}.png")
                page.screenshot(path=error_screenshot)
                
                browser.close()
                return {
                    "status": "warning",
                    "message": "Falha Receita (Possível bloqueio/Captcha). Tente modo não-headless.",
                    "files": [error_screenshot]
                }
