import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def encrypt_post(
    html: str,
    title: str,
    password: str | None,
) -> tuple[str, str, str]:
    html_b = html.encode('utf-8')
    title_b = title.encode('utf-8')

    if password is not None:
        pem_str = (
            '-----BEGIN PRIVATE KEY-----\n' +
            password.strip() +
            '\n-----END PRIVATE KEY-----\n'
        )
        pem_b = pem_str.encode('utf-8')
        private_key = serialization.load_pem_private_key(pem_b, None)
        assert isinstance(private_key, rsa.RSAPrivateKey)
    else:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        password = pem.decode('utf-8')
        password = (
            password.replace('-----BEGIN PRIVATE KEY-----\n', '')
            .replace('-----END PRIVATE KEY-----\n', '')
        )

    public_key = private_key.public_key()

    html_cipher_b = public_key.encrypt(
        html_b,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    html_cipher_base64 = base64.b64encode(html_cipher_b).decode('utf-8')

    title_cipher_b = public_key.encrypt(
        title_b,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    title_cipher_base64 = base64.b64encode(title_cipher_b).decode('utf-8')

    return password, html_cipher_base64, title_cipher_base64
