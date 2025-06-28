import os
import random
import string

def gerar_nome_aleatorio(comprimento=18):
    """Gera uma string aleatória de letras e números."""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for i in range(comprimento))

def renomear_arquivos_mp3():
    """
    Renomeia todos os arquivos .mp3 no diretório do script para nomes aleatórios
    de 18 caracteres.
    """
    # Obtém o caminho absoluto do diretório onde o script está localizado
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    os.chdir(diretorio_script)
    
    print(f"Executando no diretório: {diretorio_script}\n")
    
    # Lista todos os arquivos no diretório
    arquivos_na_pasta = os.listdir(diretorio_script)
    
    # Filtra apenas os arquivos .mp3
    arquivos_mp3 = [f for f in arquivos_na_pasta if f.lower().endswith('.mp3')]
    
    if not arquivos_mp3:
        print("Nenhum arquivo .mp3 encontrado para renomear.")
        return
        
    print(f"Encontrados {len(arquivos_mp3)} arquivos .mp3 para renomear.")

    for nome_antigo in arquivos_mp3:
        extensao = ".mp3"
        novo_nome_base = ""
        novo_nome_completo = ""

        # Loop para garantir que o novo nome não exista
        while True:
            novo_nome_base = gerar_nome_aleatorio()
            novo_nome_completo = novo_nome_base + extensao
            if not os.path.exists(os.path.join(diretorio_script, novo_nome_completo)):
                break
        
        # Caminho completo dos arquivos antigo e novo
        caminho_antigo = os.path.join(diretorio_script, nome_antigo)
        caminho_novo = os.path.join(diretorio_script, novo_nome_completo)

        try:
            # Renomeia o arquivo
            os.rename(caminho_antigo, caminho_novo)
            print(f'Renomeado: "{nome_antigo}" -> "{novo_nome_completo}"')
        except OSError as e:
            print(f'Erro ao renomear "{nome_antigo}": {e}')

if __name__ == "__main__":
    renomear_arquivos_mp3()
    print("\nProcesso concluído.")