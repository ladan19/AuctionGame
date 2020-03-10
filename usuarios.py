# encoding: utf-8

from __future__ import print_function #Comando pra poder usar o função do em uma atualização no futuro

import os
import json
import threading

import lances
import leiloes


# Nome do arquivo referente aos usuários e lock usada para
# sincronização na leitura e escrita do mesmo
FILENAME = os.path.splitext(__file__)[0] + '.json'
FILELOCK = threading.RLock() #semaforo


class User(object):
    # Classe responsável por salvar e carregar informações dos usuários.
    # Existe uma lista interna a fim de manter um registro dos
    # usuários logados.
    # Cada usuário, por padrão, deverá ter 2 sockets vinculados no
    # momento de sua conexão. Um é o socket principal, que envia
    # mensagens ao servidor e recebe sua resposta imediata, e o
    # outro é o socket recebedor, que recebe mensagens com informações
    # como novos lances em algum produto.

    # Lista dos usuários logados
    _logados = [] 


    @classmethod
    def get_user_by_socket_port(cls, port):
        # Este método procura um usuário pelo endereço fornecido.
        # Se o endereço não remete a nenhum usuário, lança uma
        # exceção.
        # Serve principalmente para vincular um usuário já conectado
        # ao seu socket recebedor.
        for u in cls._logados:
            if u.sender.getpeername()[1] == port: #getpeername metodo do socket que retorno uma lista em que o primeiro elemte é o host e o segundo é a porta
                return u

        raise Exception('Nenhum usuário disponível para o endereço especificado')

    @classmethod
    def send_to_all(cls, what):
        pass 

    @classmethod
    def signup(cls, socket, name, phone, address, email, password):
        # Tenta registrar com os dados providenciados.
        # Lança uma exceção se um usuário com este nome já existir.

        # É necessário o uso da Lock neste ponto a fim de não atrapalhar outra
        # thread numa eventual escrita no arquivo.
        with FILELOCK: #trava o acesso ao arquivo
            with open(FILENAME) as f:
                users = json.load(f)

            # Corre a lista verificando se o usuário já existe
            for u in users:
                if u['name'] == name:  # Usuário já existe
                    raise Exception('Usuário especificado já existe')

            # Cria o id do novo usuário a partir do último id ou
            # atribui 1 se for o primeiro usuário do sistema
            try:
                id = users[-1]['id'] + 1 #O id do próximo usuário é +1 ---- [-1] último da lista
            except IndexError:
                id = 1

            # Cria e adiciona o dicionário com os dados do usuário
            # à lista de usuários
            user = {'name': name, 'phone': phone, 'address': address,
                    'email': email, 'password': password, 'id': id}
            users.append(user)

            # Escreve no arquivo a lista atualizada de usuários
            with open(FILENAME, 'w') as f: #write (w)
                json.dump(users, f)

        # Loga e retorna o usuário
        user = cls(sender_socket=socket, **user) #######
        cls._logados.append(user)
        return user

    @classmethod
    def login(cls, socket, name, password):
        # Tenta fazer login com as credenciais providenciadas.
        # Lança uma exceção se não encontrar.
        user = None #criar uma variavel vazia 

        # É necessário o uso da Lock neste ponto a fim de não atrapalhar outra
        # thread numa eventual escrita no arquivo.
        with FILELOCK:
            with open(FILENAME) as f:
                users = json.load(f)

        for u in users:
            if u['name'] == name and u['password'] == password:
                user = cls(sender_socket=socket, **u) ##############

        if user is not None:
            cls._logados.append(user) #cls = classe user
            return user

        raise Exception('Usuário inexistente.')

    @classmethod
    def load(cls, id): #carregar os dados do usuário sem fazer login, usado no leilão 
        with FILELOCK:
            with open(FILENAME) as f:
                users = json.load(f)

            for u in users:
                if u['id'] == id:
                    return cls(sender_socket=None, **u)  ########

        raise Exception('Usuário não encontrado.')

    def __init__(self, id, name, phone, address, email, password,
                 sender_socket, receiver_socket=None): #inicializa o objeto usuário
        self.id = id
        self.name = name
        self.phone = phone
        self.address = address
        self.email = email
        self.password = password
        self.sender = sender_socket
        self.receiver = receiver_socket

    def __str__(self): 
        return self.name #

    def bind_receiver_socket(self, socket):
        self.receiver = socket #Acoplar o socket recebedor 

    def logout(self):
        self._logados.remove(self) #remove da lista
        self.sender.close()
        self.receiver.close()

    def recv(self, bs=1024):
        # envia e recebe ao mesmo tempo
        return self.sender.recv(bs) #só receber

    def answer(self, text):
        # envia e recebe ao mesmo tempo
        self.sender.send(text) #enviar o texto pra ele, usuário como resposta a algum comando dele (ok, not_ok)

    def notify(self, text):
        # envia e recebe ao mesmo tempo
        self.receiver.send(text) #enviar pro socket receber dele, recebe as notificações do leilão 

    def delete(self):
        # Aplica a deleção de um usuário do sistema. Com isso, todos os
        # leilões e lances desse usuário também são excluídos.
        auctions = leiloes.Auction.filter_by_user(self.id)
        for a in auctions:
            a.delete() #

        bids = lances.Bid.filter_by_user(self.id) #deleta os lances
        for b in bids:
            b.delete()

        with FILELOCK:
            # abre o arquivo
            with open(FILENAME) as f:
                users = json.load(f)

            # percorre até chegar neste usuário e remove da lista
            for u in users:
                if u['id'] == self.id:
                    users.remove(u)
                    break

            # salva no arquivo
            with open(FILENAME, 'w') as f:
                json.dump(users, f)

        self.logout()


# Abaixo é feito o preparo do arquivo de usuários.
# Verifica-se se o arquivo existe;
#   Se não existe, cria.

if not os.path.exists(FILENAME):
    with open(FILENAME, 'w') as f:
        print('[]', file=f)
        # Escreve no arquivo uma "lista" json vazia.
        # Desta forma, deixamos o servidor preparado para ler e até mesmo
        # escrever json no arquivo.
