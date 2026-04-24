from .base_bot import BaseBot
import time
import os
from playwright.sync_api import sync_playwright

class TJSPBot(BaseBot):
    def run(self, data):
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.get('headless', True),
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print("Acessando TJSP...")
            try:
                page.goto("https://esaj.tjsp.jus.br/sco/abrirCadastro.do", wait_until="networkidle")
            except Exception as e:
                print(f"Erro ao acessar TJSP: {e}")
                browser.close()
                return {"status": "error", "message": f"Erro ao acessar site: {e}", "files": []}

            # Selecionar Modelo: 52 = CERTIDÃO DE DISTRIBUIÇÃO CÍVEL EM GERAL - SAJ SGC
            print("Selecionando modelo de certidão...")
            page.select_option("select[id='cdModelo']", value='52')
            
            # Aguarda carregamento dos campos
            time.sleep(2)

            # Selecionar Pessoa Física
            if page.locator("input[id='tpPessoaF']").is_visible():
                page.click("input[id='tpPessoaF']")
            
            # Preencher Dados
            try:
                print(f"Preenchendo dados para: {data['nome']}")
                # Nome
                page.fill("input[id='nmCadastroF']", data['nome'])
                # CPF
                page.fill("input[name='entity.nuCpfFormatado']", data['cpf_cnpj'])
                
                # RG
                if 'rg' in data and data['rg']:
                    page.fill("input[name='entity.nuRgFormatado']", data['rg'])
                
                # Gênero
                genero = data.get('genero', 'Masculino')
                if genero == 'Feminino':
                     page.click("input[id='flGeneroF']", force=True)
                else: 
                     page.click("input[id='flGeneroM']", force=True)

                # Email
                page.fill("input[id='identity.solicitante.deEmail']", data['email'])
            except Exception as e:
                print(f"Erro ao preencher formulário TJSP: {e}")

            # Checkbox de confirmação
            page.check("input[id='confirmacaoInformacoes']")
            
            # Simular interação para habilitar botão
            page.keyboard.press("Tab")
            time.sleep(2)

            # Aguardar botão de enviar habilitar (Loop de verificação)
            print("Aguardando liberação do botão Enviar...")
            try:
                # Tenta por 45 segundos
                for i in range(15):
                    # Verifica se habilitou
                    is_disabled = page.get_attribute("input[id='pbEnviar']", "disabled")
                    if is_disabled is None: # Habilitado
                        print("Botão habilitado!")
                        page.click("input[id='pbEnviar']")
                        break
                    
                    # Se não, tenta forçar eventos que destravam
                    page.click("body", position={"x": 10, "y": 10}) # Clique fora
                    page.focus("input[id='confirmacaoInformacoes']")
                    
                    time.sleep(3)
                else:
                    print("Tempo esgotou. Tentando clique forçado...")
                    page.click("input[id='pbEnviar']", force=True)
            except Exception as e:
                print(f"Erro ao tentar clicar em Enviar: {e}")
            
            # Verificar resultado
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
                self.setup_download_handler(page, "TJSP", data)
                
                if page.locator("text=Pedido cadastrado com sucesso").is_visible() or page.locator("text=sucesso").is_visible():
                    msg = "Pedido TJSP cadastrado com sucesso! Verifique seu e-mail."
                    print(msg)
                    browser.close()
                    return {"status": "success", "message": msg, "files": []}
                
                elif page.locator("text=Download").is_visible():
                    page.click("text=Download")
                    if self.wait_for_downloads(timeout=30):
                         browser.close()
                         return {"status": "success", "message": "Certidão TJSP baixada.", "files": self.downloaded_files}
                
                # Se houver erro visível na página
                error_msg = page.locator(".mensagemErro").text_content() if page.locator(".mensagemErro").is_visible() else None
                
                # Screenshot de estado final
                sanitized_cpf = data['cpf_cnpj'].replace('.', '').replace('-', '')
                screenshot_path = os.path.join(self.output_dir, f"TJSP_{sanitized_cpf}_{int(time.time())}.png")
                page.screenshot(path=screenshot_path)
                
                browser.close()
                return {
                    "status": "warning",
                    "message": f"TJSP finalizado. {f'Erro: {error_msg}' if error_msg else 'Verificar print.'}",
                    "files": [screenshot_path]
                }

            except Exception as e:
                print(f"Erro no processamento final do TJSP: {e}")
                browser.close()
                return {"status": "error", "message": f"Erro TJSP: {e}", "files": []}
