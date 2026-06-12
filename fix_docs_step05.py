import cv2
import numpy as np
import os
import imutils

def ordenar_pontos(pts):
    """Ordena as coordenadas dos 4 cantos do papel."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def aplicar_perspectiva(imagem, pts):
    """Aplica a transformação de perspectiva para 'alisar' o documento."""
    rect = ordenar_pontos(pts)
    (tl, tr, br, bl) = rect

    larguraA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    larguraB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxLargura = max(int(larguraA), int(larguraB))

    alturaA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    alturaB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxAltura = max(int(alturaA), int(alturaB))

    dst = np.array([
        [0, 0],
        [maxLargura - 1, 0],
        [maxLargura - 1, maxAltura - 1],
        [0, maxAltura - 1]
    ], dtype="float32")

    matriz_transformacao = cv2.getPerspectiveTransform(rect, dst)
    imagem_recortada = cv2.warpPerspective(imagem, matriz_transformacao, (maxLargura, maxAltura))
    return imagem_recortada

def processar_transformacao_final():
    diretorio_origem = 'origem'
    diretorio_destino = '.' # Salva na pasta atual
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    if not os.path.exists(diretorio_origem):
         print(f"Erro: A pasta '{diretorio_origem}' não foi encontrada. Rode o Passo 1 com backup primeiro.")
         return

    print("Iniciando o isolamento e retificação com Correção Morfológica...")
    print("-" * 50)
    
    for nome_arquivo in os.listdir(diretorio_origem):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_origem = os.path.join(diretorio_origem, nome_arquivo)
            caminho_destino = os.path.join(diretorio_destino, nome_arquivo)
            
            # Carrega a imagem original colorida
            imagem_original = cv2.imread(caminho_origem)
            
            if imagem_original is not None:
                # --- PROCESSAMENTO EM MEMÓRIA ATUALIZADO ---
                imagem_cinza = cv2.cvtColor(imagem_original, cv2.COLOR_BGR2GRAY)
                
                # ALTERAÇÃO: Blur aumentado
                imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (7, 7), 0)
                
                bordas = cv2.Canny(imagem_suavizada, 75, 200)
                
                # ALTERAÇÃO: Dilatação adicionada
                kernel = np.ones((5, 5), np.uint8)
                bordas_dilatadas = cv2.dilate(bordas, kernel, iterations=2)
                
                contornos = cv2.findContours(bordas_dilatadas.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                contornos = imutils.grab_contours(contornos)
                contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:5]
                
                contorno_documento = None
                
                if len(contornos) > 0:
                    for c in contornos:
                        perimetro = cv2.arcLength(c, True)
                        for fator_leniencia in [0.02, 0.04, 0.06, 0.08]:
                            aproximacao = cv2.approxPolyDP(c, fator_leniencia * perimetro, True)
                            if len(aproximacao) == 4:
                                contorno_documento = aproximacao
                                break
                        if contorno_documento is not None:
                            break
                    
                    if contorno_documento is None:
                        maior_contorno = contornos[0]
                        rect = cv2.minAreaRect(maior_contorno)
                        box = cv2.boxPoints(rect)
                        box = np.array(box, dtype="int")
                        contorno_documento = box.reshape(4, 1, 2)
                
                # --- PASSO 6 E 7: APLICA A TRANSFORMAÇÃO ---
                if contorno_documento is not None:
                    pontos_formatados = contorno_documento.reshape(4, 2)
                    documento_final = aplicar_perspectiva(imagem_original, pontos_formatados)
                    
                    cv2.imwrite(caminho_destino, documento_final)
                    print(f"Sucesso: Documento '{nome_arquivo}' extraído e endireitado!")
                    contador += 1
                else:
                    print(f"Falha Crítica: Não foi possível calcular a perspectiva para '{nome_arquivo}'.")
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}' da pasta origem.")

    print("-" * 50)
    print(f"Processamento completo! {contador} documento(s) perfeitamente extraído(s).")

if __name__ == "__main__":
    processar_transformacao_final()