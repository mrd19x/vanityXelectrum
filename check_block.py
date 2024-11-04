import os
import requests
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fungsi untuk membersihkan konsol
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Konfigurasi RPC Electrum
RPC_USER = 'zia'
RPC_PASSWORD = '123123'
RPC_URL = 'http://127.0.0.1:7777'

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
        
        # Mengembalikan saldo terkonfirmasi dan tidak terkonfirmasi sebagai float
        confirmed_balance = float(result.get('result', {}).get('confirmed', '0.0'))  # Mengambil saldo terkonfirmasi
        unconfirmed_balance = float(result.get('result', {}).get('unconfirmed', '0.0'))  # Mengambil saldo tidak terkonfirmasi
        return confirmed_balance, unconfirmed_balance  # Kembalikan sebagai tuple
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching balance for address {address}: {e}")
        return 0.0, 0.0  # Kembalikan 0.0 jika ada kesalahan

def get_block_data(block_height, scan_block, scan_balance):
    """Mengambil data dari block tertentu dan menyimpan alamat legacy."""
    url = f"https://blockchain.info/block-height/{block_height}?format=json"
    try:
        if scan_block:
            print(f"Scanning block height: {block_height}")
        
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        
        # Mengambil daftar transaksi dari block
        block = data['blocks'][0]
        transactions = block['tx']
        
        # Membuat folder 'history' jika belum ada
        os.makedirs('history', exist_ok=True)

        # Set untuk menyimpan alamat yang sudah ditemukan dalam block ini
        unique_addresses = set()

        # Mengumpulkan semua alamat dari input dan output
        for tx in transactions:
            # Memeriksa input
            for inp in tx['inputs']:
                if 'prev_out' in inp and 'addr' in inp['prev_out']:
                    address = inp['prev_out']['addr']
                    if address.startswith('1'):  # Memastikan alamat adalah alamat legacy
                        unique_addresses.add(address)

            # Memeriksa output
            for out in tx['out']:
                if 'addr' in out:
                    address = out['addr']
                    if address.startswith('1'):  # Memastikan alamat adalah alamat legacy
                        unique_addresses.add(address)

        # Nama file berdasarkan block height
        file_name = f'history/{block_height}.txt'
        
        # Cek saldo untuk setiap alamat unik
        with open(file_name, 'a') as file:  # Buka file dengan mode append
            for address in unique_addresses:
                if scan_balance:
                    print(f"address: {address}", end=' ')
                confirmed_balance, unconfirmed_balance = get_address_balance(address)  # Cek saldo alamat
                total_balance = confirmed_balance + unconfirmed_balance  # Hitung total saldo

                if confirmed_balance >= 0.099:  # Cek apakah saldo terkonfirmasi lebih besar atau sama dengan 0.05
                    file.write(f"{address} - Confirmed {confirmed_balance:.8f} BTC | Unconfirmed {unconfirmed_balance:.8f} BTC\n")  # Simpan alamat dan saldo ke file
                    if scan_balance:
                        print(f"- Confirmed {confirmed_balance:.8f} BTC | Unconfirmed {unconfirmed_balance:.8f} BTC | Got You 🔥")  # Menampilkan saldo di konsol
                elif scan_balance:
                    print(f"- Confirmed {confirmed_balance:.8f} BTC | Unconfirmed {unconfirmed_balance:.8f} BTC | Under Target 👁️")  # Menampilkan saldo jika tidak ada

        print(f"Addresses from block {block_height} have been processed.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching block data: {e}")

def main(start, end, scan_block, scan_balance, max_threads):
    # Membuat thread pool
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Mengumpulkan futures untuk setiap block
        futures = {executor.submit(get_block_data, block_height, scan_block, scan_balance): block_height for block_height in range(start, end + 1)}
        
        for future in as_completed(futures):
            block_height = futures[future]
            try:
                future.result()  # Mendapatkan hasil, jika ada exception akan dilempar di sini
            except Exception as e:
                print(f"Block {block_height} generated an exception: {e}")
            time.sleep(0.8)  # Jeda 0.8 detik antara setiap panggilan API

if __name__ == "__main__":
    clear_console()  # Panggil fungsi untuk membersihkan konsol
    parser = argparse.ArgumentParser(description='Fetch Bitcoin addresses from blocks.')
    parser.add_argument('--start', type=int, required=True, help='Starting block height')
    parser.add_argument('--end', type=int, required=True, help='Ending block height')
    parser.add_argument('--scan', action='append', choices=['block', 'balance'], help='What to scan for (can be specified multiple times)')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads to use for fetching data (default is 5)')

    args = parser.parse_args()

    # Menentukan apakah harus melakukan pemindaian block atau balance
    scan_block = 'block' in args.scan if args.scan else False
    scan_balance = 'balance' in args.scan if args.scan else False

    main(args.start, args.end, scan_block, scan_balance, args.threads)
