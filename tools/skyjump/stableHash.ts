import { createHash } from 'node:crypto';

/** SHA-256 of UTF-8 text with newlines normalized to LF. Windows CRLF must not drift frozen hashes. */
export const sha256NewlineStable = (bytes: Buffer | Uint8Array | string) => {
	const raw = typeof bytes === 'string' ? bytes : Buffer.from(bytes).toString('utf8');
	const lf = raw.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
	return createHash('sha256').update(lf, 'utf8').digest('hex');
};
