import os
import requests
import time
import platform
import argparse
import uuid
import base64

API_KEY = 'a7cf61f5-9130-467c-a411-54d3954b7b3e'  # API Key untuk autentikasi ke Pixeldrain
TELEGRAM_TOKEN = '7979371135:AAHoJ7J4340RNSgrAWWXkcody6Z4XPXIdwk'  # Token Bot Telegram
TELEGRAM_CHAT_ID = '-1002414687035'  # Chat ID Telegram (untuk grup/channel gunakan format negatif)

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

def send_to_telegram(message):
    """Kirim pesan ke Telegram."""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Message sent to Telegram successfully.")
    else:
        print(f"Failed to send message to Telegram. Status code: {response.status_code}")
        print(f"Response: {response.text}")

def upload_to_pixeldrain(file_path):
    """Unggah file ke Pixeldrain dan kembalikan link unduhan."""
    url = 'https://pixeldrain.com/api/file'
    
    # Encode API Key untuk Authorization header dalam format Basic Auth
    auth_str = f":{API_KEY}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_b64}'
    }
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        
        # Mengunggah file dengan header Authorization
        response = requests.post(url, files=files, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success') and 'id' in result:
                file_url = f"https://pixeldrain.com/u/{result['id']}"
                print(f"File uploaded to Pixeldrain: {file_url}")
                
                # Kirim link ke Telegram
                send_to_telegram(f"File uploaded to Pixeldrain: {file_url}")
                
                return file_url
        else:
            print(f"Failed to upload file {file_path} to Pixeldrain. Status code: {response.status_code}")
            print(f"Response: {response.text}")
        return None

def save_buffered_addresses(buffer, output_dir):
    """Simpan buffer ke dalam file baru jika mencapai 500 alamat, kemudian unggah ke Pixeldrain."""
    if len(buffer) == 0:
        return

    # Nama file unik menggunakan UUID
    unique_filename = os.path.join(output_dir, f"addresses_{uuid.uuid4().hex}.txt")
    
    with open(unique_filename, 'w') as outfile:
        for entry in buffer:
            outfile.write(f"{entry}\n")
    
    # Unggah file ke Pixeldrain
    upload_to_pixeldrain(unique_filename)
    
    buffer.clear()  # Kosongkan buffer setelah disimpan

def check_balance_from_file(input_file, buffer_size=5000, min_balance=0.001, output_dir='output'):
    """Cek saldo untuk alamat dari file input, hanya simpan saldo >= min_balance, dan simpan secara batch."""
    
    # Pastikan direktori output ada
    os.makedirs(output_dir, exist_ok=True)

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
                        save_buffered_addresses(buffer, output_dir)
            else:
                print(f"Invalid address format: {address}")

    # Simpan sisa buffer yang belum disimpan ke file
    if buffer:
        save_buffered_addresses(buffer, output_dir)

def main():
    clear_console()
    parser = argparse.ArgumentParser(description='Bitcoin Balance Checker')
    parser.add_argument('--checkbalance', action='store_true', help='Check balance for addresses from an input file.')
    parser.add_argument('--input', type=str, help='Input file containing addresses.')
    parser.add_argument('--output_dir', type=str, default='output', help='Directory to save output files.')
    args = parser.parse_args()

    if args.checkbalance:
        if not args.input:
            print("Please provide an --input file for checking balance.")
            return
        check_balance_from_file(args.input, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
