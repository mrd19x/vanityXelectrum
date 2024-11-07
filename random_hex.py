import argparse
import random
import hashlib
import base58
import requests
from ecdsa import SigningKey, SECP256k1
import re
import concurrent.futures
import time
import os
import threading

# Konfigurasi RPC Electrum
RPC_USER = 'zia'
RPC_PASSWORD = '123123'
RPC_URL = 'http://127.0.0.1:7777'

# Deklarasi global
processed_hex = set()  # Menggunakan set untuk memastikan private key unik
processed_hex_lock = threading.Lock()  # Mutex untuk memastikan hanya satu thread yang mengakses processed_hex
file_lock = threading.Lock()  # Mutex untuk mengamankan akses file saat menyimpan hasil

def generate_random_hex(hex_pattern):
    """Menggantikan karakter 'x' dalam hex_pattern dengan nilai heksadesimal acak."""
    return ''.join(
        random.choice('0123456789abcdef') if char == 'x' else char
        for char in hex_pattern
    )

def is_valid_private_key(private_key_hex):
    """Memeriksa apakah private key berada dalam rentang yang valid."""
    private_key_int = int(private_key_hex, 16)
    return 0 < private_key_int < SECP256k1.order

def private_key_to_wif(private_key_hex):
    """Konversi private key heksadesimal ke WIF."""
    private_key_bytes = bytes.fromhex(private_key_hex)
    extended_key = b'\x80' + private_key_bytes
    first_sha = hashlib.sha256(extended_key).digest()
    second_sha = hashlib.sha256(first_sha).digest()
    checksum = second_sha[:4]
    wif = base58.b58encode(extended_key + checksum).decode()
    return wif

def wif_to_address(wif):
    """Konversi WIF menjadi Bitcoin address."""
    private_key = base58.b58decode(wif)[1:-4]
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()
    sha256_bpk = hashlib.sha256(public_key).digest()
    ripemd160_bpk = hashlib.new('ripemd160', sha256_bpk).digest()
    extended_ripemd160 = b'\x00' + ripemd160_bpk
    checksum = hashlib.sha256(hashlib.sha256(extended_ripemd160).digest()).digest()[:4]
    binary_address = extended_ripemd160 + checksum
    return base58.b58encode(binary_address).decode()

def get_address_balance(address):
    """Mengambil saldo alamat Bitcoin menggunakan RPC Electrum dan mengembalikan saldo terkonfirmasi dan tidak terkonfirmasi."""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getaddressbalance",
        "params": [address]
    }
    try:
        response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASSWORD))
        response.raise_for_status()
        result = response.json()
        confirmed_balance = float(result.get('result', {}).get('confirmed', '0.0'))
        unconfirmed_balance = float(result.get('result', {}).get('unconfirmed', '0.0'))
        return confirmed_balance, unconfirmed_balance
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error saat memeriksa saldo untuk alamat {address}: {e}")
        return 0.0, 0.0

def has_transaction_history(address):
    """Mengembalikan True jika alamat memiliki riwayat transaksi, False jika tidak."""
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getaddresshistory",
        "params": [address]
    }
    try:
        response = requests.post(RPC_URL, json=payload, auth=(RPC_USER, RPC_PASSWORD))
        response.raise_for_status()
        result = response.json()
        return len(result.get('result', [])) > 0
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error saat memeriksa riwayat transaksi untuk alamat {address}: {e}")
        return False

def save_to_file(hexa, wif, address):
    """Simpan data hexa, WIF, dan address ke file log jika ada riwayat transaksi atau saldo."""
    # Pastikan direktori log/ ada, jika belum buat
    os.makedirs("log", exist_ok=True)
    
    with file_lock:
        with open("log/results.txt", "a") as f:
            f.write(f"Hexa: {hexa}\nWIF: {wif}\nAddress: {address}\n\n")

def generate_and_check_address(hex_pattern, index, total_possibilities):
    """Generate dan cek saldo serta riwayat transaksi dari Bitcoin address."""
    while True:
        private_key_hex = generate_random_hex(hex_pattern)

        # Menggunakan Lock untuk mengakses processed_hex secara aman
        with processed_hex_lock:
            if private_key_hex in processed_hex:
                continue  # Lewati jika sudah pernah diproses

            # Tambahkan private_key_hex ke processed_hex setelah cek
            processed_hex.add(private_key_hex)

        if not is_valid_private_key(private_key_hex):
            continue

        wif = private_key_to_wif(private_key_hex)
        btc_address = wif_to_address(wif)

        confirmed, unconfirmed = get_address_balance(btc_address)
        history = has_transaction_history(btc_address)

        if confirmed > 0 or unconfirmed > 0 or history:
            print(f"{index+1}/{total_possibilities} - Bitcoin Address: {btc_address}, Confirmed: {confirmed}, Unconfirmed: {unconfirmed}, History: {'Yes' if history else 'No'}")
            save_to_file(private_key_hex, wif, btc_address)
        else:
            print(f"{index+1}/{total_possibilities} - Bitcoin Address: {btc_address} - Tidak ada saldo, Tidak ada riwayat transaksi.")
        
        break

def calculate_possibilities(hex_pattern):
    """Menghitung jumlah kemungkinan berdasarkan jumlah 'x' dalam pola heksadesimal."""
    num_x = hex_pattern.count('x')
    return 16 ** num_x

def generate_all_addresses(hex_pattern, num_threads):
    """Generate dan print seluruh Bitcoin address dari pola hex yang diberikan."""
    possibilities = calculate_possibilities(hex_pattern)
    print(f"Jumlah kemungkinan hasil: {possibilities}")
    
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(possibilities):
            futures.append(executor.submit(generate_and_check_address, hex_pattern, i, possibilities))

        for future in concurrent.futures.as_completed(futures):
            future.result()

    end_time = time.time()
    print(f"\nProses selesai. Waktu eksekusi: {end_time - start_time:.2f} detik.")

def main():
    parser = argparse.ArgumentParser(description="Generate Bitcoin address dari pola hex dengan 'x' sebagai pengganti nilai acak.")
    parser.add_argument("--find", type=str, required=True, help="64-character hex string with 'x' as placeholders for random values")
    parser.add_argument("--threads", type=int, default=1, help="Jumlah thread untuk paralel (default: 1)")
    args = parser.parse_args()
    
    hex_pattern = args.find
    num_threads = args.threads

    if not re.fullmatch(r'[0-9a-fx]{64}', hex_pattern):
        print("Error: Input harus 64 karakter dan hanya boleh berisi 0-9, a-f, atau x.")
        return

    generate_all_addresses(hex_pattern, num_threads)

if __name__ == "__main__":
    main()
