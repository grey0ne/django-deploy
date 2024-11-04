#!/usr/bin/env bash

CERT_NAME=${1}
CERT_DOMAIN=${2}

BIN_OPENSSL=/usr/bin/openssl
LOCAL_CERT_CERT=${SSL_CERTS_DIR}/${CERT_NAME}.crt
LOCAL_CERT_KEY=${SSL_CERTS_DIR}/${CERT_NAME}.key

echo "${CERT_NAME}"
echo "${CERT_DOMAIN}"

# Generate SSL certificate
mkdir -p ${SSL_CERTS_DIR}
${BIN_OPENSSL} req -x509 -out ${LOCAL_CERT_CERT} -keyout ${LOCAL_CERT_KEY} \
-newkey rsa:2048 -nodes -sha256 \
-subj "/CN=${CERT_DOMAIN}" -extensions EXT \
-config <(printf "[dn]\nCN=${CERT_DOMAIN}\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS.1:${CERT_DOMAIN}\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")

# Show results
echo ""
echo "New SSL certificate was generated:"
echo "- Certificate: ${LOCAL_CERT_CERT}"
echo "- Key: ${LOCAL_CERT_KEY}"
echo ""

