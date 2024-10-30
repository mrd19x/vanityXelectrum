import requests
import os
import argparse
import time

def check_vulnerability(address):
    url = f'https://blockchain.info/rawaddr/{address}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Memeriksa apakah permintaan berhasil

        data = response.json()

        filtered_transactions = [
            tx for tx in data.get('txs', []) if len(tx.get('inputs', [])) > 1
        ]
        
        vulnerable_hashes = []

        for tx in filtered_transactions:
            scripts = [input['script'] for input in tx['inputs']]
            seen_prefixes = set()

            for script in scripts:
                if len(script) >= 74:
                    part_a = script[:2]                  
                    part_b = script[2:10]                
                    part_c = script[10:74]               

                    prefix = part_a + part_b + part_c

                    if prefix in seen_prefixes:
                        vulnerable_hashes.append(tx['hash'])  
                        break

                    seen_prefixes.add(prefix)

        return vulnerable_hashes  

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:  # Too Many Requests
            # print(f'HTTP error occurred for address {address}: {http_err}')
            return None  # Return None to indicate we need to retry later
        else:
            # print(f'HTTP error occurred for address {address}: {http_err}')
            return []  # Return empty list for other HTTP errors

    except Exception as err:
        print(f'Error occurred for address {address}: {err}')
        return []

def bulk_check(file_path):
    folder_name = 'vulnerable_tx'
    os.makedirs(folder_name, exist_ok=True)

    total_addresses = 0
    total_vulnerable = 0
    failed_addresses = []  # List to keep track of failed addresses

    os.system('cls' if os.name == 'nt' else 'clear')
    
    with open(file_path, 'r') as file:
        for address in file:
            address = address.strip()  
            
            if address: 
                vulnerable_hashes = check_vulnerability(address)

                if vulnerable_hashes is None:  # Handle the 429 error
                    failed_addresses.append(address)  # Store failed address
                    print(f'Retrying address {address} in 30 minutes...')
                    break  # Stop processing further addresses

                vulnerable_count = len(vulnerable_hashes)
                total_addresses += 1
                total_vulnerable += vulnerable_count
                
                if vulnerable_count > 0:
                    filename = os.path.join(folder_name, f"{address}.txt")
                    with open(filename, 'w') as f:
                        for hash in vulnerable_hashes:
                            f.write(hash + '\n')

                print(f'Checked {total_addresses} addresses. Vulnerable transactions found: {total_vulnerable}', end='\r')
                time.sleep(1)  # Optional sleep to avoid hammering the API

    # Retry failed addresses after 30 minutes
    if failed_addresses:
        print(f'\nRetrying failed addresses in 30 minutes...')
        time.sleep(1800)  # Wait for 30 minutes
        
        # Retry each failed address
        for address in failed_addresses:
            print(f'Retrying address {address}...')
            vulnerable_hashes = check_vulnerability(address)
            if vulnerable_hashes:  # If we find vulnerabilities
                filename = os.path.join(folder_name, f"{address}.txt")
                with open(filename, 'w') as f:
                    for hash in vulnerable_hashes:
                        f.write(hash + '\n')
                print(f'Vulnerable transactions found for address {address} and saved.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check Bitcoin address vulnerabilities.')
    parser.add_argument('--bulk', action='store_true', help='Enable bulk checking mode.')
    parser.add_argument('--source', type=str, help='File containing list of wallet addresses.')

    args = parser.parse_args()

    if args.bulk and args.source:
        bulk_check(args.source)
    else:
        address = input("Masukkan alamat Bitcoin: ")
        check_vulnerability(address)
