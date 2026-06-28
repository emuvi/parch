import os
import sys
import re
import glob
import time
import PyPDF2
from datetime import datetime
from typing import Optional, List

from lmstd import LMStd, ChatResponse

# Initialize the LM Studio client pointing to the local LM Studio server.
try:
    client = LMStd(base_url=os.environ.get("LMSTD_HOST", "http://localhost:1234"),
                   api_token=os.environ.get("LMSTD_APIKEY"))
except Exception as e:
    print(f"🔴 [Error] Failed to initialize LMStd client: {e}")
    sys.exit(1)

def get_current_time() -> str:
    """Returns the current time formatted as HH:MM:SS."""
    return datetime.now().strftime('%H:%M:%S')

def log_message(message: str) -> None:
    """Logs a message to the console with a timestamp."""
    print(f"[{get_current_time()}] {message}")

def get_pages_to_extract(total_pages: int) -> List[int]:
    """Determines which pages to extract from a PDF based on total pages."""
    if total_pages > 99:
        mid_start = (total_pages // 2) - 16
        pages_to_extract = sorted(set(
            list(range(33)) +
            list(range(mid_start, mid_start + 33)) +
            list(range(total_pages - 33, total_pages))
        ))
    else:
        pages_to_extract = list(range(total_pages))
    return pages_to_extract

def extract_pdf_text(file_path: str) -> str:
    """Extracts text content from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)
            pages_to_extract = get_pages_to_extract(total_pages)
            
            for page_num in pages_to_extract:
                try:
                    page = reader.pages[page_num]
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                except Exception:
                    pass
    except Exception as e:
        log_message(f"Error reading PDF {file_path}: {e}")
    return text.strip()

def build_summary_prompt(text: str) -> str:
    """Builds the prompt string for the LLM to generate a summary."""
    truncated_text = text[:4000]
    prompt = (
        "Based on the following text extracted from a PDF, tell me what it is about "
        "in a maximum of 100 characters. Be concise and direct, providing only the summary "
        "without conversational filler. Do not use quotes or special characters that "
        "are invalid in filenames. Respond in the exact same language as the provided text, "
        "and ensure perfect spell checking on the language of the document.\n\n"
        f"### TEXT ###\n{truncated_text}"
    )
    return prompt

def get_summary_from_llm(prompt: str) -> Optional[str]:
    """Calls the Local LM Studio API to get a summary based on the prompt."""
    try:
        response: ChatResponse = client.chat(
            system_prompt="You are a helpful assistant that summarizes documents extremely concisely for filenames. Always respond in the same language as the input text and ensure perfect spelling.",
            input_data=prompt,
            temperature=0.0
        )
        content: Optional[str] = None
        if "output" in response:
            for item in response.get("output", []):
                if item.get("type") == "message":
                    content = item.get("content")
                    break

        if content:
            return content.strip()
        return None
    except Exception as e:
        log_message(f"Error calling Local LM Studio API: {e}")
        raise ConnectionError("API Error")

def sanitize_filename(summary: str) -> Optional[str]:
    """Cleans up the generated summary to be a valid and safe filename."""
    try:
        if summary.startswith("```"):
            summary = summary.split('\n', 1)[-1]
            if summary.endswith("```"):
                summary = summary[:-3]
        summary = summary.strip()

        if len(summary) > 100:
            summary = summary[:100].strip()

        new_base_name = re.sub(r'[\\/*?:"<>|\n\r\t]', "_", summary)
        new_base_name = re.sub(r'_{2,}', "_", new_base_name).strip(" _.")

        if not new_base_name:
            return None

        return new_base_name
    except Exception as e:
        log_message(f"Error sanitizing filename: {e}")
        return None

def get_unique_new_path(current_dir: str, new_base_name: str, original_path: str) -> Optional[str]:
    """Generates a unique file path by appending a counter if the file already exists."""
    try:
        new_file_name = f"{new_base_name}.pdf"
        new_path = os.path.join(current_dir, new_file_name)

        if os.path.exists(new_path) and original_path.lower() != new_path.lower():
            counter = 2
            while True:
                new_file_name = f"{new_base_name} ({counter}).pdf"
                new_path = os.path.join(current_dir, new_file_name)
                if not os.path.exists(new_path) or original_path.lower() == new_path.lower():
                    break
                counter += 1
        return new_path
    except Exception as e:
        log_message(f"Error generating unique new path: {e}")
        return None

def mark_file_with_suffix(file: str, current_dir: str, suffix: str) -> None:
    """Renames a file and its sidecars with a specific suffix to avoid infinite processing loops."""
    try:
        base_name, ext = os.path.splitext(file)
        error_name = f"{base_name} {suffix}{ext}"
        os.rename(file, error_name)
        log_message(f"[{file}] -> Renamed to {error_name} to prevent looping.")
        
        # Rename sidecar files
        for related_file in os.listdir(current_dir):
            if related_file != error_name and related_file != file and os.path.splitext(related_file)[0] == base_name:
                rel_ext = os.path.splitext(related_file)[1]
                try:
                    os.rename(related_file, f"{base_name} {suffix}{rel_ext}")
                except Exception:
                    pass
    except Exception as e:
        log_message(f"[{file}] -> Could not append suffix {suffix} to file: {e}")

def main() -> None:
    current_dir = os.getcwd()

    print("This script will continuously monitor the current folder for new PDF files (excluding 'RAND*')")
    print("to summarize their content and rename them (and their sidecar files).")
    proceed = input("Do you want to proceed? (yes/no): ").strip().lower()
    if proceed != 'yes':
        log_message("Operation canceled.")
        return

    log_message("Starting continuous summary watcher. Press Ctrl+C to stop.")
    print("-" * 90)

    try:
        waiting = False
        total_processed_files = 0
        total_failed_files = 0
        
        while True:
            try:
                pdf_files = sorted(glob.glob("*.pdf"))
                files_to_process = []
                for f in pdf_files:
                    if f.upper().startswith("RAND"):
                        continue
                    if "(UNREADABLE)" in f or "(SUMMARY_FAILED)" in f or "(ERROR)" in f:
                        continue
                    files_to_process.append(f)

                if not files_to_process:
                    print(f"\r[{get_current_time()}] ⏳ Waiting for new PDF files... (Checking every 5s)", end="", flush=True)
                    waiting = True
                    time.sleep(5)
                    continue

                if waiting:
                    print()
                    waiting = False

                processed_files = 0
                failed_files = 0

                for file in files_to_process:
                    try:
                        log_message(f"[{file}] -> Extracting text...")
                        text = extract_pdf_text(file)

                        if not text:
                            log_message(f"[{file}] -> Failed: Could not extract text from the PDF.")
                            failed_files += 1
                            mark_file_with_suffix(file, current_dir, "(UNREADABLE)")
                            continue

                        log_message(f"[{file}] -> Calling LLM for summary...")
                        start_time = time.time()
                        
                        prompt = build_summary_prompt(text)
                        llm_response = get_summary_from_llm(prompt)

                        elapsed_time = time.time() - start_time
                        log_message(f"[{file}] -> LLM call completed in {elapsed_time:.2f}s")

                        if not llm_response:
                            log_message(f"[{file}] -> Failed: LLM returned empty or invalid response.")
                            failed_files += 1
                            mark_file_with_suffix(file, current_dir, "(SUMMARY_FAILED)")
                            continue
                            
                        print(f"  - LLM Summary: {llm_response}")

                        new_base_name = sanitize_filename(llm_response)
                        if not new_base_name:
                            log_message(f"[{file}] -> Failed: Could not sanitize LLM response for a filename.")
                            failed_files += 1
                            mark_file_with_suffix(file, current_dir, "(SUMMARY_FAILED)")
                            continue
                            
                        new_path = get_unique_new_path(current_dir, new_base_name, file)
                        if not new_path:
                            log_message(f"[{file}] -> Failed: Could not determine unique new path.")
                            failed_files += 1
                            mark_file_with_suffix(file, current_dir, "(ERROR)")
                            continue

                        new_file_name = os.path.basename(new_path)
                        final_new_base_name = os.path.splitext(new_file_name)[0]
                        old_base_name = os.path.splitext(file)[0]

                        # Perform rename of the main PDF
                        try:
                            os.rename(file, new_path)
                            log_message(f"[{file}] -> Success! Renamed to: {new_file_name}")
                            
                            # Perform rename of sidecar files
                            for related_file in os.listdir(current_dir):
                                if related_file == file or related_file == new_file_name:
                                    continue
                                rel_base, rel_ext = os.path.splitext(related_file)
                                if rel_base == old_base_name:
                                    related_target = os.path.join(current_dir, f"{final_new_base_name}{rel_ext}")
                                    try:
                                        os.rename(related_file, related_target)
                                        log_message(f"[{related_file}] -> Success! Renamed related file to: {os.path.basename(related_target)}")
                                    except Exception as e:
                                        log_message(f"[{related_file}] -> Error renaming related file: {e}")

                            processed_files += 1
                        except Exception as e:
                            log_message(f"[{file}] -> Error renaming PDF file: {e}")
                            failed_files += 1
                            time.sleep(2)

                    except ConnectionError as ce:
                        log_message(f"[{file}] -> API Error: {ce}. Skipping to next file.")
                        failed_files += 1
                        continue
                    except Exception as e:
                        log_message(f"[{file}] -> Unexpected error while processing file: {e}")
                        import traceback
                        traceback.print_exc()
                        mark_file_with_suffix(file, current_dir, "(ERROR)")
                        failed_files += 1
                    finally:
                        print(f"  -> Cycle Totals: {processed_files} success, {failed_files} fails | Overall: {total_processed_files + processed_files} success, {total_failed_files + failed_files} fails\n")

                if processed_files > 0 or failed_files > 0:
                    total_processed_files += processed_files
                    total_failed_files += failed_files
                    print(f"\n[{get_current_time()}] Process cycle completed. {processed_files} file(s) renamed. {failed_files} file(s) failed.")
                    print(f"[{get_current_time()}] Overall Session Totals: {total_processed_files} success, {total_failed_files} fails.")

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
