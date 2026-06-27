import cv2
import imutils
import numpy as np
import os
import shutil

def criar_diretorio(caminho):
    """
    Cria um diretório se ele não existir, tratando possíveis erros de sistema.
    """
    try:
        if not os.path.exists(caminho):
            print(f"[*] Criando diretório: '{caminho}'...")
            os.makedirs(caminho)
        else:
            print(f"[*] Diretório '{caminho}' já existe.")
        return True
    except Exception as e:
        print(f"[!] Erro ao criar diretório '{caminho}': {e}")
        return False

def ler_imagem(caminho, modo=cv2.IMREAD_COLOR):
    """
    Lê uma imagem do disco de forma segura e exibe avisos no caso de arquivo não encontrado.
    """
    try:
        print(f"[*] Lendo imagem: '{caminho}'...")
        imagem = cv2.imread(caminho, modo)
        if imagem is None:
            print(f"[!] Erro: Imagem '{caminho}' não encontrada ou formato inválido.")
            return None
        return imagem
    except Exception as e:
        print(f"[!] Erro inesperado ao ler imagem '{caminho}': {e}")
        return None

def salvar_imagem(caminho, imagem):
    """
    Salva uma imagem no disco, relatando sucesso ou falha da operação do OpenCV.
    """
    try:
        print(f"[*] Salvando imagem: '{caminho}'...")
        sucesso = cv2.imwrite(caminho, imagem)
        if not sucesso:
            print(f"[!] Erro: Falha ao salvar imagem em '{caminho}'.")
            return False
        return True
    except Exception as e:
        print(f"[!] Erro inesperado ao salvar imagem '{caminho}': {e}")
        return False

def fazer_backup_arquivo(origem, destino):
    """
    Copia e guarda um arquivo original de forma segura usando shutil.
    """
    try:
        print(f"[*] Fazendo backup de '{origem}' para '{destino}'...")
        shutil.copy2(origem, destino)
        return True
    except Exception as e:
        print(f"[!] Erro ao fazer backup de '{origem}': {e}")
        return False

def aplicar_escala_cinza(imagem):
    """
    Converte uma imagem BGR (colorida) para escala de cinza de maneira unificada.
    """
    try:
        print("[*] Convertendo imagem para escala de cinza...")
        return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        print(f"[!] Erro ao converter para escala de cinza: {e}")
        return None

def aplicar_desfoque_gaussiano(imagem, kernel=(7, 7)):
    """
    Aplica desfoque gaussiano na imagem visando suavizar e reduzir o ruído visual.
    """
    try:
        print(f"[*] Aplicando desfoque gaussiano com kernel {kernel}...")
        return cv2.GaussianBlur(imagem, kernel, 0)
    except Exception as e:
        print(f"[!] Erro ao aplicar desfoque gaussiano: {e}")
        return None

def aplicar_canny_e_dilatacao(imagem, threshold1=75, threshold2=200):
    """
    Aplica o algoritmo Canny para detecção de bordas e logo após espessa as linhas (dilatação).
    """
    try:
        print("[*] Aplicando detecção de bordas (Canny)...")
        bordas = cv2.Canny(imagem, threshold1, threshold2)
        print("[*] Aplicando dilatação nas bordas para reforçar contornos...")
        kernel = np.ones((5, 5), np.uint8)
        bordas_dilatadas = cv2.dilate(bordas, kernel, iterations=2)
        return bordas_dilatadas
    except Exception as e:
        print(f"[!] Erro ao aplicar detecção de bordas e dilatação: {e}")
        return None

def encontrar_maior_contorno_documento(imagem_bordas):
    """
    Tenta encontrar um contorno quadrilátero que represente o documento na imagem de bordas.
    Caso não consiga achar perfeitamente os 4 pontos com leniência, aproxima usando minAreaRect.
    """
    try:
        print("[*] Procurando contornos no mapa de bordas...")
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
                        print(f"[*] Contorno de 4 pontos encontrado (fator de leniência: {fator_leniencia}).")
                        break
                if contorno_documento is not None:
                    break
            
            if contorno_documento is None:
                print("[*] Contorno de 4 pontos não encontrado com precisão. Usando retângulo delimitador no maior contorno.")
                maior_contorno = contornos[0]
                rect = cv2.minAreaRect(maior_contorno)
                box = cv2.boxPoints(rect)
                box = np.array(box, dtype="int")
                contorno_documento = box.reshape(4, 1, 2)
        else:
            print("[!] Nenhum contorno encontrado na imagem.")
            
        return contorno_documento
    except Exception as e:
        print(f"[!] Erro ao encontrar contornos do documento: {e}")
        return None

def ordenar_pontos(pts):
    """
    Ordena matriz de 4 coordenadas no sentido horário: 
    superior-esquerdo, superior-direito, inferior-direito, inferior-esquerdo.
    """
    try:
        print("[*] Ordenando e orientando os 4 pontos do documento...")
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect
    except Exception as e:
        print(f"[!] Erro ao ordenar pontos: {e}")
        return None

def aplicar_transformacao_perspectiva(imagem, pts):
    """
    Aplica a transformação geométrica (Warp Perspective) para corrigir a inclinação do documento
    e isolar a folha de papel do cenário de fundo.
    """
    try:
        print("[*] Aplicando transformação de perspectiva (retificação)...")
        rect = ordenar_pontos(pts)
        if rect is None:
            return None
            
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
    except Exception as e:
        print(f"[!] Erro ao aplicar transformação de perspectiva: {e}")
        return None

def listar_arquivos_imagem(diretorio, extensoes_validas=('.jpg', '.jpeg', '.png')):
    """
    Lista e retorna todos os arquivos de imagem válidos presentes em um diretório alvo.
    """
    try:
        print(f"[*] Listando arquivos em '{diretorio}'...")
        arquivos = []
        for nome_arquivo in os.listdir(diretorio):
            if nome_arquivo.lower().endswith(extensoes_validas):
                arquivos.append(nome_arquivo)
        print(f"[*] Encontrados {len(arquivos)} arquivo(s) de imagem válido(s).")
        return arquivos
    except Exception as e:
        print(f"[!] Erro ao listar arquivos em '{diretorio}': {e}")
        return []

def executar_passo_1_cinza_e_backup():
    """Cria backup na pasta 'origem', converte imagens para escala de cinza e sobrescreve no diretório atual."""
    print("\n>>> Executando Passo 1: Backup na pasta 'origem' e Escala de Cinza...")
    diretorio_atual = '.'
    diretorio_backup = 'origem'
    
    if not criar_diretorio(diretorio_backup):
        return
        
    arquivos = listar_arquivos_imagem(diretorio_atual)
    contador = 0
    
    for nome_arquivo in arquivos:
        print(f"\n--- Processando (Passo 1): {nome_arquivo} ---")
        caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
        caminho_backup = os.path.join(diretorio_backup, nome_arquivo)
        
        if fazer_backup_arquivo(caminho_completo, caminho_backup):
            imagem = ler_imagem(caminho_completo, cv2.IMREAD_COLOR)
            if imagem is not None:
                imagem_cinza = aplicar_escala_cinza(imagem)
                if imagem_cinza is not None:
                    if salvar_imagem(caminho_completo, imagem_cinza):
                        contador += 1
                        print(f"[+] Passo 1 concluído com sucesso para '{nome_arquivo}'.")

    print(f"\n>>> Passo 1 concluído globalmente! {contador} de {len(arquivos)} imagem(ns) processada(s).")

def executar_passo_2_desfoque():
    """Lê as imagens em escala de cinza da pasta atual, aplica o Desfoque Gaussiano e as sobrescreve."""
    print("\n>>> Executando Passo 2: Redução de Ruído (Desfoque Gaussiano)...")
    diretorio_atual = '.'
    arquivos = listar_arquivos_imagem(diretorio_atual)
    contador = 0
    
    for nome_arquivo in arquivos:
        print(f"\n--- Processando (Passo 2): {nome_arquivo} ---")
        caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
        
        imagem_cinza = ler_imagem(caminho_completo, cv2.IMREAD_GRAYSCALE)
        if imagem_cinza is not None:
            imagem_suavizada = aplicar_desfoque_gaussiano(imagem_cinza)
            if imagem_suavizada is not None:
                if salvar_imagem(caminho_completo, imagem_suavizada):
                    contador += 1
                    print(f"[+] Passo 2 concluído com sucesso para '{nome_arquivo}'.")

    print(f"\n>>> Passo 2 concluído globalmente! {contador} de {len(arquivos)} imagem(ns) processada(s).")

def executar_passo_3_bordas():
    """Lê as imagens suavizadas da pasta atual, aplica detecção de bordas (Canny + Dilatação) e as sobrescreve."""
    print("\n>>> Executando Passo 3: Detecção de Bordas (Canny + Dilatação)...")
    diretorio_atual = '.'
    arquivos = listar_arquivos_imagem(diretorio_atual)
    contador = 0
    
    for nome_arquivo in arquivos:
        print(f"\n--- Processando (Passo 3): {nome_arquivo} ---")
        caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
        
        imagem_suavizada = ler_imagem(caminho_completo, cv2.IMREAD_GRAYSCALE)
        if imagem_suavizada is not None:
            bordas_dilatadas = aplicar_canny_e_dilatacao(imagem_suavizada)
            if bordas_dilatadas is not None:
                if salvar_imagem(caminho_completo, bordas_dilatadas):
                    contador += 1
                    print(f"[+] Passo 3 concluído com sucesso para '{nome_arquivo}'.")

    print(f"\n>>> Passo 3 concluído globalmente! {contador} de {len(arquivos)} imagem(ns) processada(s).")

def executar_passo_4_contornos():
    """Encontra contornos na imagem de bordas, desenha o contorno verde do documento sobre ela e a sobrescreve."""
    print("\n>>> Executando Passo 4: Detecção e Visualização de Contornos...")
    diretorio_atual = '.'
    arquivos = listar_arquivos_imagem(diretorio_atual)
    contador = 0
    
    for nome_arquivo in arquivos:
        print(f"\n--- Processando (Passo 4): {nome_arquivo} ---")
        caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
        
        imagem_bordas = ler_imagem(caminho_completo, cv2.IMREAD_GRAYSCALE)
        if imagem_bordas is not None:
            contorno_documento = encontrar_maior_contorno_documento(imagem_bordas)
            
            try:
                print("[*] Desenhando contorno encontrado (verde) para visualização...")
                imagem_visualizacao = cv2.cvtColor(imagem_bordas, cv2.COLOR_GRAY2BGR)
                if contorno_documento is not None:
                    cv2.drawContours(imagem_visualizacao, [contorno_documento], -1, (0, 255, 0), 3)
                
                if salvar_imagem(caminho_completo, imagem_visualizacao):
                    contador += 1
                    print(f"[+] Passo 4 concluído com sucesso para '{nome_arquivo}'.")
            except Exception as e:
                print(f"[!] Erro ao desenhar/salvar contorno em '{nome_arquivo}': {e}")

    print(f"\n>>> Passo 4 concluído globalmente! {contador} de {len(arquivos)} imagem(ns) processada(s).")

def executar_passo_5_transformacao_final():
    """Lê os originais do backup, detecta as bordas/contornos sem salvar fases intermediárias, aplica a perspectiva e exporta final."""
    print("\n>>> Executando Passo 5: Isolamento, Retificação e Exportação Final...")
    diretorio_origem = 'origem'
    diretorio_destino = '.'
    
    if not os.path.exists(diretorio_origem):
         print(f"[!] Erro: A pasta de backup '{diretorio_origem}' não foi encontrada. É necessário executar o Passo 1 primeiro.")
         return

    arquivos = listar_arquivos_imagem(diretorio_origem)
    contador = 0
    
    for nome_arquivo in arquivos:
        print(f"\n--- Processando (Passo 5 - Exportação Final): {nome_arquivo} ---")
        caminho_origem = os.path.join(diretorio_origem, nome_arquivo)
        caminho_destino = os.path.join(diretorio_destino, nome_arquivo)
        
        imagem_original = ler_imagem(caminho_origem, cv2.IMREAD_COLOR)
        if imagem_original is not None:
            imagem_cinza = aplicar_escala_cinza(imagem_original)
            if imagem_cinza is None: continue
            
            imagem_suavizada = aplicar_desfoque_gaussiano(imagem_cinza)
            if imagem_suavizada is None: continue
            
            bordas_dilatadas = aplicar_canny_e_dilatacao(imagem_suavizada)
            if bordas_dilatadas is None: continue
            
            contorno_documento = encontrar_maior_contorno_documento(bordas_dilatadas)
            
            if contorno_documento is not None:
                try:
                    pontos_formatados = contorno_documento.reshape(4, 2)
                    documento_final = aplicar_transformacao_perspectiva(imagem_original, pontos_formatados)
                    
                    if documento_final is not None:
                        if salvar_imagem(caminho_destino, documento_final):
                            contador += 1
                            print(f"[+] Passo 5 concluído com sucesso para '{nome_arquivo}'.")
                except Exception as e:
                    print(f"[!] Erro ao processar transformação de perspectiva para '{nome_arquivo}': {e}")
            else:
                print(f"[!] Falha ao processar transformação final de '{nome_arquivo}': contorno do documento não encontrado.")

    print(f"\n>>> Passo 5 concluído globalmente! {contador} de {len(arquivos)} imagem(ns) finalizada(s).")

def executar_pipeline():
    """
    Controla o fluxo principal de execução da ferramenta, orquestrando as etapas de 
    processamento de imagem em uma ordem pré-definida e lidando com falhas inesperadas.
    """
    print("=" * 60)
    print(" INICIANDO PIPELINE DE PROCESSAMENTO DE DOCUMENTOS")
    print("=" * 60)

    try:
        executar_passo_1_cinza_e_backup()
        executar_passo_2_desfoque()
        executar_passo_3_bordas()
        executar_passo_4_contornos()
        executar_passo_5_transformacao_final()
    except Exception as e:
        print(f"\n[!] Ocorreu um erro crítico e inesperado durante a execução do pipeline: {e}")

    print("\n" + "=" * 60)
    print(" PIPELINE CONCLUÍDO COM SUCESSO!")
    print(" As imagens finais e retificadas estão na pasta atual.")
    print(" Os arquivos originais estão preservados na pasta 'origem/'.")
    print("=" * 60)

if __name__ == "__main__":
    executar_pipeline()