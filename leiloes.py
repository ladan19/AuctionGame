# encoding: utf-8

from __future__ import print_function

import os
import json
import time
import threading
from datetime import datetime, timedelta

from lances import Bid
from usuarios import User


FILENAME = os.path.splitext(__file__)[0] + '.json'
FILELOCK = threading.RLock()


class Auction(object):
    @classmethod
    def new(cls, user_id, name, description, min_bid, day, month, year, hour,
            minute, second, max_timeout):
        # Cria um novo leilão com os dados especificados
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

            try:
                id = auctions[-1]['id'] + 1
            except IndexError:
                id = 1

            start_date = (year, month, day, hour, minute, second)

            a = cls(id, user_id, name, description, min_bid, start_date,
                    max_timeout)

            a.save()

        return a

    @classmethod
    def load(cls, id):
        # Carrega o leilão cujo id é o especificado nos argumentos
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

        for a in auctions:
            if a['id'] == id:
                return cls(a['id'], a['user_id'], a['name'], a['description'],
                           a['min_bid'], a['start_date'], a['max_timeout'],
                           a['last_bid'], a['users'], a['open'])

        raise Exception('Leilão não encontrado.')

    @classmethod #classmethod a nível de classe, ####
    def filter_by_user(cls, id):
        # Filtra leilões a partir do id de um usuário.
        # Retorna uma lista de leilões cujos user_id === id.
        auction_list = []
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

            for a in auctions:
                if a['user_id'] == id:
                    auction_list.append(cls(
                        a['id'], a['user_id'], a['name'], a['description'],
                        a['min_bid'], a['start_date'], a['max_timeout'],
                        a['last_bid'], a['users'], a['open']))

        return auction_list

    @classmethod
    def all(cls): #lista leiloes
        # Retorna todos os leilões presentes no sistema, abertos
        # ou não.
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

        return [cls(a['id'], a['user_id'], a['name'], a['description'],
                    a['min_bid'], a['start_date'], a['max_timeout'],
                    a['last_bid'], a['users'], a['open']) for a in auctions]

    def __init__(self, id, user_id, name, description, min_bid, start_date,
                 max_timeout, last_bid=None, users=None, open=False):
        # Método inicializador do nosso Leilão.
        # Convetendo os dados do json para python e assim facilitando a manipulação.
        
        self.id = id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.min_bid = min_bid
        self.start_date = start_date
        self.max_timeout = max_timeout
        self.last_bid = last_bid
        self.users = [] if users is None else users #
        self.open = open

    def __str__(self):
        # Método especial __str__. Retorna uma string legível
        # do objeto quando usado em instruções print, por exemplo.
        return '%d,%s,%s,%.2f,%d,%d,%d,%d,%d,%d,%d,%s' % (
            (self.id, self.name, self.description, self.min_bid) +
            tuple(self.start_date) + (self.max_timeout, self.user()) #lista_leiloes .2f casa decimais
        )

    def user(self):
        # Retorna o objeto User associado ao criador deste leilão.
        return User.load(self.user_id) #pra pegar o nome pra def _str_

    def save(self):
        # Converte os dados do objeto Auction em uma estrutura de dicionário e salva em um arquivo json.
        # Assim como nos métodos de loading,
        # este método faz uso do lock (semáforo) para ler do e escrever para
        # o arquivo.
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

            for a in auctions:
                if a['id'] == self.id:
                    break
            else:
                a = {'id': self.id}
                auctions.append(a)

            a['name'] = self.name
            a['user_id'] = self.user_id
            a['description'] = self.description
            a['min_bid'] = self.min_bid
            a['start_date'] = self.start_date
            a['max_timeout'] = self.max_timeout
            a['last_bid'] = self.last_bid
            a['users'] = self.users
            a['open'] = self.open

            with open(FILENAME, 'w') as f:
                json.dump(auctions, f)

    def time_to_start(self):
        # Retorna o tempo em segundos até o início do leilão
        start_date = datetime(*self.start_date) #é uma lista contendo ano, mes dia hora ....
        return start_date - datetime.now()

    def closes_in(self):
        # Retorna o tempo em segundos para terminar o leilão
        if self.last_bid is None: 
            return None

        diff = datetime.now() - datetime(*Bid.load(self.last_bid).bid_date) #tempo 
        max_timeout = timedelta(seconds=self.max_timeout)
        seconds_remaining = (diff - max_timeout).total_seconds() #

        return abs(seconds_remaining)

    def delete(self):
        # O primeiro passo é deletar todos os lances feitos neste
        # leilão
        bids = Bid.filter_by_auction(self.id)

        for b in bids:
            b.delete()

        # Depois prosseguimos para a deleção do leilão em si,
        # assim como feito na deleção dos lances
        with FILELOCK:
            with open(FILENAME) as f:
                auctions = json.load(f)

            for a in auctions:
                if a['id'] == self.id:
                    break

            auctions.remove(a)  #lista do python

            with open(FILENAME, 'w') as f:
                json.dump(auctions, f)

    def start(self):
        # Essa função cria a thread com a contagem regressiva para a
        # abertura do leilão, e conta os segundos antes de fechar.
        # A thread é iniciada com a função _run abaixo.
        t = threading.Thread(target=_run, args=(self.id,))
        t.daemon = True #caso aperto ctrl+c pra thread não travar
        t.start()

	#Um contador dentro da def para o termino do leilão 
def _run(auction_id):
    a = Auction.load(auction_id)
    seconds = a.time_to_start().total_seconds()
    print(seconds)
    time.sleep(seconds) #espera até o inicio do leilão
    a = Auction.load(auction_id) #carrega novamente a auction
    a.open = True
    a.save()
    #Envia para todos os usuários logados o leilão que abriu
    for u in User._logados:
        if u.id in a.users:
            u.notify('Leilao aberto:\n%s\n> ' % a)

    a = Auction.load(auction_id)
    while True:
        last_bid = a.last_bid #leilao
        timeout = a.closes_in() #tempo pra ele fechar

        if timeout is None:
            timeout = a.max_timeout #se não houver lance, ele fecha com o max_timeout

        print(timeout)
        time.sleep(timeout)

        a = Auction.load(auction_id)
        if last_bid == a.last_bid:  # Ninguém fez nenhum lance e o tempo acabou
            break

    a.open = False
    a.save()

    highest_bid = sorted(
        Bid.filter_by_auction(a.id), key=lambda b: b.value, reverse=True)[0] #sorted pela uma lista e ele devolve uma lista ordenada 
#lambda serve pra definir pelo oq o sorted vai ordenadar os lances, nesse casa é o valor
    for u in User._logados:
        if u.id in a.users:
            u.notify(
                'fim_leilao,%d,%.2f,%s' %
                (a.id, highest_bid.value, User.load(highest_bid.user_id).name))


# Abaixo é feito o preparo do arquivo de leilões.
# Verifica-se se o arquivo existe;
#   Se não existe, cria.
#Semaforo nessa parte deu problema, acredito que seja executado antes de alguma escrita ou coisa do tipo
if not os.path.exists(FILENAME):
    with open(FILENAME, 'w') as f:
        print('[]', file=f)
        # Escreve no arquivo uma "lista" json vazia.
        # Desta forma, deixamos o servidor preparado para ler e até mesmo
        # escrever json no arquivo.
