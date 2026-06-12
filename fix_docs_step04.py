import cv2
import imutils
import numpy as np
import os

def detectar_e_filtrar_contornos_leniente():
    """Encontra contornos com tolerância, usando aproximação progressiva ou retângulo delimitador."""
    
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("Iniciando a detecção e filtragem leniente de contornos...")
    print("-" * 50)
    
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            
            # Carrega a imagem com as bordas (resultado do passo 3)
            imagem_bordas = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            
            if imagem_bordas is not None:
                contornos = cv2.findContours(imagem_bordas.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                contornos = imutils.grab_contours(contornos)
                
                # Mantém apenas os 5 maiores contornos
                contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:5]
                
                contorno_documento = None
                
                if len(contornos) > 0:
                    # TENTATIVA 1: Procurar quadrilátero com diferentes níveis de tolerância
                    for c in contornos:
                        perimetro = cv2.arcLength(c, True)
                        
                        # Testa multiplicadores do epsilon: começa estrito (0.02) e vai ficando leniente (até 0.08)
                        for fator_leniencia in [0.02, 0.04, 0.06, 0.08]:
                            aproximacao = cv2.approxPolyDP(c, fator_leniencia * perimetro, True)
                            if len(aproximacao) == 4:
                                contorno_documento = aproximacao
                                break # Achou 4 pontas, para de tentar outros fatores
                        
                        if contorno_documento is not None:
                            break # Achou um quadrilátero, sai do loop de contornos
                    
                    # TENTATIVA 2 (FALLBACK): Se não achou 4 pontas de jeito nenhum, força um retângulo!
                    if contorno_documento is None:
                        print(f"Aviso: Usando fallback (Retângulo Delimitador) para '{nome_arquivo}'.")
                        maior_contorno = contornos[0] # Pega o maior contorno (provavelmente o papel)
                        
                        # Encontra o retângulo (mesmo que rotacionado) que cobre esse contorno
                        rect = cv2.minAreaRect(maior_contorno)
                        box = cv2.boxPoints(rect)
                        box = np.array(box, dtype="int")
                        
                        # Formata a matriz para o mesmo formato que o approxPolyDP retorna: (4, 1, 2)
                        contorno_documento = box.reshape(4, 1, 2)
                
                # Visualização
                imagem_visualizacao = cv2.cvtColor(imagem_bordas, cv2.COLOR_GRAY2BGR)
                
                if contorno_documento is not None:
                    # Desenha o contorno com linha verde de espessura 3
                    cv2.drawContours(imagem_visualizacao, [contorno_documento], -1, (0, 255, 0), 3)
                    if len(contorno_documento) == 4:
                         print(f"Sucesso: Documento localizado em '{nome_arquivo}'.")
                else:
                    print(f"Falha Crítica: Nenhum contorno encontrado em '{nome_arquivo}'.")
                
                cv2.imwrite(caminho_completo, imagem_visualizacao)
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")

    print("-" * 50)
    print(f"Processamento concluído! {contador} imagem(ns) avaliada(s).")

if __name__ == "__main__":
    detectar_e_filtrar_contornos_leniente()