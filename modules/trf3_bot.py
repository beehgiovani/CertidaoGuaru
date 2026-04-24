from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

class TRF3Bot(BaseBot):
    def run(self, data):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get('headless', True), 
                args=[
                    '--disable-http2', 
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--window-position=0,0'
                ]
            )
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True
            )
            
            # Stealth
            page = context.new_page()
            if stealth_sync:
                stealth_sync(page)
            
            print("Acessando TRF3...")
            try:
                # Timeout maior
                page.goto("https://web.trf3.jus.br/certidao-regional/CertidaoCivelEleitoralCriminal/SolicitarDadosCertidao", timeout=90000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Erro ao carregar página TRF3: {e}")
                browser.close()
                return {"status": "error", "message": f"Erro Conexão TRF3: {e}", "files": []}
            
            # Selecionar Tipo de Certidão
            try:
                page.wait_for_selector("select[id='Tipo']", timeout=30000)
                page.select_option("select[id='Tipo']", value="CIVEL") 
            except:
                print("TRF3: Falha ao carregar formulário.")
            
            # Selecionar Tipo de Documento
            page.select_option("select[id='TipoDeDocumento']", value="CPF")
            
            time.sleep(1)

            # Preencher Dados
            cpf_limpo = data['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '')
            page.fill("input[id='Documento']", cpf_limpo)
            page.fill("input[id='Nome']", data['nome'])
            
            try:
                page.select_option("select[id='TipoDeAbrangencia']", value="TRF")
            except:
                pass

            # Configurar download handler
            self.setup_download_handler(page, "TRF3", data)

            # Resolver Captcha (reCAPTCHA v2)
            print("Verificando reCAPTCHA TRF3...")
            try:
                recaptcha_frame = page.frame_locator("iframe[title*='reCAPTCHA']").first
                if recaptcha_frame.is_visible():
                    print("reCAPTCHA detectado. Tentando clique inicial...")
                    recaptcha_frame.locator(".recaptcha-checkbox-border").click(timeout=5000)
                    time.sleep(2)
            except:
                pass

            # Clicar em "Emitir certidão"
            # Clicar em "Emitir certidão"
            print("Clicando em Emitir...")
            try:
                # Tenta esperar botão ficar clicável
                page.wait_for_selector("a[id='submit'], button:has-text('Emitir')", timeout=10000)
                # Retry click loop
                for i in range(3):
                    try:
                        page.click("a[id='submit'], button:has-text('Emitir')", timeout=3000)
                        break
                    except:
                        page.click("text=Emitir certidão", force=True)
                        time.sleep(1)
            except Exception as e:
                print(f"Erro ao clicar Emitir TRF3: {e}")

            # Aguardar processamento/Download
            if self.wait_for_downloads(timeout=30):
                 print("TRF3: Download confirmado.")
                 browser.close()
                 return {
                     "status": "success",
                     "message": "Certidão TRF3 emitida.",
                     "files": self.downloaded_files
                 }
            
            # Tentar verificar se houve mensagem de sucesso mas o download falhou
            if page.locator("text=Certidão emitida com sucesso").is_visible():
                 # Tenta achar link de download
                 try:
                     with page.expect_download(timeout=10000) as download_info:
                        page.click("a[href*='GerarCertidao']", force=True)
                     download = download_info.value
                     path = os.path.join(self.output_dir, f"TRF3_Manual_{int(time.time())}.pdf")
                     download.save_as(path)
                     browser.close()
                     return {"status": "success", "message": "TRF3 Baixado manual.", "files": [path]}
                 except: pass

            # Screenshot de falha
            sanitized_cpf = cpf_limpo
            screenshot_path = os.path.join(self.output_dir, f"TRF3_{sanitized_cpf}_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            browser.close()
            return {
                "status": "warning",
                "message": "TRF3 finalizado sem download. Verifique o print.",
                "files": [screenshot_path]
            }
