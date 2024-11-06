import os

# Tentukan path direktori history
history_dir = 'history'
# Tentukan nama file output untuk menyimpan hasil gabungan
output_file = 'gabungan.txt'

# Membuka file output untuk menulis hasil gabungan
with open(output_file, 'w') as outfile:
    # Melakukan iterasi untuk setiap file dalam direktori history
    for filename in os.listdir(history_dir):
        # Cek apakah file tersebut ber-ekstensi .txt
        if filename.endswith('.txt'):
            file_path = os.path.join(history_dir, filename)
            # Buka file .txt dan tambahkan isinya ke output
            with open(file_path, 'r') as infile:
                for line in infile:
                    # Skip baris kosong
                    if line.strip():
                        outfile.write(line)

print(f"Semua file .txt di dalam direktori '{history_dir}' telah digabungkan ke dalam '{output_file}' tanpa baris kosong.")
