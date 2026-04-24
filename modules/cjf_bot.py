from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

class CJFBot(BaseBot):
    def run(self, data):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get('headless', True),
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--window-position=0,0'
                ]
            )
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Stealth
            page = context.new_page()
            if stealth_sync:
                stealth_sync(page)
            
            print("Acessando CJF...")
            try:
                page.goto("https://certidao-unificada.cjf.jus.br/#/solicitacao-certidao", timeout=60000, wait_until="domcontentloaded")
            except:
                page.reload(wait_until="domcontentloaded")

            # Aguardar carregamento (SPA)
            try:
                page.wait_for_selector("p-dropdown[formcontrolname='tipo']", timeout=30000)
                
                # Selecionar Tipo
                print("Selecionando tipo de certidão no CJF...")
                page.click("p-dropdown[formcontrolname='tipo']")
                time.sleep(1)
                
                # Clica na opção Cível
                try:
                    page.locator("p-dropdownitem li").filter(has_text="Cível").click(timeout=3000)
                except:
                    page.click("p-dropdownitem li >> nth=0")

                # Selecionar CPF
                page.click("p-radiobutton[value='CPF'] .p-radiobutton-box", force=True)
                time.sleep(1)

                # Preencher CPF
                page.fill("input[name='cpfCnpj']", data['cpf_cnpj'])
                
                # E-mails
                email = data.get('email') or "contato@exemplo.com"
                page.fill("input[formcontrolname='email']", email)
                page.fill("input[formcontrolname='emailConfirmacao']", email)

            except Exception as e:
                print(f"Erro na interação inicial CJF: {e}")

            # Configurar download handler
            self.setup_download_handler(page, "CJF", data)
            
            # Resolver Captcha
            print("Verificando reCAPTCHA CJF...")
            try:
                recaptcha_frame = page.frame_locator("iframe[title*='reCAPTCHA']").first
                if recaptcha_frame.is_visible():
                    recaptcha_frame.locator(".recaptcha-checkbox-border").click(timeout=5000)
                    time.sleep(2)
            except:
                pass

            # Clicar Solicitar
            # Clicar Solicitar
            print("Clicando em Solicitar...")
            try:
                page.wait_for_selector("button:has-text('Solicitar certidão')", timeout=10000)
                page.click("button:has-text('Solicitar certidão')", timeout=5000)
            except:
                print("Botão Solicitar não respondeu, tentando force click...")
                page.click("button:has-text('Solicitar certidão')", force=True)
            
            # Verificar sucesso na mensagem para evitar 'Warning' se o download demorar
            success_msg = False
            try:
                page.wait_for_selector("text=Certidão gerada com sucesso", timeout=10000)
                success_msg = True
            except: pass
            
            if self.wait_for_downloads(timeout=30):
                 browser.close()
                 return {
                     "status": "success",
                     "message": "Certidão CJF emitida com sucesso.",
                     "files": self.downloaded_files
                 }
            
            # Se não baixou via handler, mas deu sucesso, tenta achar link manual
            if success_msg:
                 print("Mensagem de sucesso detectada, procurando link manual...")
                 # Geralmente o CJF baixa automático, mas vamos prevenir
                 # Não há link explícito geralmente, mas se deu sucesso e não baixou, pode ser popup blocker
                 pass

            # Screenshot de falha
            sanitized_cpf = data['cpf_cnpj'].replace('.', '').replace('-', '')
            screenshot_path = os.path.join(self.output_dir, f"CJF_{sanitized_cpf}_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            browser.close()
            
            if success_msg:
                 # Se apareceu sucesso visualmente mas nosso handler falhou
                 return {
                     "status": "warning", 
                     "message": "CJF indicou sucesso mas arquivo não capturado. Verifique logs/pasta.", 
                     "files": [screenshot_path]
                 }

            return {
                "status": "warning",
                "message": "CJF finalizado sem download. Verifique o print.",
                "files": [screenshot_path]
            }
