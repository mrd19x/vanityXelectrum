import requests
import subprocess
import os
import time
import platform

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
    with open('founds.csv', 'a') as f:
        for entry in entries:
            f.write(f"{entry}\n")

def main():
    clear_console()  # Bersihkan konsol sebelum menjalankan vanitygen
    # Jalankan vanitygen
    process = subprocess.Popen(['./supervanitygen/vanitygen', '-q', '-k', '12xA'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("Menjalankan vanitygen...")

    buffer_size = 500  # Ukuran buffer
    found_entries = []  # Buffer untuk menyimpan entri yang valid

    try:
        while True:
            output = process.stdout.readline()
            if output == b"" and process.poll() is not None:
                break
            if output:
                # Dekode dan ambil private key dan address dari output
                output_str = output.decode('utf-8').strip()
                # print(f"Output dari vanitygen: {output_str}")  # Tampilkan output ke console

                # Mengasumsikan output format: privatekey,address
                try:
                    private_key, address = output_str.split(',')
                    address = address.strip()  # Bersihkan spasi

                    if is_valid_address(address):
                        balance = get_address_balance(address)
                        if balance is not None:
                            confirmed_balance = float(balance['confirmed'])  # Konversi dari satoshi ke BTC
                            unconfirmed_balance = float(balance['unconfirmed'])  # Konversi dari satoshi ke BTC

                            # Tampilkan informasi ke konsol
                            print(f"{private_key}|{address}|{confirmed_balance:.8f}|{unconfirmed_balance:.8f}")

                            # Simpan private key dan address ke buffer jika saldo lebih besar dari 0
                            if confirmed_balance > 0 or unconfirmed_balance > 0:
                                found_entries.append(f"{private_key}|{address}|{confirmed_balance:.8f}|{unconfirmed_balance:.8f}")
                                # print(f"Private key dan address disimpan ke buffer: {private_key}|{address}")

                            # Jika buffer sudah mencapai ukuran yang ditentukan, simpan ke file
                            if len(found_entries) >= buffer_size:
                                save_found_entries(found_entries)
                                # print(f"{buffer_size} entri disimpan ke founds.csv.")
                                found_entries.clear()  # Bersihkan buffer setelah menyimpan
                        else:
                            print(f"Gagal mendapatkan saldo untuk alamat: {address}.")
                    else:
                        print(f"Alamat tidak valid: {address}")

                except ValueError:
                    print(f"Format output tidak valid: {output_str}")
    except KeyboardInterrupt:
        print("Menghentikan proses...")

    # Simpan sisa entri di buffer ke file sebelum keluar
    if found_entries:
        save_found_entries(found_entries)
        print(f"Sisa entri disimpan ke founds.csv.")

    # Menutup proses vanitygen jika selesai
    process.terminate()
    process.wait()

if __name__ == "__main__":
    main()
