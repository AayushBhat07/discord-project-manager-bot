const crypto = require('crypto');

const ALGORITHM = 'aes-256-gcm';

/**
 * Encrypt plaintext using AES-256-GCM.
 * Returns format: iv:authTag:encryptedData (all base64)
 */
function encrypt(plaintext, key) {
  if (!plaintext || !key) return null;

  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ALGORITHM, Buffer.from(key, 'hex'), iv);

  let encrypted = cipher.update(plaintext, 'utf8', 'base64');
  encrypted += cipher.final('base64');

  const authTag = cipher.getAuthTag();

  return `${iv.toString('base64')}:${authTag.toString('base64')}:${encrypted}`;
}

/**
 * Decrypt ciphertext encrypted with AES-256-GCM.
 * Expects format: iv:authTag:encryptedData (all base64)
 * Falls back to plaintext on failure (backward compatibility).
 */
function decrypt(ciphertext, key) {
  if (!ciphertext || !key) return null;

  const parts = ciphertext.split(':');
  if (parts.length !== 3) {
    return ciphertext;
  }

  const [ivBase64, authTagBase64, encryptedBase64] = parts;

  try {
    const iv = Buffer.from(ivBase64, 'base64');
    const authTag = Buffer.from(authTagBase64, 'base64');
    const encrypted = Buffer.from(encryptedBase64, 'base64');

    const decipher = crypto.createDecipheriv(ALGORITHM, Buffer.from(key, 'hex'), iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted);
    decrypted = Buffer.concat([decrypted, decipher.final()]);

    return decrypted.toString('utf8');
  } catch (error) {
    return ciphertext;
  }
}

/**
 * Generate a random 32-byte encryption key (64 hex chars).
 */
function generateKey() {
  return crypto.randomBytes(32).toString('hex');
}

module.exports = { encrypt, decrypt, generateKey, ALGORITHM };
