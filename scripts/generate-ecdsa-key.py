import sys

sys.path.append('lib')

import ecdsa

sk = ecdsa.SigningKey.generate()

print(sk.to_string().hex())
