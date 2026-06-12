import cv2
import os

def aplicar_desfoque():
    """Lê as imagens da pasta atual, aplica o Desfoque Gaussiano e sobrescreve os arquivos."""
    
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("Iniciando a redução de ruído (Gaussian Blur aumentado para 7x7)...")
    print("-" * 50)
    
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            
            imagem_cinza = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            
            if imagem_cinza is not None:
                # ALTERAÇÃO AQUI: Kernel aumentado para (7, 7)
                imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (7, 7), 0)
                
                cv2.imwrite(caminho_completo, imagem_suavizada)
                
                print(f"Sucesso: '{nome_arquivo}' suavizado e sobrescrito.")
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")

    print("-" * 50)
    print(f"Processamento concluído! {contador} imagem(ns) suavizada(s).")

if __name__ == "__main__":
    aplicar_desfoque()