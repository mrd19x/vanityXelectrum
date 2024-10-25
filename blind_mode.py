import hashlib
import base58
import os
import requests
import time
import platform
import bech32  # Pastikan Anda menginstal bech32 dengan `pip install bech32`
from ecdsa import SigningKey, SECP256k1
from Crypto.Hash import SHA256, RIPEMD160
import argparse
from concurrent.futures import ThreadPoolExecutor

def clear_console():
    """Bersihkan konsol tergantung pada sistem operasi."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def is_valid_address(address):
    """Cek apakah format alamat Bitcoin valid atau tidak."""
    if len(address) < 26 or len(address) > 35:  # Panjang umum alamat Bitcoin
        return False
    if address.startswith(('1', '3', 'bc1')):  # Alamat Bitcoin biasa dan Bech32
        return True
    return False

def get_address_balance(address, delay=2):
    url = 'http://127.0.0.1:7777'  # Ganti dengan port RPC yang sesuai
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getaddressbalance",
        "params": [address]
    }

    # Autentikasi menggunakan tuple (username, password)
    auth = ('zia', '123123')

    while True:  # Loop tanpa batas untuk mencoba mendapatkan balance
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, auth=auth, timeout=1)

            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    # Menyembunyikan error dari hasil RPC
                    return None
            else:
                print(f"Error: Status code {response.status_code} untuk address {address}.")
                return None
        except requests.exceptions.Timeout:
            print(f"Timeout saat mencoba mendapatkan balance untuk address: {address}, mencoba lagi...")
        except Exception as e:
            print(f"Exception occurred: {e} untuk address: {address}, mencoba lagi...")

        time.sleep(delay)  # Tunggu sejenak sebelum mencoba lagi

def save_found_entries(entries):
    """Simpan semua private key dan address ke dalam founds.csv."""
    with open('founds_blind_mode.csv', 'a') as f:
        for entry in entries:
            f.write(f"{entry}\n")

def private_key_to_wif_uncompressed(private_key):
    extended_key = b'\x80' + private_key
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    final_key = extended_key + checksum
    return base58.b58encode(final_key).decode('utf-8')

def private_key_to_wif_compressed(private_key):
    extended_key = b'\x80' + private_key + b'\x01'
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    final_key = extended_key + checksum
    return base58.b58encode(final_key).decode('utf-8')

def private_key_to_uncompressed_public_key(private_key):
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()
    return public_key

def private_key_to_compressed_public_key(private_key):
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x02' + vk.to_string()[:32] if vk.to_string()[63] % 2 == 0 else b'\x03' + vk.to_string()[:32]
    return public_key

def public_key_to_address_p2pkh(public_key):
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_hash)
    public_key_hash = ripemd160.digest()
    versioned_key_hash = b'\x00' + public_key_hash
    checksum = hashlib.sha256(hashlib.sha256(versioned_key_hash).digest()).digest()[:4]
    final_key = versioned_key_hash + checksum
    return base58.b58encode(final_key).decode('utf-8')

def public_key_to_address_p2sh(public_key):
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_hash)
    public_key_hash = ripemd160.digest()
    script_pubkey = b'\x00\x14' + public_key_hash  # P2SH script (OP_HASH160 <pubKeyHash> OP_EQUAL)
    sha256_script = hashlib.sha256(script_pubkey).digest()
    ripemd160_script = RIPEMD160.new(sha256_script).digest()
    prefix = b'\x05'  # Mainnet prefix for P2SH
    versioned_key_hash = prefix + ripemd160_script
    checksum = hashlib.sha256(hashlib.sha256(versioned_key_hash).digest()).digest()[:4]
    final_key = versioned_key_hash + checksum
    return base58.b58encode(final_key).decode('utf-8')

def public_key_to_address_p2wpkh(public_key):
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_hash)
    public_key_hash = ripemd160.digest()

    # P2WPKH prefix (0x00 for mainnet, 0x01 for testnet)
    witness_version = 0
    witness_program = public_key_hash

    # Create the bech32 address
    hrp = "bc"  # Use "tb" for testnet
    return bech32.encode(hrp, witness_version, witness_program)

def public_key_to_address_p2sh_p2wpkh(public_key):
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160 = RIPEMD160.new()
    ripemd160.update(sha256_hash)
    public_key_hash = ripemd160.digest()
    
    # Create a redeem script for P2WPKH
    redeem_script = b'\x00\x14' + public_key_hash  # OP_0 <hash160>
    
    # Create the P2SH address from the redeem script
    sha256_script = hashlib.sha256(redeem_script).digest()
    ripemd160_script = RIPEMD160.new(sha256_script).digest()
    prefix = b'\x05'  # Mainnet prefix for P2SH
    versioned_key_hash = prefix + ripemd160_script
    checksum = hashlib.sha256(hashlib.sha256(versioned_key_hash).digest()).digest()[:4]
    final_key = versioned_key_hash + checksum
    return base58.b58encode(final_key).decode('utf-8')

def generate_and_process_private_key(test_mode=False):
    # Generate a random 32-byte private key
    private_key = os.urandom(32)
    
    # Generate WIFs
    wif_uncompressed = private_key_to_wif_uncompressed(private_key)
    wif_compressed = private_key_to_wif_compressed(private_key)

    # Generate public keys
    uncompressed_public_key = private_key_to_uncompressed_public_key(private_key)
    compressed_public_key = private_key_to_compressed_public_key(private_key)

    # Generate addresses
    uncompressed_address = public_key_to_address_p2pkh(uncompressed_public_key)
    compressed_address = public_key_to_address_p2pkh(compressed_public_key)
    p2sh_address = public_key_to_address_p2sh(compressed_public_key)
    p2wpkh_address = public_key_to_address_p2wpkh(compressed_public_key)
    p2sh_p2wpkh_address = public_key_to_address_p2sh_p2wpkh(compressed_public_key)

    # Cek saldo untuk setiap alamat
    addresses = [
        ("P2PKH Uncompressed Address", uncompressed_address),
        ("P2PKH Compressed Address", compressed_address),
        ("P2SH Address", p2sh_address),
        ("P2WPKH Address", p2wpkh_address),
        ("P2SH-P2WPKH Address", p2sh_p2wpkh_address)
    ]

    # Buffer untuk menyimpan entri yang valid
    found_entries = []

    # Print results with balance
    for label, address in addresses:
        balance = get_address_balance(address)
        if balance is not None:
            confirmed_balance = float(balance['confirmed'])  # Konversi dari satoshi ke BTC
            unconfirmed_balance = float(balance['unconfirmed'])  # Konversi dari satoshi ke BTC
            
            # Tampilkan informasi
            print(f"{label}: {address} | Confirmed Balance: {confirmed_balance:.8f} BTC | Unconfirmed Balance: {unconfirmed_balance:.8f} BTC")

            # Logika penyimpanan berdasarkan mode
            if (confirmed_balance > 0 or unconfirmed_balance > 0) or test_mode:
                found_entries.append(f"{private_key.hex()},{wif_compressed},{wif_uncompressed},{label},{address},{confirmed_balance:.8f},{unconfirmed_balance:.8f}")

    # Simpan semua entri yang ditemukan ke file CSV
    if found_entries:
        save_found_entries(found_entries)

def main():
    clear_console()  # Bersihkan konsol sebelum menjalankan
    parser = argparse.ArgumentParser(description='Bitcoin Address Generator and Balance Checker')
    parser.add_argument('--test', action='store_true', help='Enable test mode to save addresses with zero balance.')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads to use for processing.')
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        while True:
            executor.submit(generate_and_process_private_key, test_mode=args.test)

if __name__ == "__main__":
    main()
