# encoding: utf-8

from __future__ import print_function

import socket
import threading

import comandos
from usuarios import User

# Host e porta utilizados pelo servidor
HOST = '127.0.0.1'
PORT = 5003


def handle_connection(conn, addr):
    # Função principal para lidar com novas conexões que o servidor receberá.
    # Ela é a responsável por associar os sockets ao usuário correto.
    # Um timeout padrão de 600 segundos (10 minutos) será imposto a fim de
    # não sobrecarregar o servidor em caso de conexões inativas.
    conn.settimeout(600)

    # Após receber a conexão, o servidor deve aguardar por dados de login
    # ou de registro. Ou, no caso do socket recebedor (secundário) do
    # usuário, uma referência ao socket primário.
    conn.send(('[Servidor] Efetue login ou cadastre um novo usuário. '
              'Digite `ajuda` para listar os comandos disponíveis.'))

    try:
        while True:
            # Aguarda um comando. Este comando pode ser ajuda, faz_login
            # ou adiciona_usuario.
            command = conn.recv(1024)
            command_lower = command.lower()

            if command_lower == 'ajuda':
                conn.send('\n'.join(comandos.client_commands_anonymous))

            elif command_lower.startswith('faz_login'):
                # Usuário tenta fazer login aqui. Segundo a especificação,
                # ao separar a strings por vírgulas, temos
                # o comando, o nome do usuário e sua senha. Logo:
                try:
                    command, name, password = command.split(',')
                except Exception as e:  # Cliente enviou menos ou mais que 3 dados
                    print(repr(e))
                    conn.send('not_ok')
                    continue

                # E tentamos fazer o login do usuário com esses dados.
                try:
                    user = User.login(conn, name, password)
                    print('[Servidor] %s:%d :: Usuário logado:' % addr,
                          name)
                    conn.send('ok')
                    break  # Sai do loop infinito para continuar
                except Exception as e:  # O código do except será executado se não
                    # existe um usuário com esses dados
                    print(repr(e))
                    conn.send('not_ok')
                    print('[Servidor] %s:%d :: Falha no login:' % addr,
                          name)

            elif command_lower.startswith('adiciona_usuario'):
                # Cliente tenta criar um usuário. Especifica-se:
                # nome, telefone, endereço, e-mail e senha.
                try:
                    command, name, phone, address, email, password = \
                        command.split(',')
                except Exception as e:  # Cliente enviou menos ou mais que 6 dados
                    print(repr(e))
                    conn.send('not_ok')
                    continue

                # Pode ser que já exista um usuário com esse nome.
                # Se for o caso, não deve ser possível fazer o registro.

                try:
                    user = User.signup(conn, name, phone, address,
                                       email, password)# Tentar registrar
                    print('[Servidor] %s:%d :: Usuário registrado:' % addr,
                          name)
                    conn.send('ok')
                    break  # Sai do loop infinito para continuar
                except Exception as e:  # O código do except será executado se não
                    # existe um usuário com esses dados
                    print(repr(e))
                    conn.send('not_ok')
                    print('[Servidor] %s:%d :: Falha no registro:' % addr,
                          name)

            elif command.startswith('lista_leiloes'): #startwith se a string começa com essa texto --> não precisava
                auctions = comandos.lista_leiloes()
                conn.send(auctions)

            elif command.isdigit():
                # Se a string for um número, deve ser o segundo socket
                # enviando o número da porta do primeiro socket
                # para que seja possível ligá-lo ao usuário logado.
                port_number = int(command)

                try:
                    user = User.get_user_by_socket_port(port_number)

                    # Associa o socket da conexão atual ao usuário; este
                    # socket é o socket recebedor do usuário. Por este
                    # socket o servidor enviará as atualizações automáticas
                    # como, por exemplo, novos lances em leilões em que
                    # o usuário participa.
                    user.bind_receiver_socket(conn)
                    conn.send('ok')
                    return

                except Exception as e:  # Não há um usuário logado cuja porta do socket
                    # primário é essa
                    print(repr(e))
                    conn.send('not_ok')

            else:
                conn.send('not_ok')

    except socket.timeout: #caso o cliente não mande nada 
        conn.send('[Servidor] Tempo excedido.')
        conn.close()
        print('[Servidor] %s:%d :: Tempo excedido.' % addr)
        return

    handle_user(user)  # Passa a bola para a função abaixo


def handle_user(user): #usuario logado
    try:
        while True:
            data = user.recv() #def recv no usuários
            command = data.partition(',')[0] #Funciona parecido com slpit porém pega o primeiro comando antes da virgula [0]

            if command not in comandos.client_commands:
                user.answer('not_ok')
                continue

            try:
                output = comandos.client_functions[command](user, data) 
                user.answer('ok' if output is True else output) #se o output for explicitamento True responde com OK, snão responde com o próprio output
            except Exception as e:
                print(repr(e)) #representação da except debug
                user.answer('not_ok')

    except socket.timeout:
        user.answer('[Servidor] Tempo excedido.')
        user.sender.close()

        if user.receiver is not None:
            user.receiver.close()

        user.logout()


# A verificação abaixo serve para saber se o programa teve como ponto
# de entrada este arquivo. Se for, inicializamos e levantamos o
# servidor e começamos a ouvir as conexões.
if __name__ == '__main__':
    server = socket.socket()  # Inicializa um socket
    print('[Servidor] Inicializando servidor em %s:%d...' % (HOST, PORT))
    server.bind((HOST, PORT))  # Vincula o servidor ao endereço de IP 127.0.0.1 e porta:5003
    

    server.listen(0)  # Aqui habilitamos o servidor para começar a ouvir conexões que chegam
    
    try:
        print('[Servidor] Aguardando conexões...')
        while True:
            # Aqui deixamos um loop infinito onde o servidor aceita
            # conexões. Todo o resto será feito pelas threads criadas
            # após este ponto. O try/except serve para capturar 
           
            connection = server.accept()

            print('[Servidor] Nova conexão de %s:%d' % connection[1])

            # Inicia uma nova thread com os dados de conexão recebidos
            t = threading.Thread(target=handle_connection, args=connection)
            t.daemon = True
            t.start()

    except KeyboardInterrupt:
        print('\n[Servidor] Ctrl-C recebido. Finalizando...')
