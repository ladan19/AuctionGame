# encoding: utf-8

from lances import Bid
from leiloes import Auction
from usuarios import User

client_commands = [
    'apaga_usuario',
    'entrar_leilao',
    'enviar_lance',
    'lanca_produto',
    'lista_leiloes',
    'sair',
    'sair_leilao',
]


client_commands_anonymous = [
    'adiciona_usuario',
    'faz_login',
    'lista_leiloes',
]


server_commands = [
    'listagem',
    'ok',
    'not_ok',
    'lance',
    'fim_leilao',
    'contato_vendedor',
    'contato_cliente'
]



# Abaixo ficarão as funções para lidar com
#comandos de usuários logados e do servidor


# Comandos de usuários logados

def lista_leiloes(user=None, data=None):
    # Função para listar os leilões. Carrega todos os leilões em uma
    # lista e envia para o usuário.
    auctions = Auction.all() #reotrno a lista com todos os leilões cadastrados

    msg = '\n'.join(str(a) for a in auctions) + '\nok' #join 

    return msg


def apaga_usuario(user, data):
    # Função para apagar o usuário. Confere se a senha e o nome batem
    # com a senha e o nome do usuário logado. Se são iguais, delete
    # o usuário.
    command, name, password = data.split(',')

    if user.name == name and user.password == password:
        user.delete() #está no user
        return True

    raise Exception('not_ok')


def entrar_leilao(user, data):
    # Função para entrar no leilão. Carrega o objeto Auction e adiciona
    # o id do usuário logado à lista users. Desta forma é possível saber
    # quais usuários estão 'seguindo' o leilão.
    command, auction_id = data.split(',')
    auction = Auction.load(int(auction_id)) 

    if user.id not in auction.users: #lista de usuário participando do leilão ( não estiver na lista de leilão) ele entra
        auction.users.append(user.id) 
        auction.save()
        return True

    raise Exception('not_ok')


def enviar_lance(user, data):
    # Função para enviar o lance. Verifica se o valor passado
    # é maior do que o valor mínimo. Se for, registra um novo
    # objeto Bid referenciando o usuário, o leilão e o valor.
    # Envia uma mensagem de volta para o controle do servidor
    # contendo os lances já feitos para os usuários 'seguidores'
    # do leilão.
    command, auction_id, value = data.split(',')
    auction_id = int(auction_id)
    value = float(value) #número com virgula
    auction = Auction.load(auction_id) #carregar o leilão

    if auction.open and value >= auction.min_bid and user.id in auction.users:
        bid = Bid.new(user.id, auction_id, float(value))
        auction.last_bid = bid.id #identificar o último lance no leilão
        auction.save() #salvar

        for u in User._logados: #u é cada usuario na lista de logados e user é o usuario logado
            if u.id in auction.users and u.id != user.id: #u.id e acution.user verificar quais usuários logados estão participando do leilão
                u.notify('%d,%s,%f,%d,%d\n' % (                 #u.id != user.id verifica dentro dos usuario logados se ele não é o usuario que enviou o comando
                    auction_id, user.name, bid.value, len(auction.users), 
                    len(Bid.filter_by_auction(auction_id)))) #

        return True

    raise Exception('not_ok')


def lanca_produto(user, data):
    # Registra um novo produto para leilão. Cria um objeto Auction com os dados
    # e salva no arquivo de leilões.
    data = data.split(',') 
    name = data[1]
    description = data[2]
    min_bid = float(data[3])
    day = int(data[4])
    month = int(data[5])
    year = int(data[6])
    hour = int(data[7])
    minute = int(data[8])
    second = int(data[9])
    max_timeout = int(data[10])

    auction = Auction.new(user.id, name, description, min_bid, day, month,
                          year, hour, minute, second, max_timeout)

    auction.start()

    return True


def sair(user, data):
    # Faz logout do usuário.
    user.answer('ok')
    user.logout()
    return True


def sair_leilao(user, data):
    # Retira o usuário daquele leilão, como um 'unfollow' no leilão.
    command, auction_id = data.split(',')
    auction = Auction.load(int(auction_id))

    auction.users.remove(user.id) #remove é uma função da lista do python
    auction.save()
    return True


client_functions = { #dicionario, comando mapeando as funções (as defs)
    'lista_leiloes': lista_leiloes,
    'apaga_usuario': apaga_usuario,
    'entrar_leilao': entrar_leilao,
    'enviar_lance': enviar_lance,
    'lanca_produto': lanca_produto,
    'sair': sair,
    'sair_leilao': sair_leilao
}
