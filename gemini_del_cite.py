import re
import pyperclip

def del_citations(text):
    text = re.sub(r'\[cite_start\]', '', text)
    text = re.sub(r'\[cite:\s*\d+(?:\s*,\s*\d+)*\]', '', text)
    return text

def main():
    origin = pyperclip.paste()

    if not origin:
        print("Clipboard is empty.")
        return

    print("Origin on Clipboard:")
    print("---------------------------")
    print(origin)

    cleaned = del_citations(origin)

    pyperclip.copy(cleaned)

    print("\nCleaned on Clipboard:")
    print("----------------------------------------------------------------")
    print(cleaned)

if __name__ == "__main__":
    main()