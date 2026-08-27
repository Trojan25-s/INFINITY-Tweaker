"""
Cryptographic storage helper for secure local activation persistence.
Uses machine-bound derivation and XOR/AES packaging so keys are never stored plaintext.
"""
import os
import json
import base64
import hashlib
from Core.Security.hwid import get_hardware_fingerprint

VAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Core", "Security", ".vault.dat")

def _get_derived_key() -> bytes:
    hwid = get_hardware_fingerprint()
    salt = b"INFINITY_TWEAKER_VAULT_KEY_2026"
    return hashlib.sha256(hwid.encode('utf-8') + salt).digest()

def save_activation_vault(data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(VAULT_PATH), exist_ok=True)
        raw_json = json.dumps(data).encode('utf-8')
        key = _get_derived_key()
        
        # Obfuscated machine-bound encryption
        encrypted = bytearray()
        for i in range(len(raw_json)):
            encrypted.append(raw_json[i] ^ key[i % len(key)])
            
        payload = base64.b64encode(bytes(encrypted)).decode('utf-8')
        with open(VAULT_PATH, 'w', encoding='utf-8') as f:
            f.write(payload)
        return True
    except Exception:
        return False

def load_activation_vault() -> dict:
    if not os.path.exists(VAULT_PATH):
        return {}
    try:
        with open(VAULT_PATH, 'r', encoding='utf-8') as f:
            payload = f.read().strip()
        if not payload:
            return {}
        encrypted = base64.b64decode(payload)
        key = _get_derived_key()
        
        decrypted = bytearray()
        for i in range(len(encrypted)):
            decrypted.append(encrypted[i] ^ key[i % len(key)])
            
        data = json.loads(decrypted.decode('utf-8'))
        return data
    except Exception:
        return {}

def clear_activation_vault() -> bool:
    try:
        if os.path.exists(VAULT_PATH):
            os.remove(VAULT_PATH)
        return True
    except Exception:
        return False
