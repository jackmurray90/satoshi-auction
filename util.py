from hashlib import sha256

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def decode_base58(bc, length):
  n = 0
  for char in bc:
    n = n * 58 + digits58.index(char)
  return n.to_bytes(length, 'big')

def valid_bitcoin_address(bc):
  if len(bc) < 25 or len(bc) > 34:
    return False
  if bc[0] != '1' and bc[0] != '3':
    return False
  try:
    bcbytes = decode_base58(bc, 25)
    return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]
  except Exception:
    return False
