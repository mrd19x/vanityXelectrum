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
    sudo apt-get install -y python3-pyqt5 libsecp256k1-dev python3-cryptography
}

# Fungsi untuk menginstal dependensi pada CentOS
install_centos() {
    echo "Menginstal dependensi untuk CentOS..."
    sudo yum install -y python3-qt5 libsecp256k1-devel python3-cryptography
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

echo "Instalasi selesai."