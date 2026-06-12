import cv2
import numpy as np
import os

def detectar_bordas():
    """Lê as imagens da pasta atual, aplica Canny e Dilatação, e sobrescreve os arquivos."""
    
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("Iniciando a detecção de bordas e Dilatação Morfológica...")
    print("-" * 50)
    
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            
            imagem_suavizada = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            
            if imagem_suavizada is not None:
                # Aplica o Detector de Bordas Canny
                bordas = cv2.Canny(imagem_suavizada, 75, 200)
                
                # ALTERAÇÃO AQUI: Aplica a dilatação para fechar os buracos no contorno
                kernel = np.ones((5, 5), np.uint8)
                bordas_dilatadas = cv2.dilate(bordas, kernel, iterations=2)
                
                # Salva a imagem com as bordas dilatadas
                cv2.imwrite(caminho_completo, bordas_dilatadas)
                
                print(f"Sucesso: '{nome_arquivo}' processado (bordas dilatadas).")
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")

    print("-" * 50)
    print(f"Processamento concluído! {contador} imagem(ns) com bordas detectadas.")

if __name__ == "__main__":
    detectar_bordas()