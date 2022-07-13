from math import ceil
import os
from os.path import exists
from datetime import datetime, time
from re import ASCII

FF8BYTES = 18446744073709551615      #VALOR INTEIRO DE FF PRA 8 BYTES

def clear():
    #clears terminal
    os.system('cls' if os.name == 'nt' else 'clear')

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

def Read_Folder(image, boot_info, isRoot):
    next_block = 0

    if isRoot:
        image.seek(24)

    while next_block != FF8BYTES:
        next_block = int.from_bytes(image.read(8), 'little')

        if isRoot:
            super_block_size = 1
            size_used = 32
        else:
            super_block_size = int.from_bytes(image.read(8), 'little')
            size_used = 16
        isRoot = False
        size_left = boot_info['block_size'] * super_block_size - size_used

        
        mini_block_attribute = image.read(1)
        folder_content = []
        while size_left:
            if mini_block_attribute == b'\x00':
                break
            thing_size = int.from_bytes(image.read(7), 'little')
            first_block = int.from_bytes(image.read(8), 'little')
            size_left -= 16
            thing_name = ''
            thing_attribute = mini_block_attribute
            mini_block_attribute = image.read(1)
            while mini_block_attribute == b'\x40' and size_left:
                thing_name += image.read(15).decode('ASCII')
                size_left -= 16
                mini_block_attribute = image.read(1)
            thing_name = thing_name.split(chr(0))[0]
            folder_content.append([thing_name, thing_size, first_block, thing_attribute])
    return folder_content

def ShowFolder(folder_content, image, boot_info):
    clear()

    max_name = 0
    for content in folder_content:
        if len(content[0])>max_name:
            max_name = len(content[0])+3

    for index in range(len(folder_content)):
        content = folder_content[index]
        line = str(index)+' - '
        if content[-1][0]//16 == 1:       #verifica se o nibble à esquerda é 1
            line += '/'+content[0]+' '*(max_name-len(content[0]))+str(content[1])+'B'
        else:
            line += content[0]+' '*(max_name-len(content[0]))+str(content[1])+'B'
        print(line)

    UserInterface(folder_content, image, boot_info)
    pass

def Startup():
    print('-'*27)
    print('| BEM-VINDO AO SUPERMINI! |')
    print('-'*27)
    cmd = input('Insira a ação desejada:\nA - Abrir uma imagem\nC - Criar uma imagem\n')
    while cmd.upper()!='A' and cmd.upper()!='C':
        cmd = input('Comando inválido. Digite novamente.\n')

    if cmd.upper() == 'A':
        filename = input('Digite o nome da imagem SuperMini que deseja acessar\n')
        while not exists(filename):
            filename = print('Arquivo não encontrado!')
        
        image = open(filename, 'rb+')
        boot_info = read_boot(image)
        root_content = Read_Folder(image, boot_info, True)
    elif cmd.upper() == 'C':
        CriarImagem()

    return image, boot_info, root_content

def OpenThing(folder_content, cmd, image, boot_info):
    thing_index = int(cmd[2:])
    image = WalkImage(image, boot_info, folder_content[thing_index][2])

    if folder_content[thing_index][-1][0]//16 == 1:
        folder_content = Read_Folder(image, boot_info, folder_content[thing_index][2]==0)
        ShowFolder(folder_content, image, boot_info)
    else:
        ShowFile(image, boot_info, folder_content, thing_index)

def UpdateBitmap(image, boot_info, blocks_used):
    image = WalkImage(image, boot_info, 1)
    for blocks in blocks_used:
        image.seek(boot_info['block_size'] + (blocks)//8)
        # write 1 to bitmap at position of blocks used 
        byte = image.read(1)
        byte = byte[0] | (1 << 7 - (blocks)%8)
        image.seek(boot_info['block_size'] + (blocks)//8)
        image.write(bytes([byte]))

def CreateBlockSet(image, boot_info, size):
    #bitmap_size is the number of blocks used by the bitmap
    # go to the bitmap
    image = WalkImage(image, boot_info, 1)
    # numbers of blocks needed to store the file
    blocks_needed = ceil((size + 16)/boot_info['block_size'])
    # list the starting block and sequence of free blocks next to it
    free_blocks = []
    free_blocks.append([])
    blocks_for_thing = []
    # all blocks are free are with value 0
    blocks_left = boot_info['blocks_quantity']
    set = 0
    i = 0
    checked = 0

    while blocks_left:
        #bitmap_byte read one byte at a time of the bitmap
        bitmap_byte = image.read(1)
        # checks each bit of the byte
        for j in range(8):
            if not blocks_left:
                break
        # checks if it is free and adds it to the list of free blocks
            if  (~bitmap_byte[0]) & (1 << 8-(j+1)):
                free_blocks[set].append(i*8+j)
            else:
                if free_blocks[set]:
                    set += 1
                    free_blocks.append([])
            blocks_left -= 1
        for j in range(checked, len(free_blocks)):
            if len(free_blocks[j]) >= blocks_needed:
                blocks_for_thing += free_blocks[j][:blocks_needed]
                blocks_for_thing.sort()
                UpdateBitmap(image, boot_info, blocks_for_thing)
                CreateBlocks(image, boot_info, blocks_for_thing)
                return blocks_for_thing
            checked = len(free_blocks[j]) - 1
        i += 1
    #sum all the elements inside free_blocks list
    sum = 0
    for i in range(len(free_blocks)):
        sum += len(free_blocks[i])
    if sum < blocks_needed:
        print("Não é possível armazenar todos os arquivos")
        return None


    #sort the list of lists of free blocks by the size of the list
    free_blocks.sort(key=len, reverse=True)
    size_get = 0
    for i in range(len(free_blocks)):
        size_get_iteration = min(size - size_get, len(free_blocks[i]) * boot_info['block_size'])
        size_get += size_get_iteration - 16
        blocks_get_iteration = ceil(size_get_iteration/boot_info['block_size'])
        blocks_for_thing += free_blocks[i][:blocks_get_iteration]
        if size_get >= size:
            blocks_for_thing.sort()
            UpdateBitmap(image, boot_info, blocks_for_thing)
            CreateBlocks(image, boot_info, blocks_for_thing)
            return blocks_for_thing

def CreateBlocks(image, boot_info, blocks_for_thing):
    first_block = blocks_for_thing[0]
    image = WalkImage(image, boot_info, first_block)
    superblock_size = 1
    for block in blocks_for_thing:
        # keep counting the sequence for a superblock
        if block == first_block + superblock_size:
            superblock_size += 1
        # if the sequence ended, write this superblock and go to the start of the next sequence
        else:
            image.write(int.to_bytes(block, 8, 'little'))
            image.write(int.to_bytes(superblock_size, 8, 'little'))
            superblock_size = 1
            image.seek(block * boot_info['block_size'])
            first_block = block
        
        #check all the blocks that are sequential
        image.seek(boot_info['block_size'] * block)
        image.write(bytes([0]*boot_info['block_size']))

def ReadFreeMiniblocks(image, boot_info, miniblocks_needed, current_block):
    next_block = 0 
    miniblocks_free = 0
    first_miniblock_free = None
    while next_block != FF8BYTES:
        next_block = int.from_bytes(image.read(8), 'little')
        if current_block == 0:
            superblock_size = boot_info['block_size']
            size_left = boot_info['block_size'] - 32
        else:
            superblock_size = int.from_bytes(image.read(8), byteorder='little')
            size_left = superblock_size * boot_info['block_size'] - 16
        count = 0
        while size_left:
            # save miniblock as a list of 16 bytes
            miniblock = image.read(16)
            # check if the first byte is 00
            if miniblock[0] == 0:
                miniblocks_free += 1
                if first_miniblock_free is None:
                    first_miniblock_free = count
            else:
                miniblocks_free = 0
                first_miniblock_free = None
            size_left -= 16
            count += 1
            if miniblocks_free == miniblocks_needed:
                return miniblocks_free, first_miniblock_free, current_block
        if next_block != FF8BYTES:
            current_block = next_block
    return miniblocks_free, first_miniblock_free, current_block

def WriteMiniBlock(image, type, size, block):
    image.write(type)
    image.write(int.to_bytes(size, 7, 'little'))
    image.write(int.to_bytes(block, 8, 'little'))

def WriteMiniBlockName(image, text):
    image.write(b'\x40')
    image.write(text.encode('ASCII'))
    image.write(b'\x00' * (15 - len(text)))

def CreateNewDir(image, boot_info, parent_block):
    blocks = CreateBlockSet(image, boot_info, 80)
    if blocks is None:
        print("Nao foi possivel alocar o diretório")
    else:
        image = WalkImage(image, boot_info, blocks[0])
        image.write(int.to_bytes(FF8BYTES, 8, 'little'))
        image.write(int.to_bytes(1, 8, 'little'))
        WriteMiniBlock(image, b'\x10', 0, blocks[0])
        WriteMiniBlockName(image, ".")
        WriteMiniBlock(image, b'\x10', 0, parent_block)
        WriteMiniBlockName(image, "..")
    return blocks[0]


def CreateDirectory(folder_content, cmd, image, boot_info):   #Lucas
    dir_name = cmd[2:]
    miniblocks_needed = 1 + (ceil(len(dir_name)/15))
    dir_size_needed = miniblocks_needed * 16
    # get the first byte and see if it is free, go on this until you find one
    # check if it has enough, if it doesn't, ask to create more blocks with the next
        # if you create a new one, then you need to update the next block(or check if you just allocated the next one and increase its size)

    current_block = folder_content[0][2]
    image = WalkImage(image, boot_info, folder_content[0][2])
    if folder_content[0][2] == 0:
        image.seek(24, 1)
    miniblocks_free, first_miniblock_free, current_block = ReadFreeMiniblocks(image, boot_info, miniblocks_needed, current_block)
    sequential = True

    if miniblocks_free < miniblocks_needed:
        # if you don't have enough, create more blocks
        blocks = CreateBlockSet(image, boot_info, dir_size_needed - miniblocks_free * 16)
        if blocks is None:
            print("Não é possível armazenar todos os arquivos")
            return

        # if blocks are sequential, increase the superblock size
        elif blocks[0] == folder_content[0][2] + superblock_size:
            image = WalkImage(image, boot_info, current_block)
            image.read(8)
            # to-do: discover the size of the superblock created and increase size of superblock
            # to-do: write this size of superblock to image
            image.write((superblock_size + len(blocks)).to_bytes(8, byteorder='little'))

            image = WalkImage(image, boot_info, blocks[0])
            next_block = image.read(8)
            superblock_size += int.from_bytes(image.read(8), byteorder='little')
            image = WalkImage(image, boot_info, blocks[0])
            image.write(int.to_bytes(0, 16, byteorder='little'))
            image = WalkImage(image, boot_info, current_block)
            image.write(int.to_bytes(next_block, 8, byteorder='little'))
            image.write(int.to_bytes(superblock_size, 8, byteorder='little'))
            last_miniblock = miniblocks_free[-1]
            #create a list incrementing by one
            miniblocks_free += [i for i in range(last_miniblock + 1, miniblocks_needed - miniblocks_free)]
        else:
            image = WalkImage(image, boot_info, current_block)
            next_block = blocks[0]
            image.write((next_block).to_bytes(8, byteorder='little'))
            superblock_size = int.from_bytes(image.read(8), byteorder='little')
            sequential = False

    # create the directory
    first_block_new_dir = CreateNewDir(image, boot_info, folder_content[0][2])

    name_len = len(dir_name)
    if sequential:
        # só escreve
        image.seek(current_block * boot_info['block_size'] + first_miniblock_free * 16 + 32) 

        WriteMiniBlock(image, b'\x10', 0, first_block_new_dir)
        while name_len > 15:
            WriteMiniBlockName(image, dir_name[:15])
            dir_name = dir_name[15:]
            name_len -= 15
        WriteMiniBlockName(image, dir_name[:name_len])
    else:
        if first_miniblock_free is None:
            image = WalkImage(image, boot_info, next_block * boot_info['block_size'])
            next_block = int.from_bytes(image.read(8), byteorder='little')
            superblock_size = int.from_bytes(image.read(8), byteorder='little')
        else:
            image = WalkImage(image, boot_info, current_block * boot_info['block_size'])
            next_block = int.from_bytes(image.read(8), byteorder='little')
            superblock_size = int.from_bytes(image.read(8), byteorder='little')
            image.seek(first_miniblock_free * 16, 1)
        
        WriteMiniBlock(image, b'\x10', 0, first_block_new_dir)
        size_left = superblock_size * boot_info['block_size'] - (first_miniblock_free + +2) * 16
        while name_len > 15:
            if size_left == 0:
                image = WalkImage(image, boot_info, next_block)
                next_block = int.from_bytes(image.read(8), byteorder='little')
                superblock_size = int.from_bytes(image.read(8), byteorder='little')
                size_left = superblock_size * boot_info['block_size'] - 16
            WriteMiniBlockName(image, dir_name[:min(15)])
            dir_name = dir_name[15:]
            name_len -= 15
            size_left -= 16

def TransferToDisc(folder_content, cmd, image, boot_info):    #Lucas
    # start all the variables needed
    file = b''
    file_number = int(cmd[2:])
    super_block_begin = folder_content[file_number][2]
    size_left = folder_content[file_number][1]
    image = WalkImage(image, boot_info, super_block_begin)

    # read all the blocks of the file and get the data in raw format
    next_block = 0
    while next_block != FF8BYTES and size_left:
        next_block = int.from_bytes(image.read(8), 'little')
        block_size = int.from_bytes(image.read(8), 'little')
        read_block = block_size * boot_info['block_size'] - 16
        file += image.read(min(read_block, size_left))
        size_left -= read_block

    # Duvida: se importar em pedir se o usuário deseja que seja escrito little endian ou big endian antes de escrever?
    # write file to disc as bytes
    filename = input('Digite o nome do arquivo em que deseja salvar\n')
    with open(filename, 'wb') as f:
        f.write(file)

def WriteToSuperMini(folder_content, cmd, image, boot_info):  #Igor
    pass

def FormatImg(folder_content, cmd, image, boot_info):         #Mahat
    pass

def CriarImagem():          #Mahato
    pass

def ShowHelp(folder_content, cmd, image, boot_info):     
    clear() 
    print('Todos os comandos seguem a seguinte sintaxe: \'X args\'')
    print('Substitua X pela letra correspondente ao comando desejada e args pelos parâmetros necessários ao comando.')
    print('Não esqueça de colocar um espaço entre o comando e seus parâmetros!')
    print()
    print('Os seguintes comandos podem ser utilizados:')
    print('A - Abrir arquivo/diretório. O parâmetro passado deve ser o índice exibido no diretório atual')
    print('    Ex: A 12')
    print('C - Criar diretório. O parâmetro passado deve ser o nome do diretório.')
    print('    Ex: C nova_pasta')
    print('E - Escrever um arquivo no SuperMini. O parâmetro deve ser o nome do arquivo a ser lido do disco para o SuperMini.')
    print('    Ex: E teste.txt. ATENÇÃO: O arquivo a ser escrito no SuperMini deve se encontrar na mesma pasta que a aplicação')
    print('F - Formatar. Nenhum parâmetro é passado.')
    print('    Ex: F')
    print('S - Sair. Encerra a aplicação. Nenhum parâmetro é passado.')
    print('    Ex: S')
    print('T - Transferir do SuperMini para o disco. O parâmetro deve ser o índice do arquivo a ser transferido.')
    print('    Ex: T 12')
    print()
    
    back_input = input('Insira X para voltar ao diretório anterior.\n')
    while back_input.upper() != 'X':
        back_input = input('Insira X para voltar ao diretório anterior.\n')
    
    ShowFolder(folder_content, image, boot_info)
    pass

def Fechar(folder_content, cmd, image, boot_info):
    clear()
    print('Obrigado por utilizar o SuperMini!')
    now = datetime.now().time()
    if now >= time(5,00) and now <= time(12,00): 
        print('++++++Tenha um ótimo dia!++++++')
    elif now > time(12,00) and now <= time(18,00): 
        print('******Tenha uma ótima tarde!******')
    else:
        print('------Tenha uma ótima noite!------')
    
    exit()

def UserInterface(folder_content, image, boot_info):
    print('-------------------------------------------')
    print('Insira um comando. Insira H para ver ajuda.')
    
    commands = ['A', 'C', 'E', 'F', 'H', 'S', 'T']
    #Abrir, Criar Diretorio, Escrever no SuperMini, Formatar, Transferir para disco
    cmd = input()

    while cmd[0].upper() not in commands or (cmd[0].upper()=='A' and int(cmd[2:])>=len(folder_content)):
        cmd = input('Comando inválido. Digite novamente.\n')
    
    command_dict = {
        'A': OpenThing,
        'C': CreateDirectory,
        'E': WriteToSuperMini,
        'F': FormatImg,
        'H': ShowHelp,
        'S': Fechar,
        'T': TransferToDisc
    }

    command_dict[cmd[0].upper()](folder_content, cmd, image, boot_info)
        
    pass

def ShowFile(image, boot_info, folder_content, thing_index):
    next_block = 0
    size_in_bytes = folder_content[thing_index][1]
    content = ''

    while next_block != FF8BYTES:
        next_block = int.from_bytes(image.read(8), 'little')
        super_block_size = int.from_bytes(image.read(8), 'little')
        size_left_in_block = boot_info['block_size'] * super_block_size - 16

        content += image.read(min(size_in_bytes, size_left_in_block)).decode('ASCII')

        size_in_bytes -= size_left_in_block

    print(content)

    UserInterface(folder_content, image, boot_info)

    pass

def WalkImage(image, boot_info, block):
    image.seek(block * boot_info['block_size'])
    return image

def main():
    image, boot_info, root_content = Startup()
    ShowFolder(root_content, image, boot_info)


if '__main__' == __name__:
    main()