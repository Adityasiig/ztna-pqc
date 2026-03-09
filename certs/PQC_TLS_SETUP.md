# Post-Quantum Cryptography (PQC) Integration Guide

To enable PQC in the ZTNA framework, we use the `liboqs` library and the `oqs-openssl111` project.

## 1. Prerequisites (Ubuntu 22.04/24.04)
```bash
sudo apt update && sudo apt install build-essential cmake libssl-dev git -y
```

## 2. Compiling Open Quantum Safe (liboqs)
```bash
git clone https://github.com/open-quantum-safe/liboqs.git
cd liboqs
mkdir build && cd build
cmake -GNinja ..
ninja
sudo ninja install
```

## 3. Configuring OpenSSL with OQS Providers
Download and build the OQS-enabled OpenSSL to support algorithms like `kyber768` and `dilithium3`:
```bash
git clone https://github.com/open-quantum-safe/oqs-provider.git
cd oqs-provider
mkdir build && cd build
cmake -DOPENSSL_ROOT_DIR=/usr/local -DCMAKE_BUILD_TYPE=Release ..
make
```

## 4. Generating PQC Certificates
To secure the ZTNA Gateway (VM2):
```bash
# Generate Dilithium3 (PQC) root CA
openssl req -x509 -new -newkey dilithium3 -nodes -keyout ca.key -out ca.crt -subj "/CN=ZTNA-CA"

# Generate Kyber768 (PQC) server certificate
openssl req -new -newkey kyber768 -nodes -keyout server.key -out server.csr -subj "/CN=ztna-gateway.local"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt
```

## 5. Starting the PQC-TLS Server
```bash
openssl s_server -cert server.crt -key server.key -labels -tls1_3 -www -curves kyber768
```
*Note: This ensures the handshake negotiation uses NIST-standardized quantum-resistant algorithms.*
