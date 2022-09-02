
import logging
from getpass import getpass
import asyncio
import json
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
import time

# This code line allows to use asyncio in Windows.
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class SendMessage(slixmpp.ClientXMPP):
    def __init__(self, jid, password, to, message, origin, origin_hop, user_connection):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.to = to
        self.message = message
        self.origin = origin
        self.origin_hop = origin_hop
        self.user_connection = user_connection
        self.historial_origin = []
        self.update = True
        self.converged = False
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message_sender)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        # 'computation||'+origin+'||'+origin_hop
        #'computation||'+json.dumps(origin)+'||'+json.dumps(origin_hop)
        mensaje = 'computation||' + json.dumps(self.origin) + '||' + json.dumps(self.origin_hop)

        for contact in self.user_connection:
            self.send_message(mto=contact, mbody=mensaje, mtype='chat')
        
    
    def message_sender(self, msg):
        print("Escuchando mensajes")
        if msg['type'] in ('chat', 'normal'):
            # print("From: ", msg["from"])
            # print("Subject: ", msg["subject"])
            # print("Message: ", msg["body"])
            message = ((msg["body"]))

            message = message.split('||')
            action = message[0]

            if action == 'computation':
                org = message[1]
                org_hop = message[2]
                org = json.loads(org)
                org_hop = json.loads(org_hop)

                new_orig, new_orig_hop = self.distance_vector_update(self.jid, self.origin, self.origin_hop, org, org_hop)

                #self.historial_origin = (self.historial_origin.copy() + [list(new_origin.values())])[-5:] #esto va a ser una lista de los ultimos 5 vectores
                self.historial_origin = (self.historial_origin.copy() + [list(new_orig.values())])[-5:]

                if len(self.historial_origin) == 5 and self.check_lists(self.historial_origin):
                    self.update = False

                if self.update:
                    self.origin = new_orig
                    self.origin_hop = new_orig_hop
                    print("Nuevo vector de distancia: ", self.origin)
                    print("Nuevo vector de hops: ", self.origin_hop)

                    mensaje = 'computation||' + json.dumps(self.origin) + '||' + json.dumps(self.origin_hop)

                    for contact in self.user_connection:
                        self.send_message(mto=contact, mbody=mensaje, mtype='chat')
                elif(not self.converged):
                    time.sleep(5)
                    print("XD ya convergi xddd")
                    self.converged = True
                    #0 seria la accion
                    #1 seria a quien va dirigido
                    #2 seria de quien viene
                    #3 seria el mensaje
                    #4 seria el hop
                    new_mensaje = 'converged||' + self.to + '||'+ self.jid + '||' + self.message + '||'
                    #primero verificar si el self.to no es igual al self.jid 
                    if self.to != self.jid:
                        new_mensaje += self.jid
                        intermadiary_routers = self.origin_hop[self.to].split(',')
                        if(len(intermadiary_routers) > 1):
                            self.send_message(mto=intermadiary_routers[1], mbody=new_mensaje, mtype='chat')
                        else:
                            print("No hay intermediario")
                        
                    else:
                        print("El mensaje en el nodo:", self.jid, "es:", self.message)


    def check_lists(self, list_of_lists):
        for l in list_of_lists:
            if l != list_of_lists[0] or 1000 in l:
                return False
        return True

    def distance_vector_update(self, self_node, distance_vector, hops_vector, upcomming_distance_vector, upcomming_hops_vector):
        node_list = list(distance_vector.keys())
        result_distance = {}
        result_hops = {}
        for n in node_list:
            # el +1 es porque la distancia hacia mis vecinos se que es 1
            if (upcomming_distance_vector[n] + 1) < distance_vector[n]:
                result_distance[n] = upcomming_distance_vector[n] + 1
                result_hops[n] = self_node +","+upcomming_hops_vector[n]  #la , es para separar los hops que se deben tener
            else:
                #si no se cambia nada se quedan como estaban
                result_distance[n] = distance_vector[n]
                result_hops[n] = hops_vector[n]
        return result_distance, result_hops
    

class ActiveRouter(slixmpp.ClientXMPP):
    def __init__(self, jid, password, origin, origin_hop, user_connection):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.origin = origin
        self.origin_hop = origin_hop
        self.user_connection = user_connection
        self.historial_origin = []
        self.converged = False
        self.update = True
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

    def check_lists(self, list_of_lists):
        for l in list_of_lists:
            if l != list_of_lists[0] or 1000 in l:
                return False
        return True

    def message(self, msg):
        print("Escuchando mensajes")
        if msg['type'] in ('chat', 'normal'):
            # print("From: ", msg["from"])
            # print("Subject: ", msg["subject"])
            # print("Message: ", msg["body"])
            message = ((msg["body"]))

            message = message.split('||')
            action = message[0]

            if action == 'computation':
                org = message[1]
                org_hop = message[2]
                org = json.loads(org)
                org_hop = json.loads(org_hop)

                new_orig, new_orig_hop = self.distance_vector_update(self.jid, self.origin, self.origin_hop, org, org_hop)

                #self.historial_origin = (self.historial_origin.copy() + [list(new_origin.values())])[-5:] #esto va a ser una lista de los ultimos 5 vectores
                self.historial_origin = (self.historial_origin.copy() + [list(new_orig.values())])[-5:]

                if len(self.historial_origin) == 5 and self.check_lists(self.historial_origin):
                    self.update = False

                if self.update:
                    self.origin = new_orig
                    self.origin_hop = new_orig_hop
                    print("Nuevo vector de distancia: ", self.origin)
                    print("Nuevo vector de hops: ", self.origin_hop)

                    mensaje = 'computation||' + json.dumps(self.origin) + '||' + json.dumps(self.origin_hop)

                    for contact in self.user_connection:
                        self.send_message(mto=contact, mbody=mensaje, mtype='chat')
            elif action == 'converged':
                dest = message[1]
                orig = message[2]
                content = message[3]
                hop = message[4]
                
                if dest == self.jid:
                    print("\n\n\nMENSAJE ENTRANTE:")
                    print("De: ", orig)
                    print("Para: ", dest)
                    print("Mensaje: ", content)
                    print("Historial de saltos: ", hop)
                else:
                    intermadiary_routers = self.origin_hop[dest].split(',')
                    if(len(intermadiary_routers) > 1):
                        hop += ","+intermadiary_routers[0]
                        print(self.jid, "va a reenviar el mensaje a:", intermadiary_routers[1])
                        self.send_message(mto=intermadiary_routers[1], mbody='||'.join(['converged', dest, orig, content, hop]), mtype='chat')
                    else:
                        print("No hay intermediario en el nodo:", self.jid)
                #0 seria la accion
                #1 seria a quien va dirigido
                #2 seria de quien viene
                #3 seria el mensaje
                #4 seria el hop
                    






    # Esto cada vez que le caiga un mensaje
    # se me ocurria un split tipo 'computation||dv||hops
    # self_node quien soy yo (jid del cliente)
    # distance_vector seria como origin, mi distance vector
    # hops_vector seria como origin_hop, mi hops vector (donde tengo que saltar para llegar)
    # upcomming_distance_vector seria como origin pero del que me llega el mensaje
    # upcomming_hops_vector seria como origin_hop pero del que me llega el mensaje
    # al final deberiamos de actualizar origin y origin_hop con los nuevos valores que nos devuelve la funcion y mandarlo a los vecinos
    

    def distance_vector_update(self, self_node, distance_vector, hops_vector, upcomming_distance_vector, upcomming_hops_vector):
        node_list = list(distance_vector.keys())
        result_distance = {}
        result_hops = {}
        for n in node_list:
            # el +1 es porque la distancia hacia mis vecinos se que es 1
            if (upcomming_distance_vector[n] + 1) < distance_vector[n]:
                result_distance[n] = upcomming_distance_vector[n] + 1
                result_hops[n] = self_node +","+upcomming_hops_vector[n]  #la , es para separar los hops que se deben tener
            else:
                #si no se cambia nada se quedan como estaban
                result_distance[n] = distance_vector[n]
                result_hops[n] = hops_vector[n]
        return result_distance, result_hops

            


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


def distance_vector_initialization(input_usuario, user_connections, network_users):
    hops = {}
    distance_vector = {}
    for n in network_users:
        if n in user_connections:
            distance_vector[n] = 1
            hops[n] = input_usuario +","+n
        elif n == input_usuario:
            distance_vector[n] = 0
            hops[n] = input_usuario
        else:
            distance_vector[n] = 1000
            hops[n] = input_usuario
    return distance_vector, hops



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)-8s %(message)s')

    print('Bienvenido \n')

    jid = input('Ingrese su JID: ')
    password = getpass('Ingrese su contraseña: ')

    path = input('Ingrese el path del archivo de configuración: ')

    f = open(path, "r")
    data = json.load(f)

    input_usuario = jid
    user_connections = data['config'][input_usuario]
    network_users = list(data['config'].keys())

    origin, origin_hops = distance_vector_initialization(input_usuario, user_connections, network_users)

    menu()
    # de todos los clientes, si uno apacha enter, va a mandar origin y origin_hops a sus vecinos
    opcion = input('Seleccione una opcion: ')
    if opcion == '1':
        to = input('To: ')
        message = input('Message: ')
        router = SendMessage(jid, password, to, message,
                             origin, origin_hops, user_connections)
        router.register_plugin('xep_0030')
        router.register_plugin('xep_0004')
        router.register_plugin('xep_0060')
        router.register_plugin('xep_0199')
        router.connect(disable_starttls=True)
        router.process(forever=False)
        router.disconnect()
    elif opcion == '2':
        router = ActiveRouter(jid, password, origin, origin_hops, user_connections)
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
