import os
import sys
import quopri
from datetime import datetime

def get_current_time():
    """
    Returns the current time formatted as [HH:MM:SS] for logging purposes.
    
    Returns:
        str: Current time in string format.
    """
    return f"[{datetime.now().strftime('%H:%M:%S')}]"

def log_msg(emoji, category, function_name, message):
    """
    Prints a formatted log message with timestamp, emoji, category, function name, and message.
    
    Args:
        emoji (str): The emoji indicating the message type.
        category (str): The category of the message (e.g., LOG, STEP, SUCCESS, ERROR).
        function_name (str): The name of the function where the log is generated.
        message (str): The content of the log message.
    """
    print(f"{get_current_time()} {emoji} [{category}] [{function_name}] {message}")

def decode_qp(value):
    """
    Decodes a quoted-printable string to UTF-8.
    
    Args:
        value (str): The quoted-printable string to decode.
        
    Returns:
        str: The decoded UTF-8 string or the original value if decoding fails.
    """
    try:
        return quopri.decodestring(value.encode('utf-8')).decode('utf-8')
    except Exception as e:
        log_msg("🔴", "ERROR", "decode_qp", f"Failed to decode '{value}': {str(e)}. Using raw value.")
        return value

def _unfold_lines(raw_lines):
    """
    Unfolds vCard lines where continuations start with a space or tab.
    
    Args:
        raw_lines (list of str): The raw lines read from the VCF file.
        
    Returns:
        list of str: The unfolded lines.
    """
    lines = []
    for line in raw_lines:
        line_stripped = line.rstrip('\r\n')
        if line_stripped.startswith(' ') or line_stripped.startswith('\t'):
            if lines:
                lines[-1] += line_stripped[1:]
        else:
            lines.append(line_stripped)
    return lines

def _combine_quoted_printable(lines):
    """
    Combines lines that were broken due to quoted-printable soft line breaks '='.
    
    Args:
        lines (list of str): The unfolded lines from the VCF file.
        
    Returns:
        list of str: The lines with quoted-printable soft breaks combined.
    """
    combined = []
    qp_buffer = ""
    for line in lines:
        if qp_buffer:
            line = qp_buffer + line
            qp_buffer = ""
            
        if 'ENCODING=QUOTED-PRINTABLE' in line and line.endswith('='):
            qp_buffer = line[:-1]
        else:
            combined.append(line)
            
    if qp_buffer:
        combined.append(qp_buffer)
    return combined

def _parse_name(value):
    """
    Parses a structured vCard name into a readable string.
    
    Args:
        value (str): The structured name string separated by semicolons.
        
    Returns:
        str: A readable representation of the structured name.
    """
    name_parts = value.split(';')
    desc_parts = []
    labels = ["Sobrenome", "Nome", "Nome do Meio", "Prefixo", "Sufixo"]
    
    for label, part in zip(labels, name_parts):
        if part:
            desc_parts.append(f"{label}: {part}")
            
    return " ".join(desc_parts) if desc_parts else value

def _parse_field(current_contact, key_part, value):
    """
    Parses a single vCard field and adds it to the current contact dictionary.
    
    Args:
        current_contact (dict): The dictionary representing the contact being built.
        key_part (str): The key part of the vCard line (e.g., 'TEL;TYPE=CELL').
        value (str): The value part of the vCard line.
    """
    if 'ENCODING=QUOTED-PRINTABLE' in key_part:
        value = decode_qp(value)
        
    field_name = key_part.split(';')[0].upper()
    
    if field_name == 'FN':
        current_contact['Nome Formatado'] = value
    elif field_name == 'N':
        current_contact['Nome Estruturado'] = _parse_name(value)
    elif field_name == 'TEL':
        attrs = key_part.split(';')[1:]
        desc = f"Telefone ({', '.join(attrs)})" if attrs else "Telefone"
        current_contact.setdefault('Telefones', []).append(f"{desc}: {value}")
    elif field_name == 'EMAIL':
        attrs = key_part.split(';')[1:]
        desc = f"Email ({', '.join(attrs)})" if attrs else "Email"
        current_contact.setdefault('Emails', []).append(f"{desc}: {value}")
    elif field_name == 'ORG':
        current_contact['Organização'] = value
    elif field_name == 'TITLE':
        current_contact['Cargo/Título'] = value
    elif field_name == 'ADR':
        current_contact['Endereço'] = value.replace(';', ' ').strip()
    elif field_name == 'URL':
        current_contact['Site/URL'] = value
    elif field_name == 'NOTE':
        current_contact['Anotação'] = value
    elif field_name == 'BDAY':
        current_contact['Aniversário'] = value
    elif field_name == 'PHOTO' or 'ENCODING=BASE64' in key_part or field_name == 'VERSION':
        pass  # Ignored fields
    else:
        current_contact.setdefault('Outros Campos', []).append(f"{key_part}: {value}")

def _extract_contacts(lines):
    """
    Extracts contact dictionaries from parsed vCard lines.
    
    Args:
        lines (list of str): The processed lines of the VCF file.
        
    Returns:
        list of dict: A list of dictionaries, each representing a contact.
    """
    contacts = []
    current_contact = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line == 'BEGIN:VCARD':
            current_contact = {}
        elif line == 'END:VCARD':
            if current_contact:
                contacts.append(current_contact)
        elif ':' in line:
            key_part, value = line.split(':', 1)
            _parse_field(current_contact, key_part, value)
            
    return contacts

def _write_contact(out, contact, index):
    """
    Writes a single parsed contact to the output stream.
    
    Args:
        out (file object): The output file object to write to.
        contact (dict): The dictionary containing contact information.
        index (int): The index number of the contact.
    """
    out.write(f"--- Contato {index} ---\n")
    
    if 'Nome Formatado' in contact:
        out.write(f"Nome: {contact['Nome Formatado']}\n")
    elif 'Nome Estruturado' in contact:
        out.write(f"Nome: {contact['Nome Estruturado']}\n")
        
    for key in ['Nome Estruturado', 'Organização', 'Cargo/Título', 'Endereço', 'Site/URL', 'Anotação', 'Aniversário']:
        if key in contact:
            if key == 'Nome Estruturado' and 'Nome Formatado' not in contact:
                continue
            if key != 'Nome Estruturado' or 'Nome Formatado' in contact:
                out.write(f"{key}: {contact[key]}\n")
    
    if 'Telefones' in contact:
        out.write("Telefones:\n")
        for tel in contact['Telefones']:
            out.write(f"  - {tel}\n")
        
    if 'Emails' in contact:
        out.write("Emails:\n")
        for email in contact['Emails']:
            out.write(f"  - {email}\n")
        
    if 'Outros Campos' in contact:
        out.write("Outros Campos:\n")
        for outro in contact['Outros Campos']:
            out.write(f"  - {outro}\n")
            
    out.write("\n")

def parse_vcf(input_file, output_file):
    """
    Reads a VCF file, parses its contacts, and writes them descriptively to a text file.
    
    Args:
        input_file (str): The path to the input VCF file.
        output_file (str): The path to the output text file.
        
    Raises:
        Exception: If reading, parsing, or writing fails.
    """
    log_msg("🔹", "STEP", "parse_vcf", f"Starting parsing of {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            raw_lines = f.readlines()
        log_msg("🔹", "STEP", "parse_vcf", f"Read {len(raw_lines)} lines from {input_file}")
            
        lines = _unfold_lines(raw_lines)
        combined_lines = _combine_quoted_printable(lines)
        contacts = _extract_contacts(combined_lines)
        log_msg("🔹", "STEP", "parse_vcf", f"Extracted {len(contacts)} contacts")
        
        with open(output_file, 'w', encoding='utf-8') as out:
            out.write(f"Total de Contatos: {len(contacts)}\n")
            out.write("="*50 + "\n\n")
            for i, contact in enumerate(contacts, 1):
                _write_contact(out, contact, i)
        log_msg("✅", "SUCCESS", "parse_vcf", f"Successfully wrote parsed contacts to {output_file}")
    except Exception as e:
        log_msg("🔴", "ERROR", "parse_vcf", f"Failed to parse {input_file}: {str(e)}")
        raise

def print_summary(total, successes, failures):
    """
    Prints a visual summary box with Unicode drawing characters.
    
    Args:
        total (int): Total number of files processed.
        successes (int): Number of successfully processed files.
        failures (int): Number of failed file processings.
    """
    box_width = 50
    title = "Processing Summary"
    padding = (box_width - len(title) - 2) // 2
    
    print(f"╔{'═' * (box_width - 2)}╗")
    print(f"║{' ' * padding}{title}{' ' * (box_width - 2 - padding - len(title))}║")
    print(f"╠{'═' * (box_width - 2)}╣")
    
    total_line = f"Total Processed: {total}"
    success_line = f"Successes:       {successes}"
    failure_line = f"Failures:        {failures}"
    
    print(f"║ {total_line:<{box_width-4}} ║")
    print(f"║ {success_line:<{box_width-4}} ║")
    print(f"║ {failure_line:<{box_width-4}} ║")
    print(f"╚{'═' * (box_width - 2)}╝")

def main():
    """
    Main function to find all VCF files in the current directory, process them, and log the results.
    
    Returns:
        int: 0 if all files were processed successfully or no files were found, 1 if any failures occurred.
    """
    log_msg("🔹", "STEP", "main", "Starting batch processing of VCF files")
    
    vcf_files = [f for f in os.listdir('.') if f.lower().endswith('.vcf')]
    
    if not vcf_files:
        log_msg("ℹ️", "LOG", "main", "No .vcf files found in the current directory")
        print_summary(0, 0, 0)
        return 0
        
    total_files = len(vcf_files)
    successes = 0
    failures = 0
    
    for idx, input_vcf in enumerate(vcf_files, 1):
        log_msg("🔹", "STEP", "main", f"Processing item {idx} of {total_files}")
        
        output_txt = os.path.splitext(input_vcf)[0] + '.txt'
        log_msg("ℹ️", "LOG", "main", f"Processing: {input_vcf} -> {output_txt}")
        
        try:
            parse_vcf(input_vcf, output_txt)
            successes += 1
            log_msg("✅", "SUCCESS", "main", f"Processed {input_vcf}")
        except Exception as e:
            failures += 1
            log_msg("🔴", "ERROR", "main", f"Failed processing {input_vcf}: {str(e)}")
            
    log_msg("🔹", "STEP", "main", "Batch processing completed")
    print_summary(total_files, successes, failures)
    
    return 1 if failures > 0 else 0

if __name__ == '__main__':
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
