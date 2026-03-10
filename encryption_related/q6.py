#jesus lopez
#1002103351

from Crypto.Cipher import DES
import binascii

def generate_prns_ofb():

    key = b'7rhje28r'
    v = b'is43nmfk'
    cipher = DES.new(key, DES.MODE_OFB, v)
    bytes = 32
    prns = cipher.encrypt(b'\x00' * bytes)

    count_0s, count_1s = 0, 0

    for byte in prns:
        for i in range(8):
            if byte >> i & 1:
                count_1s += 1
            else:
                count_0s += 1
    print(f'Output block: {binascii.hexlify(prns)}')
    print(f'Number of 0s: {count_0s}\nNumber of 1s: {count_1s}')

generate_prns_ofb()
