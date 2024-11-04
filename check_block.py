import os
import requests
import argparse
import time

# Fungsi untuk membersihkan konsol
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Konfigurasi RPC Electrum
RPC_USER = 'zia'
RPC_PASSWORD = '123123'
RPC_URL = 'http://127.0.0.1:7777'

def get_address_balance(address):
    """Mengambil saldo alamat Bitcoin menggunakan RPC Electrum."""
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
        
        # Mengembalikan saldo terkonfirmasi sebagai string
        confirmed_balance = result.get('result', {}).get('confirmed', '0.0')  # Mengambil saldo sebagai string
        return confirmed_balance  # Kembalikan saldo sebagai string
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching balance for address {address}: {e}")
        return '0.0'  # Kembalikan '0.0' jika ada kesalahan

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
        
        # Membuka file untuk menyimpan alamat legacy dengan mode append
        with open('history/list_address.txt', 'a') as file:
            # Menyisipkan header untuk setiap block baru
            file.write(f"\n# Addresses from block height {block_height}\n")
            
            # Set untuk menyimpan alamat yang sudah ditemukan dalam block ini
            block_addresses = set()

            for tx in transactions:
                # Memeriksa input
                for inp in tx['inputs']:
                    if 'prev_out' in inp and 'addr' in inp['prev_out']:
                        address = inp['prev_out']['addr']
                        # Memastikan alamat adalah alamat legacy dan belum ada dalam block ini
                        if address.startswith('1') and address not in block_addresses:
                            if scan_balance:
                                print(f"Checking balance for address: {address}", end=' ')
                            balance = get_address_balance(address)  # Cek saldo alamat
                            if float(balance) >= 0.00999:  # Cek apakah saldo lebih besar atau sama dengan 0.05
                                file.write(f"{address}\n")
                                block_addresses.add(address)  # Tambahkan alamat ke set
                                if scan_balance:
                                    print(f"- Balance: {balance} BTC (got you)")  # Menampilkan saldo di konsol
                            elif scan_balance:
                                print(f"- Balance: {balance} BTC (under target)")  # Menampilkan saldo jika tidak ada

                # Memeriksa output
                for out in tx['out']:
                    if 'addr' in out:
                        address = out['addr']
                        # Memastikan alamat adalah alamat legacy dan belum ada dalam block ini
                        if address.startswith('1') and address not in block_addresses:
                            if scan_balance:
                                print(f"Checking balance for address: {address}", end=' ')
                            balance = get_address_balance(address)  # Cek saldo alamat
                            if float(balance) >= 0.00999:  # Cek apakah saldo lebih besar atau sama dengan 0.05
                                file.write(f"{address}\n")
                                block_addresses.add(address)  # Tambahkan alamat ke set
                                if scan_balance:
                                    print(f"- Balance: {balance} BTC (got you)")  # Menampilkan saldo di konsol
                            elif scan_balance:
                                print(f"- Balance: {balance} BTC (under target)")  # Menampilkan saldo jika tidak ada

        print(f"Addresses from block {block_height} have been appended to 'history/list_address.txt'.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching block data: {e}")

def main(start, end, scan_block, scan_balance):
    for block_height in range(start, end + 1):
        get_block_data(block_height, scan_block, scan_balance)
        time.sleep(0.8)  # Jeda 0.8 detik antara setiap panggilan API

if __name__ == "__main__":
    clear_console()  # Panggil fungsi untuk membersihkan konsol
    parser = argparse.ArgumentParser(description='Fetch Bitcoin addresses from blocks.')
    parser.add_argument('--start', type=int, required=True, help='Starting block height')
    parser.add_argument('--end', type=int, required=True, help='Ending block height')
    parser.add_argument('--scan', action='append', choices=['block', 'balance'], help='What to scan for (can be specified multiple times)')

    args = parser.parse_args()

    # Menentukan apakah harus melakukan pemindaian block atau balance
    scan_block = 'block' in args.scan if args.scan else False
    scan_balance = 'balance' in args.scan if args.scan else False

    main(args.start, args.end, scan_block, scan_balance)
