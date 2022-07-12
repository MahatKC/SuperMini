from math import ceil
import os
from os.path import exists
from datetime import datetime, time

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
    print(blocks_used)
    for blocks in blocks_used:
        print((blocks)//8)
        image.seek(boot_info['block_size'] + (blocks)//8)
        # write 1 to bitmap at position of blocks used 
        byte = image.read(1)
        byte = byte[0] | (1 << 7 - (blocks)%8)
        image.seek(boot_info['block_size'] + (blocks)//8)
        image.write(bytes([byte]))

def FindBlockSet(folder_content, cmd, image, boot_info, size):
    #bitmap_size is the number of blocks used by the bitmap
    # bitmap_indexes = boot_info['blocks_quantity']
    # go to the bitmap
    image = WalkImage(image, boot_info, 1)
    # numbers of blocks needed to store the file
    blocks_needed = ceil((size + 16)/boot_info['block_size'])
    # list the starting block and sequence of free blocks next to it
    free_blocks = []
    free_blocks.append([])
    blocks_for_thing = []
    # all blocks are free are with value 0
    #blocks_left = boot_info['blocks_quantity']
    blocks_left = 20
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
                UpdateBitmap(image, boot_info, blocks_for_thing)
                return blocks_for_thing
            print(len(free_blocks[j]), checked)
            checked = len(free_blocks[j]) - 1
        i += 1
    #sum all the elements inside free_blocks list
    print(free_blocks)
    sum = 0
    for i in range(len(free_blocks)):
        sum += len(free_blocks[i])
    if sum < blocks_needed:
        print("Nao é possível armazenar todos os arquivos")
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
            UpdateBitmap(image, boot_info, blocks_for_thing)
            return blocks_for_thing

def CreateDirectory(folder_content, cmd, image, boot_info):   #Lucas
    image = WalkImage(image, boot_info, 1)
    x = image.read(30)
    print(x)
    x = FindBlockSet(folder_content, cmd, image, boot_info, 500)
    print(x)
    image = WalkImage(image, boot_info, 1)
    x = image.read(30)
    print(x)
    pass

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

    # Duvida: se importar com ser little endian ou big endian na hora de escrever?
    # write file to disc as bytes
    filename = input('Digite o nome do arquivo em que deseja salvar\n')
    with open(filename, 'wb') as f:
        f.write(file)

def WriteToSuperMini(folder_content, cmd, image, boot_info):  #Igor
    pass

def MenuNewImg():
    pass

def FormatImg(folder_content, cmd, image, boot_info):         #Mahat
    print('ATENÇÃO: A imagem atual será formatada e todos os dados serão perdidos.')
    choice = input('Deseja continuar? (S/N)')
    if choice != 'S':
        ShowFolder(folder_content, image, boot_info)
    else:
        clear()
        blocks_quantity, block_size = MenuFormat(boot_info)
        print(blocks_quantity, block_size)

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

def CriarImagem():          #Mahato
    image_name = input('Insira o nome da imagem que deseja criar com sufixo \'.img\'. Ex: \'teste.img\'\n')

    print('Insira o número de blocos da imagem SuperMini.')
    blocks_quantity = input('O número deve ser entre 4 e 2^64.\n')
    while blocks_quantity<4 or blocks_quantity>2**64:
        blocks_quantity = input('O número deve ser entre 4 e 2^64.\n')

    print('\nInsira o expoente de 2 para o tamanho de bloco da imagem SuperMini.')
    block_size = input('O número deve ser entre 9 (512 B/bloco) e 12 (4096 B/bloco).\n')
    while block_size<9 or block_size>12:
        block_size = input('O número deve ser entre 9 (512 B/bloco) e 12 (4096 B/bloco).\n')
    
    pass

def MenuFormat(boot_info):
    size = boot_info['blocks_quantity']*boot_info['block_size']
    current_size = 0
    while current_size != size:
        print('Insira o número de blocos da imagem SuperMini.')
        current_quantity = boot_info['blocks_quantity']
        print(f'(O atual número é de {current_quantity} blocos)')
        blocks_quantity = input('O número deve ser entre 4 e 2^64.\n')
        while blocks_quantity<4 or blocks_quantity>2**64:
            blocks_quantity = input('O número deve ser entre 4 e 2^64.\n')

        print('\nInsira o expoente de 2 para o tamanho de bloco da imagem SuperMini.')
        current_quantity = boot_info['block_size']
        print(f'(O atual tamanho é de 2^{current_quantity}({2**current_quantity} B/bloco))')
        block_size = input('O número deve ser entre 9 (512 B/bloco) e 12 (4096 B/bloco).\n')
        while block_size<9 or block_size>12:
            block_size = input('O número deve ser entre 9 (512 B/bloco) e 12 (4096 B/bloco).\n')
        
        current_size = blocks_quantity*block_size
        if current_size!=size:
            print(f'ERRO! O tamanho final do disco deve ser de {size} B! O tamanho informado é de {current_size} B.')
            clear()
    
    return blocks_quantity, block_size

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

def main():
    image, boot_info, root_content = Startup()
    ShowFolder(root_content, image, boot_info)


if '__main__' == __name__:
    main()