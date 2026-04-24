import os
import time
from abc import ABC, abstractmethod

class BaseBot(ABC):
    def __init__(self, config):
        self.config = config
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.solver = config.get('captcha_solver')
        self.downloaded_files = []
        self.active_downloads = 0

    @abstractmethod
    def run(self, data):
        pass

    def setup_download_handler(self, page, prefix, data):
        """Configura o listener para salvar downloads automaticamente."""
        def handle_download(download):
            self.active_downloads += 1
            try:
                print(f"Download iniciado: {download.suggested_filename}")
                sanitized_cpf = data['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '')
                timestamp = int(time.time())
                ext = os.path.splitext(download.suggested_filename)[1] or ".pdf"
                file_name = f"{prefix}_{sanitized_cpf}_{timestamp}{ext}"
                path = os.path.join(self.output_dir, file_name)
                download.save_as(path)
                print(f"Arquivo salvo com sucesso em: {path}")
                self.downloaded_files.append(path)
            except Exception as e:
                print(f"Erro ao salvar download: {e}")
            finally:
                self.active_downloads -= 1

        page.on("download", handle_download)

    def handle_image_captcha(self, page, img_selector, input_selector, submit_selector=None, success_selector=None, max_attempts=7, reload_action_callback=None, min_length=0):
        """
        Tenta resolver captcha de imagem usando ddddocr. 
        Se falhar após todas as tentativas, solicita input manual via terminal/interface.
        """
        for attempt in range(max_attempts):
            try:
                # 1. Verificar se já passamos (prioridade máxima)
                if success_selector and page.query_selector(success_selector):
                    print("Capcha superado ou inexistente.")
                    return True

                print(f"Tentativa {attempt + 1}/{max_attempts} de resolver captcha...")
                
                # Aguarda carregamento de rede antes de procurar imagem
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except: pass

                img_element = page.query_selector(img_selector)
                
                # Se não achou imagem:
                if not img_element:
                    if success_selector and page.query_selector(success_selector):
                        return True
                    print("Imagem do captcha não encontrada. Recarregando...")
                    page.reload()
                    if reload_action_callback: reload_action_callback(page)
                    continue

                captcha_text = ""
                img_bytes = None
                try:
                    img_bytes = img_element.screenshot()
                    captcha_text = self.solver.solve_image_ocr(img_bytes)
                except Exception as e:
                    print(f"Erro ao capturar/resolver: {e}")
                    captcha_text = ""
                
                # Validação de cumprimento mínimo
                if captcha_text and min_length > 0 and len(captcha_text) < min_length:
                    print(f"Captcha resolvido '{captcha_text}' tem menos de {min_length} caracteres. Ignorando...")
                    captcha_text = ""

                # Falha OCR e não é a última tentativa -> Reload
                if not captcha_text and attempt < max_attempts - 1:
                    print("OCR retornou vazio ou inválido. Tentando recarregar imagem...")
                    page.reload()
                    if reload_action_callback: reload_action_callback(page)
                    continue
                
                # Falha OCR e É a última tentativa -> Manual
                if (not captcha_text) and (attempt == max_attempts - 1):
                    print("⚠️ Falha na resolução automática. Solicitando intervenção manual...")
                    
                    if img_bytes is None:
                        # Tenta capturar de novo se falhou antes
                        try: img_bytes = img_element.screenshot()
                        except: 
                            print("Impossível capturar para manual.")
                            return False

                    captcha_path = os.path.join(self.output_dir, "captcha_manual.png")
                    with open(captcha_path, "wb") as f:
                        f.write(img_bytes)
                    
                    request_file = os.path.join(self.output_dir, "captcha_request.json")
                    response_file = os.path.join(self.output_dir, "captcha_response.json")
                    
                    if os.path.exists(response_file): os.remove(response_file)
                    
                    import json
                    with open(request_file, "w") as f:
                        json.dump({"image_path": captcha_path, "status": "waiting"}, f)
                    
                    print(f"AGUARDANDO INPUT MANUAL... (Verifique a interface)")
                    
                    for _ in range(24): 
                        time.sleep(5)
                        if os.path.exists(response_file):
                            with open(response_file, "r") as f:
                                resp = json.load(f)
                                captcha_text = resp.get("text")
                                print(f"Recebido input manual: {captcha_text}")
                                if os.path.exists(request_file): os.remove(request_file)
                                break
                    
                    if not captcha_text:
                        print("Tempo esgotado para input manual.")
                        return False

                # Submissão (seja auto ou manual)
                if captcha_text:
                    print(f"Usando captcha: {captcha_text}")
                    page.fill(input_selector, captcha_text)
                    
                    if submit_selector:
                        page.click(submit_selector)
                        try:
                            # TST demora um pouco para validar
                            time.sleep(1)
                            page.wait_for_load_state("networkidle", timeout=10000)
                        except: pass

                        if success_selector:
                            if page.query_selector(success_selector): return True
                        else:
                            # Verifica se imagem sumiu (sucesso) ou se ainda está lá (falha)
                            time.sleep(1)
                            if not page.query_selector(img_selector): 
                                return True
                            else:
                                print("Captcha incorreto (imagem persistiu).")
                    else:
                        return True
                else:
                    print("Captcha vazio/não resolvido.")

            except Exception as e:
                print(f"Erro na tentativa {attempt + 1}: {e}")
            
            # Recarrega se falhar (e não for a última tentativa manual bem sucedida)
            if attempt < max_attempts - 1:
                page.reload()
                if reload_action_callback: reload_action_callback(page)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except: pass
                
        return False

    def wait_for_downloads(self, timeout=30):
        """Aguarda até que pelo menos um arquivo tenha sido baixado ou o timeout expire."""
        start = time.time()
        while time.time() - start < timeout:
            if self.downloaded_files:
                return True
            if self.active_downloads > 0:
                 # Se houver downloads ativos, estende a espera
                 time.sleep(1)
                 continue
            time.sleep(0.5)
        
        # Última chance: se tiver active_downloads, espera mais um pouco
        waited_extra = 0
        while self.active_downloads > 0 and waited_extra < 60:
             time.sleep(1)
             waited_extra += 1
             if self.downloaded_files: return True

        return len(self.downloaded_files) > 0
