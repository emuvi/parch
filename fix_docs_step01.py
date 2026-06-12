import cv2
import os
import shutil

def converter_para_cinza_com_backup():
    """Cria backup na pasta 'origem', converte imagens para cinza e sobrescreve no diretório atual."""
    
    diretorio_atual = '.'
    diretorio_backup = 'origem'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    # Verifica se a pasta de backup já existe. Se não, cria a pasta.
    if not os.path.exists(diretorio_backup):
        os.makedirs(diretorio_backup)
        print(f"Pasta '{diretorio_backup}' criada para armazenar as fotos originais.")
    
    print("Iniciando backup e conversão para escala de cinza...")
    print("-" * 50)
    
    for nome_arquivo in os.listdir(diretorio_atual):
        # Ignora arquivos que já estejam dentro da pasta 'origem' (o os.listdir não entra nela, mas é boa prática)
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            caminho_backup = os.path.join(diretorio_backup, nome_arquivo)
            
            # 1. Faz a cópia exata do arquivo para a pasta de backup preservando os metadados
            shutil.copy2(caminho_completo, caminho_backup)
            
            # 2. Carrega a imagem original do diretório atual
            imagem = cv2.imread(caminho_completo)
            
            if imagem is not None:
                # 3. Converte para escala de cinza
                imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
                
                # 4. Salva a imagem, sobrescrevendo o arquivo no diretório atual
                cv2.imwrite(caminho_completo, imagem_cinza)
                
                print(f"Sucesso: '{nome_arquivo}' copiada para 'origem/' e convertida para cinza.")
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")

    print("-" * 50)
    print(f"Processamento concluído! {contador} imagem(ns) com backup feito e convertidas.")

if __name__ == "__main__":
    converter_para_cinza_com_backup()