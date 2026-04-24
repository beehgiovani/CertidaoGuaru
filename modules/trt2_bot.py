from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright

class TRT2Bot(BaseBot):
    def run(self, data):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get('headless', True),
                args=['--disable-blink-features=AutomationControlled']
            )
            # TRT2 é fresco com user agent às vezes
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Configurar download handler
            self.setup_download_handler(page, "TRT2", data)
            
            files_found = 0

            # Link 1: PJe TRT2
            print("Acessando PJe TRT2...")
            try:
                page.goto("https://pje.trt2.jus.br/certidoes/trabalhista/emissao", wait_until="domcontentloaded", timeout=45000)
                
                # Selecionar CPF
                print("Selecionando tipo CPF no PJe...")
                try:
                    page.click("text=CPF", timeout=5000)
                    time.sleep(1)
                except:
                    pass

                # Preencher CPF
                cpf_limpo = data['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '')
                try:
                    page.fill("input[id='numeroDocumento'], input[name='numeroDocumento']", cpf_limpo, timeout=5000)
                except:
                    # Fallback para input visível
                    page.fill("input[type='text']:visible", cpf_limpo)

                # Verificar reCAPTCHA
                print("Verificando reCAPTCHA no PJe...")
                try:
                    recaptcha_frame = page.frame_locator("iframe[title*='reCAPTCHA']").first
                    if recaptcha_frame.is_visible():
                        recaptcha_frame.locator(".recaptcha-checkbox-border").click(timeout=5000)
                        time.sleep(2)
                except:
                    pass

                # Clicar em Emitir
                try:
                    page.click("button:has-text('Emitir')", timeout=5000)
                except:
                    pass
                
                # Espera breve por download do PJe
                start_wait = time.time()
                while time.time() - start_wait < 10:
                    if self.downloaded_files: 
                        files_found = len(self.downloaded_files)
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Erro no fluxo PJe TRT2: {e}")

            # Link 2: Processos Físicos TRT2 (Apenas se não achou nada ainda ou para garantir)
            # Geralmente são certidões separadas
            print("Acessando TRT2 Processos Físicos...")
            try:
                page.goto("https://aplicacoes10.trt2.jus.br/certidao_trabalhista_eletronica/public/index.php/index/solicitacao", timeout=30000)
                
                # Preenche formulário legado
                page.check("input[id='tipoDocumentoPesquisado-1']") # CPF
                page.fill("input[name='numeroDocumentoPesquisado']", data['cpf_cnpj'])
                page.fill("input[name='nomePesquisado']", data['nome'])
                page.select_option("select[name='jurisdicao']", "0")

                # Callback para repreencher após reload
                def refill_action_trt2(p):
                    try:
                        p.check("input[id='tipoDocumentoPesquisado-1']") 
                        p.fill("input[name='numeroDocumentoPesquisado']", data['cpf_cnpj'])
                        p.fill("input[name='nomePesquisado']", data['nome'])
                        p.select_option("select[name='jurisdicao']", "0")
                    except Exception as e:
                         print(f"Erro ao repreencher TRT2: {e}")

                # Resolver captcha
                print("Resolvendo Captcha TRT2 Físico...")
                self.handle_image_captcha(
                    page,
                    "img[src*='captcha/image.php']",
                    "input[id='captcha-input']",
                    submit_selector="input[type='submit'], button[type='submit']",
                    max_attempts=10,
                    reload_action_callback=refill_action_trt2
                )
            except Exception as e:
                print(f"Erro no fluxo TRT2 Físico: {e}")

            # Verificação Final
            if self.wait_for_downloads(timeout=20):
                 print("TRT2: Download confirmado.")
                 browser.close()
                 return {
                     "status": "success",
                     "message": f"Certidão TRT2 processada (Total arquivos: {len(self.downloaded_files)}).",
                     "files": self.downloaded_files
                 }
            
            # Se já baixamos pelo menos um (ex: do PJe), é sucesso
            if len(self.downloaded_files) > 0:
                 browser.close()
                 return {
                     "status": "success",
                     "message": "Certidão TRT2 processada (Parcial).",
                     "files": self.downloaded_files
                 }

            # Screenshot de falha
            sanitized_cpf = data['cpf_cnpj'].replace('.', '').replace('-', '')
            screenshot_path = os.path.join(self.output_dir, f"TRT2_{sanitized_cpf}_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            browser.close()
            return {
                "status": "warning", 
                "message": "TRT2 finalizado sem downloads detectados.",
                "files": [screenshot_path]
            }
