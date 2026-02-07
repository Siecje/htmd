import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def generate_private_key() -> tuple[rsa.RSAPrivateKey, str]:
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
    return private_key, password


def encrypt_post(
    html: str,
    title: str,
    subtitle: str | None,
    password: str,
) -> tuple[str, str, str]:
    html_b = html.encode('utf-8')
    title_b = title.encode('utf-8')
    subtitle_b = (subtitle or '').encode('utf-8')

    pem_str = (
        '-----BEGIN PRIVATE KEY-----\n' +
        password.strip() +
        '\n-----END PRIVATE KEY-----\n'
    )
    pem_b = pem_str.encode('utf-8')
    private_key = serialization.load_pem_private_key(pem_b, None)
    assert isinstance(private_key, rsa.RSAPrivateKey)

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

    subtitle_cipher_b = public_key.encrypt(
        subtitle_b,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    subtitle_cipher_base64 = base64.b64encode(
        subtitle_cipher_b,
    ).decode('utf-8')

    return (
        html_cipher_base64,
        title_cipher_base64,
        subtitle_cipher_base64,
    )
