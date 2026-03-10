#jesus lopez
#1002103351

import time
from Crypto.Cipher import DES

def meet_in_the_middle(P_1, P_2, C_1, C_2, test_range=2**16):
    time_start = time.time()
    store_values = {}

    for k1 in range(test_range):
        k1_bytes = k1.to_bytes(8, 'big')
        cipher = DES.new(k1_bytes, DES.MODE_ECB)
        x = cipher.encrypt(P_1) 
        store_values[x] = k1

    for k2 in range(test_range):
        k2_bytes = k2.to_bytes(8, 'big')
        cipher = DES.new(k2_bytes, DES.MODE_ECB)
        x_prime = cipher.decrypt(C_1)

        if x_prime in store_values:
            k1 = store_values[x_prime]
            
            cipher_k1 = DES.new(k1.to_bytes(8, 'big'), DES.MODE_ECB)
            
            if cipher.encrypt(cipher_k1.encrypt(P_2)) == C_2:
                time_end = time.time()
                print(f"Keys: k1 = {k1}, k2 = {k2} \nTime: {time_end - time_start:.2f} seconds")
                return k1, k2

P_1, P_2 = b'HEWEFVJK', b'IJDLKSFE'

key_1, key_2 = 3798, 8392

key_1_bytes, key_2_bytes = key_1.to_bytes(8, 'big'), key_2.to_bytes(8, 'big')

test_range = 2**16


C_1= DES.new(key_2_bytes, DES.MODE_ECB).encrypt(DES.new(key_1_bytes, DES.MODE_ECB).encrypt(P_1))
C_2 = DES.new(key_2_bytes, DES.MODE_ECB).encrypt(DES.new(key_1_bytes, DES.MODE_ECB).encrypt(P_2))

meet_in_the_middle(P_1, P_2, C_1, C_2, test_range)