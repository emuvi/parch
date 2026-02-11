import hashlib
import os
import glob

def gerar_md5(caminho_arquivo):
    """Lê o arquivo em blocos para não sobrecarregar a memória e gera o hash MD5."""
    hash_md5 = hashlib.md5()
    with open(caminho_arquivo, "rb") as f:
        # Lê o arquivo em pedaços de 4KB
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def renomear_pdfs():
    # Lista todos os arquivos .pdf na pasta atual
    arquivos_pdf = glob.glob("*.pdf")
    
    if not arquivos_pdf:
        print("Nenhum arquivo PDF encontrado na pasta.")
        return

    print(f"Encontrados {len(arquivos_pdf)} arquivos. Iniciando processamento...")

    for arquivo in arquivos_pdf:
        try:
            # 1. Gera o hash baseado no conteúdo
            novo_nome_base = gerar_md5(arquivo)
            novo_nome = f"{novo_nome_base}.pdf"

            # 2. Verifica se o arquivo já tem o nome correto para evitar erros
            if arquivo == novo_nome:
                print(f"Pulando: {arquivo} já está renomeado.")
                continue

            # 3. Renomeia o arquivo
            os.rename(arquivo, novo_nome)
            print(f"Sucesso: {arquivo} -> {novo_nome}")
            
        except Exception as e:
            print(f"Erro ao processar {arquivo}: {e}")

if __name__ == "__main__":
    renomear_pdfs()