import subprocess
import sys

def install_packages():
    """Instala os pacotes Python necessários para extração de documentos com OpenCV."""
    
    # Lista de pacotes essenciais para visão computacional
    packages = [
        "Pillow"
    ]
    
    print("Iniciando a instalação das bibliotecas de Visão Computacional...")
    print("-" * 50)
    
    # Atualiza o pip primeiro para evitar avisos e garantir compatibilidade
    try:
        print("Atualizando o pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("Aviso: Não foi possível atualizar o pip. Continuando com a instalação...")
        
    # Instala os pacotes listados
    for package in packages:
        try:
            print(f"\nInstalando '{package}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Sucesso: '{package}' instalado corretamente.")
        except subprocess.CalledProcessError as e:
            print(f"\nERRO: Falha ao instalar '{package}'. Detalhes: {e}")
            return False
            
    print("-" * 50)
    print("Todas as bibliotecas Python foram instaladas com sucesso e o ambiente está pronto!")
    return True

if __name__ == "__main__":
    install_packages()
    print("\nPressione Enter para sair...")
    input()