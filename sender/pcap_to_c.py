def to_int_array(pac):
   tmp = str(pac).encode('hex')
   tmp = [x+y for x,y in zip(tmp[0::2], tmp[1::2])]
   return map(lambda x : int(x,16), tmp)
