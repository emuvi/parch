import os
import random
import shutil

# Configuração do script
total_to_get = 300
file_extension = ".pdf"
root_dir = os.getcwd()
get_on_dir = os.path.join(root_dir, 'body')
destination_dir = root_dir

# Verifica se o diretório de origem existe
if not os.path.isdir(get_on_dir):
    print(f"Erro: O diretório '{get_on_dir}' não foi encontrado.")
    exit()

print(f"Procurando por arquivos '{file_extension}' em '{get_on_dir}' e suas subpastas...")

# 2. Percorre o diretório de origem e coleta todos os arquivos com a extensão definida
files_found = []
for dirpath, _, filenames in os.walk(get_on_dir):
    for filename in filenames:
        if filename.lower().endswith(file_extension):
            full_path = os.path.join(dirpath, filename)
            files_found.append(full_path)

print(f"Encontrados {len(files_found)} arquivos com extensão '{file_extension}'.")

# 3. Verifica o número de arquivos e os seleciona
if not files_found:
    print(f"Nenhum arquivo {file_extension} encontrado. O script será encerrado.")
    exit()


if len(files_found) < total_to_get:
    print(f"Aviso: Foram encontrados menos de {total_to_get} arquivos. Sorteando todos os {len(files_found)} arquivos encontrados.")
    selected_files = files_found
else:
    print(f"Sorteando {total_to_get} arquivos {file_extension}...")
    selected_files = random.sample(files_found, total_to_get)

# 4. Copia os arquivos selecionados para o diretório raiz
print(f"\nCopiando {len(selected_files)} arquivos sorteados para '{destination_dir}'...")
for file_path in selected_files:
    filename = os.path.basename(file_path)
    dest_path = os.path.join(destination_dir, filename)

    # Verifica se o arquivo já existe e renomeia se necessário
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            new_filename = f"{base}_{counter}{ext}"
            dest_path = os.path.join(destination_dir, new_filename)
            counter += 1

    shutil.copy(file_path, dest_path)

print(f"\nConcluído! {len(selected_files)} arquivos foram copiados com sucesso.")