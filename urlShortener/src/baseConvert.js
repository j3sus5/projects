const ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const BASE = ALPHABET.length;

function encode(num) {
  if (num === 0) return ALPHABET[0];
  let encoded = '';
  while (num > 0) {
    encoded = ALPHABET[num % BASE] + encoded;
    num = Math.floor(num / BASE);
  }
  return encoded;
}

function decode(str) {
  let num = 0;
  for (const char of str) {
    num = num * BASE + ALPHABET.indexOf(char);
  }
  return num;
}

module.exports = { encode, decode };