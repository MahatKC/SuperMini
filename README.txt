Feito por Igor França, Lucas Veit e Mateus Karvat.
    
    A tela inicial da aplicação permite que uma imagem pré-existente seja selecionada ou uma imagem seja criada:

---------------------------
| BEM-VINDO AO SUPERMINI! |
---------------------------
Insira a ação desejada:
A - Abrir uma imagem
C - Criar uma imagem

    Para abrir uma imagem, o nome completo do arquivo (incluindo a extensão .img) deve ser passado ao sistema e a imagem
    deve estar formata no padrão SuperMini.

    Após abrir a imagem, o conteúdo de seu diretório raiz é exibido. Caso o usuário deseja acessar demais funcionalidades,
    pode inserir o comando H, que abre a tela de ajuda:

Todos os comandos seguem a seguinte sintaxe: 'X args'
Substitua X pela letra correspondente ao comando desejada e args pelos parâmetros necessários ao comando.
Não esqueça de colocar um espaço entre o comando e seus parâmetros!

Os seguintes comandos podem ser utilizados:
A - Abrir arquivo/diretório. O parâmetro passado deve ser o índice exibido no diretório atual
    Ex: A 12
C - Criar diretório. O parâmetro passado deve ser o nome do diretório.
    Ex: C nova_pasta
E - Escrever um arquivo no SuperMini. O parâmetro deve ser o nome do arquivo a ser lido do disco para o SuperMini.
    Ex: E teste.txt. ATENÇÃO: O arquivo a ser escrito no SuperMini deve se encontrar na mesma pasta que a aplicação
F - Formatar. Nenhum parâmetro é passado.
    Ex: F
S - Sair. Encerra a aplicação. Nenhum parâmetro é passado.
    Ex: S
T - Transferir do SuperMini para o disco. O parâmetro deve ser o índice do arquivo a ser transferido.
    Ex: T 12