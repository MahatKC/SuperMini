from tabnanny import check


x = b'\x00\x00\x00\x00\x00\x00\x00\x00'
blocks_left = 16
bitmap = [b'\xF0',b'\xE8']


def UpdateBitmap(image, boot_info, block_number):
    image = 

    global bitmap
    blocks_left = boot_info['blocks_quantity']
    bitmap = [b'\xF0',b'\xE8']
    for i in range(boot_info['bitmap_size']):
        bitmap.append(image.read(1))
        blocks_left -= 8
        if blocks_left == 0:
            break
    return bitmap

blocks_needed = 2

free_blocks = []
j = 0
set = 0
free_blocks.append([])
checked = 0

blocks_for_thing = []
while blocks_left:
    #bitmap_byte read one byte at a time of the bitmap
    bitmap_byte = bitmap[j]
    # checks each bit of the byte
    for i in range(8):
        if not blocks_left:
            break
        # checks if it is free and adds it to the list of free blocks
        if  (~bitmap_byte[0]) & (1 << 8-(i+1)):
            # print(i, bitmap_byte[0] & (1 << 8-(i+1)))
            free_blocks[set].append(j*8+i)
        else: #if its not free, create a new list of block sequence
            if free_blocks[set]:
                set += 1
                free_blocks.append([])
                # for each new block, you add 16 bits to the size of file, because its the cost of the pointers
        blocks_left -= 1
    j +=1
    for i in range(checked, len(free_blocks)):
        if len(free_blocks[i]) >= blocks_needed:
            blocks_for_thing += free_blocks[i][:blocks_needed] # return the amount found
            #get the bitmap to be updated to 1
            print(blocks_for_thing)
            exit()


        checked += 1
    
#sort the list of lists of free blocks by the size of the list
free_blocks.sort(key=len, reverse=True)
blocks_get = 0
for i in range(len(free_blocks)):
    blocks_get_iteration = min(blocks_needed - blocks_get, len(free_blocks[i]))
    blocks_get += blocks_get_iteration
    blocks_for_thing += free_blocks[i][:blocks_get_iteration]
    if blocks_get >= blocks_needed:
        break
    
print(blocks_for_thing)