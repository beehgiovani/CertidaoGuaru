from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None

class TSTBot(BaseBot):
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
            page = context.new_page()
            
            # Stealth
            if stealth_sync:
                stealth_sync(page)
            
            print("Acessando TST...")
            try:
                # O TST redireciona para cndt-certidao.tst.jus.br
                page.goto("https://www.tst.jus.br/certidao", wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"Erro ao acessar TST: {e}")
                browser.close()
                return {"status": "error", "message": f"Erro Conexão TST: {e}", "files": []}

            # Aceitar cookies se o banner aparecer
            try:
                if page.locator("text=Aceitar").is_visible():
                    page.click("text=Aceitar", timeout=5000)
                    print("Cookies aceitos.")
            except:
                pass

            # Clicar em Emitir Certidão
            try:
                page.wait_for_selector("input[value='Emitir Certidão']", timeout=10000)
                page.click("input[value='Emitir Certidão']")
            except Exception as e:
                print(f"Erro ao clicar em Emitir Certidão: {e}")
                # Tenta fallback para o link direto se o botão falhar
                try:
                    page.goto("https://cndt-certidao.tst.jus.br/inicio.faces", timeout=45000)
                    page.wait_for_selector("input[value='Emitir Certidão']", timeout=10000)
                    page.click("input[value='Emitir Certidão']")
                except:
                    browser.close()
                    return {"status": "error", "message": "Botão Emitir Certidão não encontrado", "files": []}

            # Preencher CPF/CNPJ
            cpf_limpo = data['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '')
            try:
                page.wait_for_selector("input[id*='cpfCnpj']", timeout=10000)
                page.fill("input[id*='cpfCnpj']", cpf_limpo)
            except:
                print("Campo CPF não encontrado no TST.")
                browser.close()
                return {"status": "error", "message": "Campo CPF não encontrado", "files": []}

            # Resolver Captcha
            img_selector = "img[id*='captcha'], img[id*='idImgBase64']"
            input_selector = "input[id='idCampoResposta']"
            
            print("Tentando resolver captcha do TST (com pre-processamento)...")
            # Configura o handler de download antes de submeter
            self.setup_download_handler(page, "TST", data)
            
            # Callback para repreencher dados após reload
            def refill_action(p):
                try:
                    p.wait_for_selector("input[id*='cpfCnpj']", timeout=10000)
                    p.fill("input[id*='cpfCnpj']", cpf_limpo)
                    # Força clique em Emitir para garantir estado
                    # (Alguns sites exigem clique antes de mostrar captcha, mas TST mostra direto geralmente.
                    #  Por precaução, apenas preenchemos CPF que é o essencial)
                except Exception as e:
                    print(f"Erro ao repreencher TST: {e}")

            # Tenta resolver até 10x
            if self.handle_image_captcha(page, img_selector, input_selector, submit_selector="input[id*='btnEmitirCertidao']", max_attempts=10, min_length=6, reload_action_callback=refill_action):
                # Aguardar download
                if self.wait_for_downloads(timeout=30):
                    browser.close()
                    return {
                        "status": "success",
                        "message": "Certidão TST emitida com sucesso.",
                        "files": self.downloaded_files
                    }
            
            # Se falhar ou não baixar
            sanitized_cpf = data['cpf_cnpj'].replace('.', '').replace('-', '')
            screenshot_path = os.path.join(self.output_dir, f"TST_{sanitized_cpf}_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            browser.close()
            return {
                "status": "warning",
                "message": "TST finalizado sem download detectado. Verifique o print.",
                "files": [screenshot_path]
            }
