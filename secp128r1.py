import hashlib
import binascii
import base58  # Pastikan Anda sudah menginstal library ini
from ecdsa import SigningKey, SECP128r1  # Menggunakan SECP128r1

# 1. Menghasilkan Kunci Pribadi
private_key = SigningKey.generate(curve=SECP128r1)
private_key_bytes = private_key.to_string()

# 2. Membuat WIF
# a. Tambahkan prefix (0x80 untuk mainnet)
wif_prefix = b'\x80' + private_key_bytes

# b. Hitung checksum
checksum = hashlib.sha256(hashlib.sha256(wif_prefix).digest()).digest()[:4]

# c. Gabungkan untuk WIF
wif = wif_prefix + checksum
wif_encoded = base58.b58encode(wif)

# 3. Menghitung Alamat Bitcoin
# a. Menghitung kunci publik
public_key = private_key.get_verifying_key()
public_key_bytes = public_key.to_string()

# b. SHA256 dari kunci publik
sha256_hash = hashlib.sha256(public_key_bytes).digest()

# c. RIPEMD160 dari SHA256
ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

# d. Menambahkan prefix (0x00 untuk mainnet)
address_prefix = b'\x00' + ripemd160_hash

# e. Menghitung checksum
address_checksum = hashlib.sha256(hashlib.sha256(address_prefix).digest()).digest()[:4]

# f. Gabungkan untuk alamat
address = address_prefix + address_checksum
address_encoded = base58.b58encode(address)

# Menampilkan hasil
print("Private Key (hex):", private_key_bytes.hex())
print("WIF:", wif_encoded.decode())
print("Public Key (hex):", public_key_bytes.hex())
print("Bitcoin Address:", address_encoded.decode())
