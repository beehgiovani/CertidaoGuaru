import os
import json
import time
from utils.captcha_solver import CaptchaSolver
from modules.tst_bot import TSTBot
from modules.receita_bot import ReceitaBot
from modules.tjsp_bot import TJSPBot
from modules.trf3_bot import TRF3Bot
from modules.trt2_bot import TRT2Bot
from modules.cjf_bot import CJFBot

def process_request(user_data, selected_bots=None, log_callback=print, headless=True):
    """
    Executa a automação para os dados fornecidos.
    
    :param user_data: Dict com dados (cpf, nome, etc)
    :param selected_bots: Lista de strings com nomes dos bots a executar (ex: ['TSTBot', 'TRT2Bot'])
    :param log_callback: Função para exibir logs (padrão: print)
    :param headless: Se True, executa sem interface gráfica.
    """
    # Inicializa o solver gratuito (ddddocr)
    log_callback("Inicializando solver de captcha...")
    solver = CaptchaSolver()
    
    config = {
        'captcha_solver': solver,
        'headless': headless
    }

    # Mapeamento de nomes para classes
    available_bots = {
        'TSTBot': TSTBot(config),
        'TRT2Bot': TRT2Bot(config),
        'TJSPBot': TJSPBot(config),
        'TRF3Bot': TRF3Bot(config),
        'ReceitaBot': ReceitaBot(config),
        'CJFBot': CJFBot(config)
    }
    
    # Garante que pasta output existe
    if not os.path.exists("output"):
        os.makedirs("output")

    if selected_bots:
        bots_to_run = [available_bots[name] for name in selected_bots if name in available_bots]
    else:
        bots_to_run = list(available_bots.values())

    log_callback(f"Iniciando automação para {user_data.get('nome', 'N/A')}...")
    
    results = {}
    
    for bot in bots_to_run:
        bot_name = bot.__class__.__name__
        try:
            log_callback(f"\n>>> Executando: {bot_name}")
            # Captura retorno estruturado
            result = bot.run(user_data)
            
            if result and isinstance(result, dict):
                status = result.get('status', 'unknown')
                msg = result.get('message', 'Sem mensagem')
                files = result.get('files', [])
                
                if status == 'success':
                    results[bot_name] = f"Sucesso: {msg}"
                    log_callback(f">>> {bot_name} Sucesso. Arquivos: {len(files)}")
                elif status == 'warning':
                     results[bot_name] = f"Atenção: {msg}"
                     log_callback(f">>> {bot_name} Atenção: {msg}")
                else:
                    results[bot_name] = f"Erro: {msg}"
                    log_callback(f">>> {bot_name} Erro: {msg}")
            else:
                # Fallback para bots antigos ou sem retorno
                results[bot_name] = "Finalizado (sem detalhes)"
                log_callback(f">>> {bot_name} finalizado (sem retorno estruturado).")

        except Exception as e:
            error_msg = f"Erro crítico ao executar {bot_name}: {str(e)}"
            log_callback(error_msg)
            results[bot_name] = f"Erro Crítico: {str(e)}"
            
    return results

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Certidao Automazada Bot Runner")
    parser.add_argument("--input-json", help="Path to input task JSON file")
    parser.add_argument("--output-json", help="Path to save results JSON file", default="output/process_results.json")
    args = parser.parse_args()

    if args.input_json:
        try:
            with open(args.input_json, 'r') as f:
                task_data = json.load(f)
            
            user_data = task_data.get('user_data')
            selected_bots = task_data.get('selected_bots')
            headless = task_data.get('headless', True)
            
            # Executa
            results = process_request(user_data, selected_bots, headless=headless)
            
            # Salva resultados
            with open(args.output_json, 'w') as f:
                json.dump(results, f, indent=4)
                
            print("Processamento finalizado. Resultados salvos.")
            
        except Exception as e:
            print(f"Erro fatal no main.py: {e}")
            sys.exit(1)
    else:
        # Modo legado / debug manual
        user_data = {
            'cpf_cnpj': '396.832.838-88', 
            'cpf': '39683283888',         
            'nome': 'Bruno giovani pereira',
            'rg': '491005805',
            'genero': 'Masculino',
            'data_nascimento': '25/05/1993',
            'email': 'brunogp.corretor@gmail.com'
        }
        process_request(user_data)

if __name__ == "__main__":
    main()
