
import logging
from getpass import getpass
import asyncio
import json
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout

# This code line allows to use asyncio in Windows.
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class SendMessage(slixmpp.ClientXMPP):
    def __init__(self, jid, password, to, message, tabla_ruteo, nodes, ref):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.to = to
        self.message = message
        self.tabla_ruteo = tabla_ruteo
        self.nodes = nodes
        self.ref = ref
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        # orig+'|'+neigh[i]+'|'+to+'|'+msg
        mensaje_completo = self.message + '|' + self.to + '|' + self.jid

        nodoD = self.ref[self.to]
        neightbor = self.tabla_ruteo[nodoD][1]
        dest = ''
        for key, value in self.ref.items():
            if value == neightbor:
                dest = key
                break

        print("Siguiendo ruta: ", self.tabla_ruteo[nodoD])
        print("Mensaje enviado al router: " + dest)

        self.send_message(mto=dest, mbody=mensaje_completo, mtype='chat')


class ActiveRouter(slixmpp.ClientXMPP):
    def __init__(self, jid, password, tabla_ruteo, nodes, ref):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.nodes = nodes
        self.tabla_ruteo = tabla_ruteo
        self.ref = ref
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

    def message(self, msg):
        print("Escuchando mensajes")
        if msg['type'] in ('chat', 'normal'):
            print("From: ", msg["from"])
            print("Subject: ", msg["subject"])
            print("Message: ", msg["body"])
            message = ((msg["body"]))

            message = message.split('|')
            msg = message[0]
            to = message[1]
            orig = message[2]

            if to == self.jid:
                print("El mensaje es para mi")
                print("Mensaje: ", msg)
                print("Router por los que paso el mensaje: ", orig)
            else:
                nodoD = self.ref[to]
                neightbor = self.tabla_ruteo[nodoD][1]
                dest = ''
                for key, value in self.ref.items():
                    if value == neightbor:
                        dest = key
                        break

                print("Siguiendo ruta: ", self.tabla_ruteo[nodoD])
                print("Mensaje enviado al router: " + dest)

                new_message = '|'.join(message)
                new_message = new_message + ',' + self.jid

                self.send_message(mto=dest, mbody=new_message, mtype='chat')


def dijkstra(matriz, start, end=-1):
    n = len(matriz)

    dist = [float('inf')]*n
    dist[start] = matriz[start][start]  # 0

    spVertex = [False]*n
    parent = [-1]*n

    path = [{}]*n

    for count in range(n-1):
        minix = float('inf')
        u = 0

        for v in range(len(spVertex)):
            if spVertex[v] == False and dist[v] <= minix:
                minix = dist[v]
                u = v

        spVertex[u] = True
        for v in range(n):
            if not(spVertex[v]) and matriz[u][v] != 0 and dist[u] + matriz[u][v] < dist[v]:
                parent[v] = u
                dist[v] = dist[u] + matriz[u][v]

    for i in range(n):
        j = i
        s = []
        while parent[j] != -1:
            s.append(j)
            j = parent[j]
        s.append(start)
        path[i] = s[::-1]

    return (dist[end], path[end]) if end >= 0 else (dist, path)


def menu():
    print("""
    1. Send message
    2. Activate router
    3. Exit
    """)


def routing_table(path):
    print("Updating Routing Table...")
    f = open(path, "r")
    data = json.load(f)
    topologia = data["config"]
    f.close()
    # ref = {}
    clave = {}
    cant_nodos = len(topologia)
    edge = [[0 for column in range(cant_nodos)] for row in range(cant_nodos)]
    keys_list = list(topologia.keys())
    for i in range(cant_nodos):
        ref[keys_list[i]] = i

    for key, value in topologia.items():
        for i in value:
            x = ref[key]
            y = ref[i]
            edge[x][y] = 1

    print(ref)
    print(edge)
    return edge


ref = {}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    print('Bienvenido \n')

    jid = input('Ingrese su JID: ')
    password = getpass('Ingrese su contraseña: ')

    path = input('Ingrese el path del archivo de topologia: ')
    edge = routing_table(path)
    key_list = list(ref.keys())
    if jid not in key_list:
        print("El usuario con el que se ha iniciado sesion no forma parte de la topologia")

    res = dijkstra(edge, ref[jid])
    tabla_ruteo = res[1]

    print("La tabla de ruteo es: ")
    for i in range(len(tabla_ruteo)):
        print("La ruta mas corta al nodo %s es a traves de:" % (key_list[i]))
        for x in tabla_ruteo[i]:
            print(key_list[x])

    menu()
    opcion = input('Seleccione una opcion: ')
    if opcion == '1':
        to = input('To: ')
        message = input('Message: ')
        router = SendMessage(jid, password, to, message,
                             tabla_ruteo, key_list, ref)
        router.register_plugin('xep_0030')
        router.register_plugin('xep_0004')
        router.register_plugin('xep_0060')
        router.register_plugin('xep_0199')
        router.connect(disable_starttls=True)
        router.process(timeout=10)
        router.disconnect()
    elif opcion == '2':
        router = ActiveRouter(jid, password, tabla_ruteo, key_list, ref)
        router.register_plugin('xep_0030')
        router.register_plugin('xep_0004')
        router.register_plugin('xep_0060')
        router.register_plugin('xep_0199')
        router.connect(disable_starttls=True)
        router.process(forever=False)
        router.disconnect()
    elif opcion == '3':
        print('Saliendo...')
    else:
        print('Opcion no valida, cerrando programa')
        exit()
