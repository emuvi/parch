import subprocess
import sys
import os

def executar_pipeline():
    """
    Chama os 5 scripts de processamento sequencialmente.
    """
    
    # Lista com o nome dos arquivos e uma descrição para o log
    passos = [
        ("fix_docs_step01.py", "Passo 1: Backup na pasta 'origem' e Escala de Cinza"),
        ("fix_docs_step02.py", "Passo 2: Redução de Ruído (Desfoque 7x7)"),
        ("fix_docs_step03.py", "Passo 3: Detecção de Bordas (Canny + Dilatação)"),
        ("fix_docs_step04.py", "Passo 4: Detecção e Filtragem de Contornos"),
        ("fix_docs_step05.py", "Passo 5: Isolamento, Retificação e Exportação Final")
    ]

    print("=" * 60)
    print(" INICIANDO PIPELINE DE PROCESSAMENTO DE DOCUMENTOS")
    print("=" * 60)

    for script_nome, descricao in passos:
        # Verifica se o arquivo do passo realmente existe na pasta antes de tentar rodar
        if not os.path.exists(script_nome):
            print(f"\n[ERRO] O arquivo '{script_nome}' não foi encontrado na pasta atual.")
            print("Certifique-se de que todos os 5 scripts estão salvos no mesmo local.")
            return

        print(f"\n>>> Executando {descricao} ({script_nome})...")
        
        try:
            # sys.executable garante que usaremos o mesmo ambiente Python que está rodando este script agora
            subprocess.run([sys.executable, script_nome], check=True)
            
        except subprocess.CalledProcessError:
            print(f"\n[ERRO FATAL] O pipeline foi interrompido porque o '{script_nome}' apresentou falhas.")
            return

    print("\n" + "=" * 60)
    print(" PIPELINE CONCLUÍDO COM SUCESSO!")
    print(" As imagens finais e retificadas estão na pasta atual.")
    print(" Os arquivos originais estão preservados na pasta 'origem/'.")
    print("=" * 60)

if __name__ == "__main__":
    executar_pipeline()