#!/bin/bash

# Fungsi untuk mengecek distro
check_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

# Fungsi untuk menginstal dependensi pada Ubuntu
install_ubuntu() {
    echo "Menginstal dependensi untuk Ubuntu..."
    sudo apt-get update
    sudo apt-get install -y python3-pyqt5 libsecp256k1-dev python3-cryptography python3-setuptools python3-pip
}

# Fungsi untuk menginstal dependensi pada CentOS
install_centos() {
    echo "Menginstal dependensi untuk CentOS..."
    sudo yum install -y python3-qt5 libsecp256k1-devel python3-cryptography python3-setuptools python3-pip
}

# Fungsi untuk mengunduh dan menginstal Electrum
install_electrum() {
    echo "Mengunduh Electrum..."
    wget https://download.electrum.org/4.5.7/Electrum-4.5.7.tar.gz
    wget https://download.electrum.org/4.5.7/Electrum-4.5.7.tar.gz.asc
    echo "Memverifikasi file..."
    gpg --verify Electrum-4.5.7.tar.gz.asc

    echo "Membuat lingkungan virtual..."
    python3 -m venv env

    echo "Lingkungan virtual telah dibuat. Aktifkan dengan menjalankan:"
    echo "source env/bin/activate"

    echo "Menginstal Electrum di lingkungan virtual..."
    source env/bin/activate
    pip install Electrum-4.5.7.tar.gz

    echo "Instalasi Electrum selesai. Untuk mengaktifkan lingkungan virtual, gunakan:"
    echo "source env/bin/activate"
}

# Fungsi untuk menginstal supervanitygen
install_supervanitygen() {
    echo "Mengunduh supervanitygen..."
    git clone https://github.com/klynastor/supervanitygen.git
    cd supervanitygen || { echo "Gagal masuk ke direktori supervanitygen"; exit 1; }

    echo "Menginstal dependensi build..."
    sudo yum -y install gcc make automake autoconf libtool gmp-devel

    echo "Membangun supervanitygen..."
    make

    echo "Build selesai. Kembali ke direktori sebelumnya..."
    cd .. || { echo "Gagal kembali ke direktori sebelumnya"; exit 1; }
}

# Memeriksa distro
distro=$(check_distro)

# Menginstal dependensi berdasarkan distro
case "$distro" in
    ubuntu|debian)
        install_ubuntu
        ;;
    centos|rhel)
        install_centos
        ;;
    *)
        echo "Distribusi tidak dikenal atau tidak didukung: $distro"
        exit 1
        ;;
esac

# Menginstal Electrum
install_electrum

# Menginstal supervanitygen
install_supervanitygen

echo "Semua instalasi selesai."
