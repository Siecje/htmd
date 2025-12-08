function str2ab(str) {
  /*
  Convert a string into an ArrayBuffer
  from https://developers.google.com/web/updates/2012/06/How-to-convert-ArrayBuffer-to-and-from-String
  */
  const buf = new ArrayBuffer(str.length);
  const bufView = new Uint8Array(buf);
  for (let i = 0, strLen = str.length; i < strLen; i++) {
    bufView[i] = str.charCodeAt(i);
  }
  return buf;
}

async function importPrivateKey(pem_base64) {
  // base64 decode the string to get the binary data
  const binaryDerString = window.atob(pem_base64);
  // convert from a binary string to an ArrayBuffer
  const binaryDer = str2ab(binaryDerString);

  ret = await window.crypto.subtle.importKey(
    "pkcs8",
    binaryDer,
    {
      name: "RSA-OAEP",
      hash: "SHA-256",
    },
    true,
    ["decrypt"],
  );
  return ret;
}

async function decrypt(ciphertext, privateKey) {
  const decodedCiphertext = atob(ciphertext);
  const ciphertextArrayBuffer = new Uint8Array(decodedCiphertext.length).buffer;
  const ciphertextUint8Array = new Uint8Array(ciphertextArrayBuffer);
  for (let i = 0; i < decodedCiphertext.length; i++) {
    ciphertextUint8Array[i] = decodedCiphertext.charCodeAt(i);
  }

  const decrypted = await window.crypto.subtle.decrypt(
    {
      name: "RSA-OAEP",
    },
    privateKey,
    ciphertextUint8Array
  );

  return new TextDecoder().decode(decrypted);
}

async function decryptPost(pemEncodedPrivateKey, cipherHTML, cipherTitle) {
  const privateKey = await importPrivateKey(pemEncodedPrivateKey);
  try {
    const decryptedHTML = await decrypt(cipherHTML, privateKey);
    const contentDiv = document.getElementById('post-content');
    contentDiv.innerHTML = decryptedHTML;

    const decryptedTitle = await decrypt(cipherTitle, privateKey);
    const titleSpan = document.getElementById('post-title');
    titleSpan.textContent = decryptedTitle;
    document.title = decryptedTitle + ' ' + document.title;
  } catch (e) {
    console.error('Decryption failed:', e);
  }
}
