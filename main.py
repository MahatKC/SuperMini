from math import ceil

def read_boot(image):
    name = image.read(7)
    blocks_quantity = int.from_bytes(image.read(8), 'little')
    block_size = 2**int.from_bytes(image.read(1), 'little') 
    boot_pointer = int.from_bytes(image.read(8), 'little')
    bitmap_size = ceil(blocks_quantity/ (8* block_size))
    dict = {'name': name, 
        'blocks_quantity': blocks_quantity, 
        'block_size' : block_size, 
        'boot_pointer' : boot_pointer,
        'bitmap_size' : bitmap_size}
    return dict

def show_folder(image, boot_info, isRoot):
    next_block = int.from_bytes(image.read(8), 'little')
    if isRoot:
        super_block_size = 1
        size_used = 32
    else:
        super_block_size = int.from_bytes(image.read(8), 'little')
        size_used = 16
    size_left = boot_info['block_size'] * super_block_size - size_used

    mini_block_attribute = image.read(1)
    while size_left:
        if mini_block_attribute == b'\x00':
            break
        thing_size = int.from_bytes(image.read(7), 'little')
        first_block = int.from_bytes(image.read(8), 'little')
        size_left -= 16
        thing_name = ''
        mini_block_attribute = image.read(1)
        while mini_block_attribute == b'\x40' and size_left:
            thing_name += image.read(15).decode('ASCII')
            size_left -= 16
            mini_block_attribute = image.read(1)
        print(thing_name, thing_size, first_block)



    pass


def main():
    image = open('superMINI.img', 'rb')
    boot_info = read_boot(image)
    show_folder(image, boot_info, True)
    image.seek(3*512)
    show_folder(image, boot_info, False)



if '__main__' == __name__:
    main()