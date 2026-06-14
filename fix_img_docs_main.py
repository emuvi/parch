import cv2
import imutils
import numpy as np
import os
import shutil

def converter_para_cinza_com_backup():
    """Cria backup na pasta 'origem', converte imagens para cinza e sobrescreve no diretório atual."""
    diretorio_atual = '.'
    diretorio_backup = 'origem'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    if not os.path.exists(diretorio_backup):
        os.makedirs(diretorio_backup)
        print(f"Pasta '{diretorio_backup}' criada para armazenar as fotos originais.")
    
    print("\n>>> Executando Passo 1: Backup na pasta 'origem' e Escala de Cinza...")
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            caminho_backup = os.path.join(diretorio_backup, nome_arquivo)
            
            shutil.copy2(caminho_completo, caminho_backup)
            imagem = cv2.imread(caminho_completo)
            if imagem is not None:
                imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(caminho_completo, imagem_cinza)
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")
    print(f"Passo 1 concluído! {contador} imagem(ns) processada(s).")

def aplicar_desfoque():
    """Lê as imagens da pasta atual, aplica o Desfoque Gaussiano e sobrescreve os arquivos."""
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("\n>>> Executando Passo 2: Redução de Ruído (Desfoque 7x7)...")
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            imagem_cinza = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            if imagem_cinza is not None:
                imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (7, 7), 0)
                cv2.imwrite(caminho_completo, imagem_suavizada)
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")
    print(f"Passo 2 concluído! {contador} imagem(ns) processada(s).")

def detectar_bordas():
    """Lê as imagens da pasta atual, aplica Canny e Dilatação, e sobrescreve os arquivos."""
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("\n>>> Executando Passo 3: Detecção de Bordas (Canny + Dilatação)...")
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            imagem_suavizada = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            if imagem_suavizada is not None:
                bordas = cv2.Canny(imagem_suavizada, 75, 200)
                kernel = np.ones((5, 5), np.uint8)
                bordas_dilatadas = cv2.dilate(bordas, kernel, iterations=2)
                cv2.imwrite(caminho_completo, bordas_dilatadas)
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")
    print(f"Passo 3 concluído! {contador} imagem(ns) processada(s).")

def detectar_e_filtrar_contornos_leniente():
    """Encontra contornos com tolerância, usando aproximação progressiva ou retângulo delimitador."""
    diretorio_atual = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    print("\n>>> Executando Passo 4: Detecção e Filtragem de Contornos...")
    for nome_arquivo in os.listdir(diretorio_atual):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
            imagem_bordas = cv2.imread(caminho_completo, cv2.IMREAD_GRAYSCALE)
            if imagem_bordas is not None:
                contornos = cv2.findContours(imagem_bordas.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
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
                
                imagem_visualizacao = cv2.cvtColor(imagem_bordas, cv2.COLOR_GRAY2BGR)
                if contorno_documento is not None:
                    cv2.drawContours(imagem_visualizacao, [contorno_documento], -1, (0, 255, 0), 3)
                cv2.imwrite(caminho_completo, imagem_visualizacao)
                contador += 1
            else:
                print(f"Erro: Não foi possível ler a imagem '{nome_arquivo}'.")
    print(f"Passo 4 concluído! {contador} imagem(ns) processada(s).")

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
    """Isola o documento, aplica a perspectiva e exporta o final."""
    diretorio_origem = 'origem'
    diretorio_destino = '.'
    extensoes_validas = ('.jpg', '.jpeg', '.png')
    contador = 0
    
    if not os.path.exists(diretorio_origem):
         print(f"Erro: A pasta '{diretorio_origem}' não foi encontrada. Rode o Passo 1 com backup primeiro.")
         return

    print("\n>>> Executando Passo 5: Isolamento, Retificação e Exportação Final...")
    for nome_arquivo in os.listdir(diretorio_origem):
        if nome_arquivo.lower().endswith(extensoes_validas):
            caminho_origem = os.path.join(diretorio_origem, nome_arquivo)
            caminho_destino = os.path.join(diretorio_destino, nome_arquivo)
            imagem_original = cv2.imread(caminho_origem)
            
            if imagem_original is not None:
                imagem_cinza = cv2.cvtColor(imagem_original, cv2.COLOR_BGR2GRAY)
                imagem_suavizada = cv2.GaussianBlur(imagem_cinza, (7, 7), 0)
                bordas = cv2.Canny(imagem_suavizada, 75, 200)
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
                
                if contorno_documento is not None:
                    pontos_formatados = contorno_documento.reshape(4, 2)
                    documento_final = aplicar_perspectiva(imagem_original, pontos_formatados)
                    cv2.imwrite(caminho_destino, documento_final)
                    contador += 1
                else:
                    print(f"Falha ao processar '{nome_arquivo}'.")
            else:
                print(f"Erro ao ler '{nome_arquivo}'.")
    print(f"Passo 5 concluído! {contador} imagem(ns) finalizada(s).")

def executar_pipeline():
    print("=" * 60)
    print(" INICIANDO PIPELINE DE PROCESSAMENTO DE DOCUMENTOS")
    print("=" * 60)

    converter_para_cinza_com_backup()
    aplicar_desfoque()
    detectar_bordas()
    detectar_e_filtrar_contornos_leniente()
    processar_transformacao_final()

    print("\n" + "=" * 60)
    print(" PIPELINE CONCLUÍDO COM SUCESSO!")
    print(" As imagens finais e retificadas estão na pasta atual.")
    print(" Os arquivos originais estão preservados na pasta 'origem/'.")
    print("=" * 60)

if __name__ == "__main__":
    executar_pipeline()