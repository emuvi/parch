import os
import random
import string


def get_random_name(comprimento=18):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for i in range(comprimento))


def rand_rename_mp3():
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    os.chdir(diretorio_script)
    
    print(f"Executando no diretório: {diretorio_script}\n")
    
    arquivos_na_pasta = os.listdir(diretorio_script)
    
    arquivos_mp3 = [f for f in arquivos_na_pasta if f.lower().endswith('.mp3')]
    
    if not arquivos_mp3:
        print("Nenhum arquivo .mp3 encontrado para renomear.")
        return
        
    print(f"Encontrados {len(arquivos_mp3)} arquivos .mp3 para renomear.")

    for nome_antigo in arquivos_mp3:
        extensao = ".mp3"
        novo_nome_base = ""
        novo_nome_completo = ""

        while True:
            novo_nome_base = get_random_name()
            novo_nome_completo = novo_nome_base + extensao
            if not os.path.exists(os.path.join(diretorio_script, novo_nome_completo)):
                break
        
        caminho_antigo = os.path.join(diretorio_script, nome_antigo)
        caminho_novo = os.path.join(diretorio_script, novo_nome_completo)

        try:
            os.rename(caminho_antigo, caminho_novo)
            print(f'Renomeado: "{nome_antigo}" -> "{novo_nome_completo}"')
        except OSError as e:
            print(f'Erro ao renomear "{nome_antigo}": {e}')


def main():
    proceed = input("Do you want to proceed with random renaming mp3 files in the current directory? (yes/no): ").strip().lower()
    if proceed == 'yes':
        rand_rename_mp3()
        print("Renaming completed.")
    else:
        print("Operation canceled.")


if __name__ == "__main__":
    main()
    input()