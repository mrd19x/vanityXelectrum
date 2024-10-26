import hashlib
import base58
import os
import requests
import time
import platform
import bech32
from ecdsa import SigningKey, SECP256k1
from Crypto.Hash import SHA256, RIPEMD160
import argparse
from random import randint

def is_valid_address(address):
    return len(address) in range(26, 36) and address.startswith(('1', '3', 'bc1'))

def get_address_balance(address):
    url = 'http://127.0.0.1:7777'
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "getaddressbalance",
        "params": [address]
    }
    auth = ('zia', '123123')
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, auth=auth, timeout=1)
        if response.status_code == 200:
            result = response.json()
            return result.get('result', None)
    except requests.exceptions.RequestException:
        pass
    return None

def save_found_entries(entries):
    with open('founds_blind_mode.csv', 'a') as f:
        f.writelines(f"{entry}\n" for entry in entries)

def private_key_to_wif(private_key, compressed=True):
    extended_key = b'\x80' + private_key + (b'\x01' if compressed else b'')
    checksum = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()[:4]
    return base58.b58encode(extended_key + checksum).decode('utf-8')

def private_key_to_public_key(private_key, compressed=True):
    sk = SigningKey.from_string(private_key, curve=SECP256k1)
    vk = sk.verifying_key
    return (b'\x02' if vk.to_string()[63] % 2 == 0 else b'\x03') + vk.to_string()[:32] if compressed else b'\x04' + vk.to_string()

def public_key_to_address(public_key, address_type='p2pkh'):
    sha256_hash = SHA256.new(public_key).digest()
    ripemd160_hash = RIPEMD160.new(sha256_hash).digest()

    if address_type == 'p2pkh':
        prefix, hash160 = b'\x00', ripemd160_hash
    elif address_type == 'p2sh':
        prefix, hash160 = b'\x05', RIPEMD160.new(SHA256.new(b'\x00\x14' + ripemd160_hash).digest()).digest()
    elif address_type == 'p2wpkh':
        return bech32.encode("bc", 0, ripemd160_hash)

    checksum = hashlib.sha256(hashlib.sha256(prefix + hash160).digest()).digest()[:4]
    return base58.b58encode(prefix + hash160 + checksum).decode('utf-8')

def generate_and_process_private_key(min_key, max_key, test_mode=False):
    private_key_int = randint(min_key, max_key)
    private_key = private_key_int.to_bytes(32, byteorder='big')

    addresses = [
        ("P2PKH Uncompressed", public_key_to_address(private_key_to_public_key(private_key, compressed=False))),
        ("P2PKH Compressed", public_key_to_address(private_key_to_public_key(private_key))),
        ("P2SH", public_key_to_address(private_key_to_public_key(private_key), address_type='p2sh')),
        ("P2WPKH", public_key_to_address(private_key_to_public_key(private_key), address_type='p2wpkh'))
    ]

    found_entries = []

    for label, address in addresses:
        balance = get_address_balance(address)
        if balance:
            confirmed = float(balance.get('confirmed', 0))
            unconfirmed = float(balance.get('unconfirmed', 0))
            print(f"{label}: {address} | Confirmed Balance: {confirmed:.8f} BTC | Unconfirmed Balance: {unconfirmed:.8f} BTC")

            if (confirmed > 0 or unconfirmed > 0) or test_mode:
                found_entries.append(f"{private_key.hex()},{private_key_to_wif(private_key)},{label},{address},{confirmed:.8f},{unconfirmed:.8f}")

    if found_entries:
        save_found_entries(found_entries)

def main():
    parser = argparse.ArgumentParser(description='Bitcoin Address Generator and Balance Checker')
    parser.add_argument('--test', action='store_true', help='Enable test mode to save addresses with zero balance.')
    parser.add_argument('--threads', type=int, default=5, help='Number of threads to use for processing.')
    parser.add_argument('--minkey', type=str, default="0", help='Minimum hexadecimal key value.')
    parser.add_argument('--maxkey', type=str, default="7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF", help='Maximum hexadecimal key value.')
    args = parser.parse_args()

    min_key = int(args.minkey, 16)
    max_key = int(args.maxkey, 16)

    while True:
        generate_and_process_private_key(min_key, max_key, test_mode=args.test)
        time.sleep(0.05)  # Small delay to reduce CPU/RAM load

if __name__ == "__main__":
    main()
