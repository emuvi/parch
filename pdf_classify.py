import os
import re
import glob
import time
import shutil
import unicodedata
import PyPDF2
from typing import Optional
from datetime import datetime
from lmstd import LMStd, ChatResponse


def get_current_time() -> str:
    """Returns the current time formatted as HH:MM:SS."""
    return datetime.now().strftime('%H:%M:%S')


def log_message(message: str) -> None:
    """Logs a message to the console with a timestamp."""
    print(f"[{get_current_time()}] {message}")


# Initialize the LM Studio client pointing to the local LM Studio server.
client = LMStd(base_url=os.environ.get("LMSTD_HOST", "http://localhost:1234"),
               api_token=os.environ.get("LMSTD_APIKEY"))


def get_classify_prompt(parent_dir: str, current_dir: str) -> str:
    """Generates the prompt instruction dynamically based on parent directory folders."""
    prompt = (
        "Você é um especialista em classificação de documentos e arquivologia.\n"
        "Sua tarefa é analisar o documento fornecido e classificá-lo em EXATAMENTE UMA das categorias listadas.\n\n"
        "### CATEGORIAS DISPONÍVEIS ###\n"
    )
    
    try:
        current_dir_name = os.path.basename(current_dir)
        dirs = []
        for entry in os.listdir(parent_dir):
            full_path = os.path.join(parent_dir, entry)
            if os.path.isdir(full_path):
                if entry != current_dir_name:
                    dirs.append(entry)
                    
        for d in sorted(dirs):
            prompt += f"- {d}\n"
            
    except Exception as e:
        log_message(f"Error reading parent directory to generate prompt: {e}")
        return ""
        
    prompt += (
        "\n### INSTRUÇÕES CRÍTICAS ###\n"
        "1. Analise o tema principal e o conteúdo do documento com cuidado.\n"
        "2. Escolha a categoria da lista acima que melhor descreve o documento.\n"
        "3. Sua resposta DEVE SER APENAS O NOME EXATO DA CATEGORIA. Não inclua absolutamente mais nada.\n"
        "4. NÃO forneça justificativas, NÃO escreva frases como 'A categoria é', e NÃO coloque pontos finais após o nome.\n"
    )
    return prompt


def extract_pdf_text(file_path: str) -> str:
    """Extracts text content from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)

            if total_pages > 99:
                mid_start = (total_pages // 2) - 16
                pages_to_extract = sorted(set(
                    list(range(33)) +
                    list(range(mid_start, mid_start + 33)) +
                    list(range(total_pages - 33, total_pages))
                ))
            else:
                pages_to_extract = list(range(total_pages))

            for page_num in pages_to_extract:
                page = reader.pages[page_num]
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        log_message(f"Error reading PDF {file_path}: {e}")
    return text.strip()


def query_model_classification(pdf_text: str, prompt: str) -> str:
    """Queries the local AI model for classification based on the extracted text."""
    system_prompt = (
        "You are an expert automated document classification system. "
        "You must rigidly follow the instructions and output ONLY the exact category name requested. "
        "Do not provide any explanations, reasoning, or conversational text."
    )

    full_prompt = f"{prompt}\n\n### TEXTO DO DOCUMENTO ###\n{pdf_text}\n\n### SUA RESPOSTA (APENAS A CATEGORIA EXATA) ###\n"

    try:
        response: ChatResponse = client.chat(
            system_prompt=system_prompt,
            input_data=full_prompt,
            temperature=0.0,
        )
        content: Optional[str] = None
        if "output" in response:
            for item in response.get("output", []):
                if item.get("type") == "message":
                    content = item.get("content")
                    break

        if content:
            return content.strip()
        return ""
    except Exception as e:
        log_message(f"Error calling Local LM Studio API: {e}")
        raise ConnectionError("API Error 500")


def normalize_text(text: str) -> str:
    """Normalize text to lowercase, strip accents, and remove punctuation."""
    normalized = unicodedata.normalize('NFD', text)
    normalized = ''.join(
        ch for ch in normalized if unicodedata.category(ch) != 'Mn')
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def find_target_directory(parent_dir: str, current_dir: str, llm_response: str) -> Optional[str]:
    """Finds the most appropriate target directory based on the LLM response."""
    if not llm_response:
        return None

    normalized_response = normalize_text(llm_response)
    normalized_response_words = set(normalized_response.split())

    best_score = 0
    best_match = None
    current_dir_name = os.path.basename(current_dir)

    try:
        for entry in os.listdir(parent_dir):
            if entry == current_dir_name:
                continue

            full_path = os.path.join(parent_dir, entry)
            if not os.path.isdir(full_path):
                continue

            normalized_entry = normalize_text(entry)
            score = 0
            
            # Exact match is best
            if normalized_entry == normalized_response:
                score += 200
            
            # Substring match
            if normalized_entry in normalized_response:
                score += 100
            if normalized_response in normalized_entry:
                score += 80

            common_words = normalized_response_words.intersection(
                set(normalized_entry.split()))
            score += len(common_words) * 10

            if score > best_score:
                best_score = score
                best_match = full_path

            if score >= 200:
                return full_path
    except Exception as e:
        log_message(f"Error reading parent directory: {e}")

    return best_match if best_score > 0 else None


def main() -> None:
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    prompt_text = get_classify_prompt(parent_dir, current_dir)
    if not prompt_text:
        log_message("Could not generate instruction prompt. Aborting.")
        return

    print("This script will continuously monitor the current folder for new PDF files (excluding 'RAND*') to classify and move.")
    print("It will classify files into the subfolders of the parent directory.")
    proceed = input("Do you want to proceed? (yes/no): ").strip().lower()
    if proceed != 'yes':
        log_message("Operation canceled.")
        return

    log_message("Starting continuous classification watcher. Press Ctrl+C to stop.")
    print("-" * 90)

    try:
        waiting = False
        total_processed_files = 0
        total_failed_files = 0
        while True:
            try:
                # Refresh prompt text occasionally in case folders changed
                prompt_text = get_classify_prompt(parent_dir, current_dir)
                
                pdf_files = sorted(glob.glob("*.pdf"))
                # Process only files that do NOT start with "RAND" and have not been marked as unreadable/unclassified/error
                files_to_process = []
                for f in pdf_files:
                    if f.upper().startswith("RAND"):
                        continue
                    if "(UNREADABLE)" in f or "(UNCLASSIFIED)" in f or "(ERROR)" in f:
                        continue
                    files_to_process.append(f)

                if not files_to_process:
                    # Sleep for 5 seconds before checking again if no files are found
                    print(
                        f"\r[{get_current_time()}] ⏳ Waiting for new PDF files... (Checking every 5s)", end="", flush=True)
                    waiting = True
                    time.sleep(5)
                    continue

                if waiting:
                    print()  # Move to the next line so we don't overwrite the waiting message
                    waiting = False

                processed_files = 0
                failed_files = 0

                for file in files_to_process:
                    try:
                        log_message(f"[{file}] -> Extracting text...")
                        text = extract_pdf_text(file)

                        if not text:
                            log_message(
                                f"[{file}] -> Failed: Could not extract text from the PDF.")
                            failed_files += 1
                            # Rename or move the file to avoid infinite loops on unreadable PDFs
                            base_name, ext = os.path.splitext(file)
                            error_name = f"{base_name} (UNREADABLE){ext}"
                            try:
                                os.rename(file, error_name)
                                log_message(
                                    f"[{file}] -> Renamed to {error_name} to prevent looping.")
                                for related_file in os.listdir(current_dir):
                                    if related_file != file and os.path.splitext(related_file)[0] == base_name:
                                        rel_ext = os.path.splitext(related_file)[1]
                                        try:
                                            os.rename(related_file, f"{base_name} (UNREADABLE){rel_ext}")
                                        except Exception:
                                            pass
                            except Exception as e:
                                log_message(
                                    f"[{file}] -> Could not rename unreadable file: {e}")
                            continue

                        text = text[:4000]

                        log_message(
                            f"[{file}] -> Calling LLM for classification...")
                        start_time = time.time()

                        llm_response = query_model_classification(
                            text, prompt_text)

                        elapsed_time = time.time() - start_time
                        log_message(
                            f"[{file}] -> LLM call completed in {elapsed_time:.2f}s")
                        print(f"  - LLM Response: {llm_response}")

                        target_dir = find_target_directory(
                            parent_dir, current_dir, llm_response)

                        if target_dir:
                            print(
                                f"  - Matched Target Folder: {os.path.basename(target_dir)}")
                            target_path = os.path.join(target_dir, file)

                            if os.path.exists(target_path):
                                base_name, ext = os.path.splitext(file)
                                counter = 2
                                while True:
                                    new_file_name = f"{base_name} ({counter}){ext}"
                                    new_target_path = os.path.join(
                                        target_dir, new_file_name)
                                    if not os.path.exists(new_target_path):
                                        target_path = new_target_path
                                        break
                                    counter += 1

                            try:
                                shutil.move(os.path.join(
                                    current_dir, file), target_path)
                                log_message(
                                    f"[{file}] -> Success! Moved to: {target_path}")
                                
                                # Move related files
                                orig_base_name = os.path.splitext(file)[0]
                                final_base_name = os.path.splitext(os.path.basename(target_path))[0]
                                
                                for related_file in os.listdir(current_dir):
                                    if related_file == file:
                                        continue
                                    rel_base, rel_ext = os.path.splitext(related_file)
                                    if rel_base == orig_base_name:
                                        related_target = os.path.join(target_dir, f"{final_base_name}{rel_ext}")
                                        try:
                                            shutil.move(os.path.join(current_dir, related_file), related_target)
                                            log_message(f"[{related_file}] -> Success! Moved related file to: {related_target}")
                                        except Exception as e:
                                            log_message(f"[{related_file}] -> Error moving related file: {e}")

                                processed_files += 1
                            except Exception as e:
                                log_message(
                                    f"[{file}] -> Error moving file: {e}")
                                failed_files += 1
                                # Sleep briefly if there was an error to avoid rapid failing loops
                                time.sleep(2)
                        else:
                            log_message(
                                f"[{file}] -> Could not determine target folder from LLM response.")
                            # Rename the file to prevent it from being processed over and over again
                            base_name, ext = os.path.splitext(file)
                            error_name = f"{base_name} (UNCLASSIFIED){ext}"
                            try:
                                os.rename(file, error_name)
                                log_message(
                                    f"[{file}] -> Renamed to {error_name} to prevent looping.")
                                for related_file in os.listdir(current_dir):
                                    if related_file != file and os.path.splitext(related_file)[0] == base_name:
                                        rel_ext = os.path.splitext(related_file)[1]
                                        try:
                                            os.rename(related_file, f"{base_name} (UNCLASSIFIED){rel_ext}")
                                        except Exception:
                                            pass
                            except Exception as e:
                                log_message(
                                    f"[{file}] -> Could not rename unclassified file: {e}")
                            failed_files += 1
                    except ConnectionError as ce:
                        log_message(f"[{file}] -> API Error: {ce}. Skipping to next file.")
                        failed_files += 1
                        continue
                    except Exception as e:
                        log_message(
                            f"[{file}] -> Unexpected error while processing file: {e}")
                        import traceback
                        traceback.print_exc()
                        try:
                            base_name, ext = os.path.splitext(file)
                            error_name = f"{base_name} (ERROR){ext}"
                            os.rename(file, error_name)
                            log_message(
                                f"[{file}] -> Renamed to {error_name} to prevent looping on this file.")
                            for related_file in os.listdir(current_dir):
                                if related_file != file and os.path.splitext(related_file)[0] == base_name:
                                    rel_ext = os.path.splitext(related_file)[1]
                                    try:
                                        os.rename(related_file, f"{base_name} (ERROR){rel_ext}")
                                    except Exception:
                                        pass
                        except Exception as rename_e:
                            log_message(
                                f"[{file}] -> Could not rename file after error: {rename_e}")
                        failed_files += 1
                    finally:
                        print(f"  -> Cycle Totals: {processed_files} success, {failed_files} fails | Overall: {total_processed_files + processed_files} success, {total_failed_files + failed_files} fails\n")

                if processed_files > 0 or failed_files > 0:
                    total_processed_files += processed_files
                    total_failed_files += failed_files
                    print(f"\n[{get_current_time()}] Process cycle completed. {processed_files} file(s) classified. {failed_files} file(s) failed.")
                    print(f"[{get_current_time()}] Overall Session Totals: {total_processed_files} success, {total_failed_files} fails.")

                # Sleep briefly after processing a batch
                time.sleep(2)

            except Exception as e:
                log_message(f"Unexpected error in the main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)

    except KeyboardInterrupt:
        print(f"\n[{get_current_time()}] Continuous monitoring stopped by user.")


if __name__ == "__main__":
    main()
