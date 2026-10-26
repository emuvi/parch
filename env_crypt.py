#!/usr/bin/env python3
"""Encrypt and decrypt `.env` files using Python's native cryptographic primitives.

Inspects the current working directory and performs authenticated encryption or
decryption using PBKDF2-HMAC-SHA256 key derivation, a SHAKE-256 stream cipher,
and Encrypt-then-MAC (HMAC-SHA256) authentication:
- Both `.env` and `.env-crypt` exist: performs no file modifications.
- Only `.env` exists: prompts for a password and writes the encrypted `.env-crypt`.
- Only `.env-crypt` exists: prompts for a password, verifies integrity, and restores `.env`.

Attributes:
    ENV_PATH (Path): Default relative path for the plaintext environment file (`.env`).
    CRYPT_PATH (Path): Default relative path for the encrypted environment file (`.env-crypt`).
    SALT_SIZE (int): Byte length of the random PBKDF2 salt (16 bytes).
    NONCE_SIZE (int): Byte length of the random SHAKE-256 stream nonce (16 bytes).
    KEY_SIZE (int): Byte length of each derived cryptographic key (32 bytes / 256 bits).
    TAG_SIZE (int): Byte length of the HMAC-SHA256 authentication tag (32 bytes).
    HEADER_SIZE (int): Combined byte length of salt, nonce, and authentication tag (64 bytes).
    PBKDF2_ITERATIONS (int): Iteration count for PBKDF2-HMAC-SHA256 key derivation (600,000).
    HASH_ALGORITHM (str): Digest algorithm name used for PBKDF2 and HMAC (`sha256`).
"""

from __future__ import annotations

import base64
from datetime import datetime
import getpass
import hashlib
import hmac
import secrets
import sys
from pathlib import Path

ENV_PATH = Path(".env")
CRYPT_PATH = Path(".env-crypt")

SALT_SIZE = 16
NONCE_SIZE = 16
KEY_SIZE = 32
TAG_SIZE = 32
HEADER_SIZE = SALT_SIZE + NONCE_SIZE + TAG_SIZE
PBKDF2_ITERATIONS = 600_000
HASH_ALGORITHM = "sha256"


def get_current_time() -> str:
    """Return the current local time formatted as `HH:MM:SS`.

    Returns:
        str: Current local timestamp in 24-hour `HH:MM:SS` format.
    """
    return datetime.now().strftime("%H:%M:%S")


def log_message(
    emoji: str,
    category: str,
    function_name: str,
    message: str,
    *,
    is_error: bool = False,
) -> None:
    """Format and print a standardized timestamped log entry.

    Args:
        emoji (str): Visual status indicator emoji (`ℹ️`, `🔹`, `✅`, or `🔴`).
        category (str): Log category label (`LOG`, `STEP`, `SUCCESS`, or `ERROR`).
        function_name (str): Name of the function or execution phase emitting the log.
        message (str): Descriptive log message content.
        is_error (bool): Whether to write the formatted entry to `sys.stderr` instead
            of `sys.stdout`. Defaults to `False`.
    """
    stream = sys.stderr if is_error else sys.stdout
    print(
        f"[{get_current_time()}] {emoji} [{category}] [{function_name}] {message}",
        file=stream,
    )


def log_info(function_name: str, message: str) -> None:
    """Emit a general informational log entry (`ℹ️ [LOG]`) to standard output.

    Args:
        function_name (str): Name of the calling function or cycle.
        message (str): Informational message to record.
    """
    log_message("ℹ️", "LOG", function_name, message)


def log_step(function_name: str, message: str) -> None:
    """Emit a step execution log entry (`🔹 [STEP]`) to standard output.

    Args:
        function_name (str): Name of the function or step starting or progressing.
        message (str): Step status description and relevant runtime parameters.
    """
    log_message("🔹", "STEP", function_name, message)


def log_success(function_name: str, message: str) -> None:
    """Emit a step completion log entry (`✅ [SUCCESS]`) to standard output.

    Args:
        function_name (str): Name of the completed function or operation.
        message (str): Completion details and result metrics.
    """
    log_message("✅", "SUCCESS", function_name, message)


def log_error(function_name: str, message: str) -> None:
    """Emit an error log entry (`🔴 [ERROR]`) to standard error.

    Args:
        function_name (str): Name of the function or step where the failure occurred.
        message (str): Actionable diagnostic message explaining what failed, why,
            and how to resolve it.
    """
    log_message("🔴", "ERROR", function_name, message, is_error=True)


def _derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """Derive independent 256-bit encryption and MAC keys using PBKDF2-HMAC-SHA256.

    Args:
        password (str): User-supplied password string.
        salt (bytes): Random cryptographic salt of length `SALT_SIZE`.

    Returns:
        tuple[bytes, bytes]: A 2-tuple `(enc_key, mac_key)` containing the 32-byte
            symmetric encryption key and 32-byte HMAC authentication key.

    Raises:
        UnicodeEncodeError: If `password` cannot be encoded as UTF-8.
        ValueError: If key derivation parameters are invalid.
    """
    key_material = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=KEY_SIZE * 2,
    )
    return key_material[:KEY_SIZE], key_material[KEY_SIZE:]


def _xor_keystream(data: bytes, enc_key: bytes, nonce: bytes) -> bytes:
    """XOR byte data with a pseudorandom keystream generated via SHAKE-256.

    Args:
        data (bytes): Input plaintext or ciphertext byte sequence.
        enc_key (bytes): 32-byte symmetric encryption key.
        nonce (bytes): 16-byte random per-encryption nonce.

    Returns:
        bytes: XOR-transformed output byte sequence of the same length as `data`,
            or `b""` when `data` is empty.

    Raises:
        TypeError: If `data`, `enc_key`, or `nonce` is not a bytes-like object.
    """
    if not data:
        return b""
    keystream = hashlib.shake_256(enc_key + nonce).digest(len(data))
    return bytes(a ^ b for a, b in zip(data, keystream))


def _compute_mac(mac_key: bytes, salt: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Compute an HMAC-SHA256 authentication tag over salt, nonce, and ciphertext.

    Args:
        mac_key (bytes): 32-byte MAC key derived from the password.
        salt (bytes): 16-byte random salt prefix.
        nonce (bytes): 16-byte random stream nonce.
        ciphertext (bytes): Encrypted payload bytes.

    Returns:
        bytes: 32-byte binary HMAC-SHA256 authentication tag.

    Raises:
        TypeError: If any input argument is not a valid bytes-like object.
    """
    return hmac.new(mac_key, salt + nonce + ciphertext, hashlib.sha256).digest()


def _unpack_payload(encoded_payload: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    """Decode a Base64 payload and split it into salt, nonce, tag, and ciphertext.

    Args:
        encoded_payload (bytes): Base64-encoded bytes read from `.env-crypt`.

    Returns:
        tuple[bytes, bytes, bytes, bytes]: A 4-tuple `(salt, nonce, tag, ciphertext)`
            extracted from the decoded binary payload.

    Raises:
        ValueError: If `encoded_payload` contains invalid Base64 data or decodes
            to fewer than `HEADER_SIZE` bytes.
    """
    try:
        payload = base64.b64decode(encoded_payload.strip(), validate=True)
    except Exception as exc:
        raise ValueError(
            f"Base64 decoding failed: {exc}. "
            "Why: '.env-crypt' contains non-base64 characters or is corrupted. "
            "Fix: Restore a valid '.env-crypt' file from version control or re-encrypt '.env'."
        ) from exc

    if len(payload) < HEADER_SIZE:
        raise ValueError(
            f"Payload too short ({len(payload)} bytes < expected minimum {HEADER_SIZE} bytes). "
            "Why: '.env-crypt' is truncated or incomplete. "
            "Fix: Restore the complete '.env-crypt' file and retry."
        )

    salt = payload[:SALT_SIZE]
    nonce_end = SALT_SIZE + NONCE_SIZE
    nonce = payload[SALT_SIZE:nonce_end]
    tag = payload[nonce_end:HEADER_SIZE]
    ciphertext = payload[HEADER_SIZE:]
    return salt, nonce, tag, ciphertext


def encrypt_data(plaintext: bytes, password: str) -> bytes:
    """Encrypt plaintext bytes using Encrypt-then-MAC and return Base64-encoded output.

    Generates a fresh random 16-byte salt and 16-byte nonce, derives encryption
    and MAC keys via PBKDF2-HMAC-SHA256, encrypts `plaintext` with a SHAKE-256
    keystream, and appends an HMAC-SHA256 tag over `salt + nonce + ciphertext`.

    Args:
        plaintext (bytes): Raw plaintext bytes to encrypt.
        password (str): Password used to derive encryption and authentication keys.

    Returns:
        bytes: Base64-encoded payload containing `salt + nonce + tag + ciphertext`.

    Raises:
        Exception: If key derivation, keystream encryption, or MAC generation fails.
    """
    salt = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    enc_key, mac_key = _derive_keys(password, salt)

    ciphertext = _xor_keystream(plaintext, enc_key, nonce)
    tag = _compute_mac(mac_key, salt, nonce, ciphertext)

    payload = salt + nonce + tag + ciphertext
    return base64.b64encode(payload)


def decrypt_data(encoded_payload: bytes, password: str) -> bytes:
    """Verify the HMAC-SHA256 authentication tag and decrypt a Base64 payload.

    Args:
        encoded_payload (bytes): Base64-encoded encrypted payload bytes.
        password (str): Password used to derive decryption and MAC verification keys.

    Returns:
        bytes: Decrypted plaintext bytes.

    Raises:
        ValueError: If `encoded_payload` is malformed or the HMAC tag does not match
            the derived authentication key.
        Exception: If an unexpected cryptographic error occurs during decryption.
    """
    salt, nonce, tag, ciphertext = _unpack_payload(encoded_payload)
    enc_key, mac_key = _derive_keys(password, salt)
    expected_tag = _compute_mac(mac_key, salt, nonce, ciphertext)

    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError(
            "HMAC authentication failed. "
            "Why: The provided password is incorrect or '.env-crypt' has been modified. "
            "Fix: Re-run the script and enter the exact password used during encryption."
        )

    return _xor_keystream(ciphertext, enc_key, nonce)


def prompt_password(prompt_text: str) -> str:
    """Prompt the user securely for a non-empty password without echoing input.

    Args:
        prompt_text (str): Prompt message displayed on the terminal.

    Returns:
        str: Non-empty password string entered by the user.

    Raises:
        ValueError: If the user cancels input (`EOFError` or `KeyboardInterrupt`)
            or submits an empty password.
    """
    try:
        password = getpass.getpass(prompt_text)
    except (EOFError, KeyboardInterrupt) as exc:
        raise ValueError(
            "Password input cancelled by user. "
            "Why: Received EOF or interrupt signal. "
            "Fix: Re-run the script and provide a password when prompted."
        ) from exc

    if not password:
        raise ValueError(
            "Password cannot be empty. "
            "Why: Blank password submitted. "
            "Fix: Re-run the script and enter a non-empty password."
        )

    return password


def _encrypt_env_file(env_path: Path, crypt_path: Path) -> None:
    """Read a plaintext `.env` file, encrypt its contents, and write `.env-crypt`.

    Args:
        env_path (Path): Path to the source plaintext `.env` file.
        crypt_path (Path): Path to the destination encrypted `.env-crypt` file.

    Raises:
        ValueError: If password input fails validation.
        OSError: If reading `env_path` or writing `crypt_path` fails.
    """
    log_step("_encrypt_env_file", f"Encrypting '{env_path.name}' -> '{crypt_path.name}'")
    password = prompt_password(f"Enter password to encrypt {env_path.name}: ")
    plaintext = env_path.read_bytes()
    encrypted = encrypt_data(plaintext, password)
    crypt_path.write_bytes(encrypted + b"\n")
    log_success(
        "_encrypt_env_file",
        f"Encrypted '{env_path.name}' -> '{crypt_path.name}' ({len(encrypted) + 1} bytes written)",
    )


def _decrypt_env_file(crypt_path: Path, env_path: Path) -> None:
    """Read an encrypted `.env-crypt` file, decrypt its contents, and write `.env`.

    Args:
        crypt_path (Path): Path to the source encrypted `.env-crypt` file.
        env_path (Path): Path to the destination plaintext `.env` file.

    Raises:
        ValueError: If password input fails or payload authentication/decryption fails.
        OSError: If reading `crypt_path` or writing `env_path` fails.
    """
    log_step("_decrypt_env_file", f"Decrypting '{crypt_path.name}' -> '{env_path.name}'")
    password = prompt_password(f"Enter password to decrypt {crypt_path.name}: ")
    encoded_payload = crypt_path.read_bytes()
    plaintext = decrypt_data(encoded_payload, password)
    env_path.write_bytes(plaintext)
    log_success(
        "_decrypt_env_file",
        f"Decrypted '{crypt_path.name}' -> '{env_path.name}' ({len(plaintext)} bytes written)",
    )


def _discover_operations(env_path: Path, crypt_path: Path) -> list[tuple[str, Path, Path]]:
    """Determine pending encryption or decryption work items from file presence.

    Inspects `env_path` and `crypt_path` and queues at most one operation:
    - Both files exist or neither file exists: returns an empty list.
    - Only `env_path` exists: queues `("encrypt", env_path, crypt_path)`.
    - Only `crypt_path` exists: queues `("decrypt", crypt_path, env_path)`.

    Args:
        env_path (Path): Path to the plaintext `.env` file.
        crypt_path (Path): Path to the encrypted `.env-crypt` file.

    Returns:
        list[tuple[str, Path, Path]]: List of `(operation, source_path, target_path)`
            work items to execute.

    Raises:
        OSError: If checking file existence on the filesystem fails.
    """
    has_env = env_path.is_file()
    has_crypt = crypt_path.is_file()

    if has_env and has_crypt:
        log_info(
            "_discover_operations",
            f"Both '{env_path.name}' and '{crypt_path.name}' exist; no action required.",
        )
        return []

    if has_env and not has_crypt:
        return [("encrypt", env_path, crypt_path)]

    if has_crypt and not has_env:
        return [("decrypt", crypt_path, env_path)]

    log_info(
        "_discover_operations",
        f"Neither '{env_path.name}' nor '{crypt_path.name}' was found in the current directory.",
    )
    return []


def main() -> int:
    """Orchestrate discovery, execution, and reporting of `.env` and `.env-crypt` tasks.

    Returns:
        int: Process exit code (`0` when all operations succeed or no work is required,
            `1` if discovery or any operation fails).
    """
    working_dir = Path.cwd()
    env_path = working_dir / ENV_PATH.name
    crypt_path = working_dir / CRYPT_PATH.name

    try:
        operations = _discover_operations(env_path, crypt_path)
    except Exception as exc:
        log_error(
            "main",
            f"Discovery phase failed: {exc}. Why: Unable to inspect working directory. Fix: Check directory permissions.",
        )
        return 1

    if not operations:
        return 0

    failures = 0

    for operation, source_path, target_path in operations:
        try:
            if operation == "encrypt":
                _encrypt_env_file(source_path, target_path)
            elif operation == "decrypt":
                _decrypt_env_file(source_path, target_path)
            else:
                raise ValueError(f"Unsupported operation '{operation}'.")
        except Exception as exc:
            failures += 1
            log_error(operation, str(exc))

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
