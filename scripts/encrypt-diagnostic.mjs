import { closeSync, fstatSync, openSync, readFileSync, readSync } from 'node:fs';
import { constants, createCipheriv, createPublicKey, publicEncrypt, randomBytes } from 'node:crypto';

try {
  const [logPath, publicKeyPath] = process.argv.slice(2);
  const key = createPublicKey(readFileSync(publicKeyPath));
  if (key.asymmetricKeyType !== 'rsa' || key.asymmetricKeyDetails.modulusLength < 3072) throw new Error('Unsupported diagnostics key');
  const context = { phase: process.env.DIAGNOSTIC_PHASE || 'build', runId: process.env.GITHUB_RUN_ID || '', attempt: process.env.GITHUB_RUN_ATTEMPT || '' };
  if (!/^[A-Za-z0-9 .-]{1,96}$/.test(context.phase)) throw new Error('Invalid diagnostics phase');
  const fd = openSync(logPath, 'r');
  let tail;
  try {
    const size = fstatSync(fd).size;
    tail = Buffer.alloc(Math.min(size, 64 * 1024));
    const bytes = readSync(fd, tail, 0, tail.length, Math.max(0, size - tail.length));
    tail = tail.subarray(0, bytes);
  } finally { closeSync(fd); }
  const aes = randomBytes(32);
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', aes, iv);
  cipher.setAAD(Buffer.from(JSON.stringify(context)));
  const ciphertext = Buffer.concat([cipher.update(tail), cipher.final()]);
  const wrappedKey = publicEncrypt({ key, padding: constants.RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' }, aes);
  const envelope = { version: 1, algorithm: 'RSA-OAEP-SHA256+A256GCM', context, wrappedKey: wrappedKey.toString('base64'), iv: iv.toString('base64'), tag: cipher.getAuthTag().toString('base64'), ciphertext: ciphertext.toString('base64') };
  const encoded = Buffer.from(JSON.stringify(envelope)).toString('base64');
  process.stdout.write('BEGIN_COLORBESTIE_ENCRYPTED_DIAGNOSTIC\n' + encoded.match(/.{1,120}/g).join('\n') + '\nEND_COLORBESTIE_ENCRYPTED_DIAGNOSTIC\n');
} catch {
  process.stderr.write('Encrypted diagnostics unavailable; raw output remains withheld.\n');
  process.exitCode = 1;
}
