# encoding: utf-8

from __future__ import print_function

import os
import json
import threading
from datetime import datetime


FILENAME = os.path.splitext(__file__)[0] + '.json'
FILELOCK = threading.RLock()


class Bid(object): #orientação ao objeto, justama para manipular mais facilmente os dados
    @classmethod
    def new(cls, user_id, auction_id, value): #cls - classe (Bid)
        # Cria um novo objeto Bid com os dados informados e salva no
        # arquivo json.
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f) #carrega nosso arquivo

            try:
                id = bids[-1]['id'] + 1
            except IndexError:
                id = 1

            b = cls(id, user_id, auction_id, value,
                    datetime.now().timetuple()[:6]) #timetuple retorma a lista contendo hora,minuto,segundo...

            b.save()

        return b

    @classmethod
    def load(cls, id):
        # Carrega o objeto Bid cujo id é o id informado.
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

        for b in bids:
            if b['id'] == id:
                return cls(b['id'], b['user_id'], b['auction_id'],
                           b['value'], b['bid_date'])

        raise Exception('Lance não encontrado.')

    @classmethod
    def filter_by_user(cls, id): #carregar todos os lances do usuário -- para deletar o usuário--
        # Carrega todos os objetos Bid cujos user_id correspondem ao
        # id informado.
        bid_list = []
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

            for b in bids:
                if b['user_id'] == id:
                    bid_list.append(cls(b['id'], b['user_id'], b['auction_id'],
                                        b['value'], b['bid_date']))

        return bid_list

    @classmethod
    def filter_by_auction(cls, id): #listar os lances de um leilão
        # Carrega todos os Bids cujos auction_id correspondem ao id
        # informado.
        bid_list = []
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

            for b in bids:
                if b['auction_id'] == id:
                    bid_list.append(cls(b['id'], b['user_id'], b['auction_id'],
                                        b['value'], b['bid_date']))

        return bid_list

    @classmethod
    def all(cls): #carrega todos os lances, para 
        # Carrega e retorna todos os objetos Bid.
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

        return [cls(b['id'], b['user_id'], b['auction_id'],
                    b['value'], b['bid_date']) for b in bids]

    def __init__(self, id, user_id, auction_id, value, bid_date):
        self.id = id
        self.user_id = user_id
        self.auction_id = auction_id
        self.value = value
        self.bid_date = bid_date

    def save(self):
        # Salva este objeto Bid no arquivo json. Assim como os métodos
        # de load (filter*, load, all), este método utiliza o lock de
        # arquivo (semáforo) para ler de e escrever para o arquivo,
        # evitando "confusões" de escrita e leitura.
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

            for b in bids:
                if b['id'] == self.id:
                    break
            else:
                b = {'id': self.id}
                bids.append(b)

            b['user_id'] = self.user_id
            b['auction_id'] = self.auction_id
            b['value'] = self.value
            b['bid_date'] = self.bid_date

            with open(FILENAME, 'w') as f:
                json.dump(bids, f)

    def delete(self):
        # Deleta este objeto Bid do arquivo json.
        with FILELOCK:
            with open(FILENAME) as f:
                bids = json.load(f)

            for b in bids:
                if b['id'] == self.id:
                    break

            bids.remove(b)

            with open(FILENAME, 'w') as f:
                json.dump(bids, f)


# Abaixo é feito o preparo do arquivo de lances.
# Verifica-se se o arquivo existe;
#   Se não existe, cria.
# Não é necessário o uso da Lock aqui porque é executado
# antes de qualquer leitura anterior.

if not os.path.exists(FILENAME):
    with open(FILENAME, 'w') as f:
        print('[]', file=f)
        # Escreve no arquivo uma "lista" json vazia.
        # Desta forma, deixamos o servidor preparado para ler e até mesmo
        # escrever json no arquivo.
