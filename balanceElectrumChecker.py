import os
import requests
import time
import platform
import argparse

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
    """Mengambil saldo alamat Bitcoin menggunakan RPC server."""
    url = 'http://127.0.0.1:7777'  # Ganti dengan port RPC yang sesuai
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getaddressbalance",
        "params": [address]
    }
    auth = ('zia', '123123')

    while True:
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, auth=auth, timeout=1)

            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    return None
            else:
                print(f"Error: Status code {response.status_code} untuk address {address}.")
                return None
        except requests.exceptions.Timeout:
            print(f"Timeout saat mencoba mendapatkan balance untuk address: {address}, mencoba lagi...")
        except Exception as e:
            print(f"Exception occurred: {e} untuk address: {address}, mencoba lagi...")

        time.sleep(delay)

def save_buffered_addresses(buffer, output_file):
    """Simpan buffer ke dalam file output."""
    with open(output_file, 'a') as outfile:
        for entry in buffer:
            outfile.write(f"{entry}\n")
    buffer.clear()  # Kosongkan buffer setelah disimpan

def check_balance_from_file(input_file, buffer_size=20, min_balance=0.001):
    """Cek saldo untuk alamat dari file input, hanya simpan saldo >= min_balance, dan simpan secara batch."""
    
    # Tentukan nama file output dengan menambahkan "_reformatted.txt" ke nama file input
    output_file = f"{os.path.splitext(input_file)[0]}_reformatted.txt"
    
    buffer = []
    with open(input_file, 'r') as infile:
        for line in infile:
            address = line.strip()
            if is_valid_address(address):
                balance = get_address_balance(address)
                if balance is not None:
                    confirmed_balance = float(balance['confirmed'])
                    unconfirmed_balance = float(balance['unconfirmed'])
                    total_balance = confirmed_balance + unconfirmed_balance
                    
                    # Tambahkan ke buffer jika saldo memenuhi kriteria
                    if total_balance >= min_balance:
                        buffer.append(f"{address}")
                        print(f"Address: {address} | Confirmed Balance: {confirmed_balance:.8f} BTC | Unconfirmed Balance: {unconfirmed_balance:.8f} BTC")

                    # Simpan buffer ke file jika mencapai ukuran buffer_size
                    if len(buffer) >= buffer_size:
                        save_buffered_addresses(buffer, output_file)
            else:
                print(f"Invalid address format: {address}")

    # Simpan sisa buffer yang belum disimpan ke file
    if buffer:
        save_buffered_addresses(buffer, output_file)

def main():
    clear_console()
    parser = argparse.ArgumentParser(description='Bitcoin Balance Checker')
    parser.add_argument('--checkbalance', action='store_true', help='Check balance for addresses from an input file.')
    parser.add_argument('--input', type=str, help='Input file containing addresses.')
    args = parser.parse_args()

    if args.checkbalance:
        if not args.input:
            print("Please provide an --input file for checking balance.")
            return
        check_balance_from_file(args.input)

if __name__ == "__main__":
    main()
