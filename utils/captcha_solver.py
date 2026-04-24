import ddddocr
import io
from PIL import Image

class CaptchaSolver:
    def __init__(self):
        # Inicializa o ddddocr. O modelo é carregado na primeira chamada.
        # Usando old=True para compatibilidade e show_ad=False para evitar logs desnecessários.
        self.ocr = ddddocr.DdddOcr(old=True, show_ad=False)
        print("ddddocr inicializado.")

    def preprocess_image(self, image_bytes):
        """
        Aplica pré-processamento na imagem para melhorar o OCR.
        Converte para escala de cinza e aplica limiarização (threshold).
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Converter para escala de cinza
            image = image.convert('L')
            # Aplicar limiarização (thresholding) para deixar preto e branco puro
            # Ajuste o valor 140 conforme necessário para o captcha específico
            image = image.point(lambda x: 0 if x < 140 else 255, '1')
            
            # Converter de volta para bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except Exception as e:
            print(f"Erro no pré-processamento de imagem: {e}")
            return image_bytes

    def solve_image_ocr(self, image_bytes):
        """
        Resolve o captcha de imagem usando ddddocr.
        :param image_bytes: Bytes da imagem (screenshot do Playwright).
        :return: Texto do captcha.
        """
        try:
            # Tenta com pré-processamento primeiro (melhor para TST)
            processed_bytes = self.preprocess_image(image_bytes)
            result = self.ocr.classification(processed_bytes)
            return result
        except Exception as e:
            print(f"Erro ao resolver captcha com ddddocr: {e}")
            return ""

    def solve_slide_puzzle(self, target_bytes, background_bytes):
        """
        Resolve o captcha de quebra-cabeça deslizante (slide puzzle).
        :param target_bytes: Bytes da imagem da peça a ser deslizada.
        :param background_bytes: Bytes da imagem de fundo.
        :return: Coordenadas (x, y) do movimento.
        """
        try:
            # O ddddocr aceita bytes diretamente
            res = self.ocr.slide_match(target_bytes, background_bytes, simple_target=True)
            # Retorna a coordenada X para o movimento (geralmente só X é necessário)
            # O resultado é um dicionário com 'target' (coordenadas da peça) e 'gap' (coordenadas do buraco)
            # Para o slide puzzle, o que importa é a coordenada X do buraco ou da peça, dependendo da implementação do site.
            # Vamos retornar a coordenada X da peça (target) que é o que o ddddocr costuma retornar para o movimento.
            return res.get('target')[0]
        except Exception as e:
            print(f"Erro ao resolver slide puzzle com ddddocr: {e}")
            return None
