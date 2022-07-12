from math import ceil
x='1111100100'
print(int(x,2).to_bytes(ceil(len(x)/8), byteorder='little'))

y=1
print(x+'2'*y)

root_miniblock_atribute = 11840
print(root_miniblock_atribute.to_bytes(16, byteorder='little'))

