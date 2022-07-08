from logging import root
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
        
        image = open(filename, 'rb')
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

def CreateDirectory(folder_content, cmd, image, boot_info):   #Lucas
    pass

def TransferToDisc(folder_content, cmd, image, boot_info):    #Lucas
    pass

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