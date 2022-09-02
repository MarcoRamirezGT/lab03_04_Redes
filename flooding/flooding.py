# Required Libraries
from http import server
from operator import ne
import socket
import pickle
import sys
from sleekxmpp.exceptions import IqError, IqTimeout
from getpass import getpass
from argparse import ArgumentParser
import logging
import asyncio
import matplotlib.pyplot as plt
import matplotlib
import random
import json
import networkx as nx
import asyncio
import logging
from os.path import exists
import os.path
from pathlib import Path
import slixmpp

# Global Variables for the EchoBot class (Error Handling Python version)
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PATH_TO_TOPOLOGY = 'top3.txt'
class Server(slixmpp.ClientXMPP):
    # Class Constructor
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        # Add the event handler for handling messages
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("inicio", self.start)
        # For the users messages
        self.add_event_handler("message", self.message)

    # Function for handling the session_start event

    async def start(self, event):

        self.send_presence()
        await self.get_roster()
    # Function for handling the message event

    def message(self, msg):
        # If the message is of type 'chat'

        if msg['type'] in ('chat', 'normal'):
            print("From: ", msg["from"])
            print("Subject: ", msg["subject"])
            print("Message: ", msg["body"])
            message = ((msg["body"]))

            message = message.split('|')

            f = open(PATH_TO_TOPOLOGY, "r")
            data = json.load(f)

            G = nx.Graph()

            for key, value in data["config"].items():
                for i in value:

                    G.add_edge(key, i)
            # Cambiar nombres de los nodos

            # names = open("names.txt", 'r')
            # new_names = json.load(names)

            # G = nx.relabel_nodes(G, new_names['nodes'], copy=False)
            origen = message[0]
            vecino = message[1]
            dest = message[2]
            mensaje = message[3]
            td = 'dataset_%s.txt' % self.jid
            dataset = open(td, 'w+')

            if dest == self.jid:
                print('El mensaje es para mi')
                # msg.reply("El mensaje es para mi\n%(body)s" % msg).send()
            else:
                dest = message[2]
                neigh = list(G.neighbors(vecino))
                neigh.remove(origen)

                for i in range(len(neigh)):
                    res = vecino+'|'+neigh[i]+'|'+dest+'|'+mensaje
                    if neigh[i] in dataset.read():
                        print('El mensaje ya existe')
                    else:

                        self.send_message(
                            mto=neigh[i], mbody=res, mtype='chat')

                        dataset.write(str(neigh[i]))
                        dataset.write('\n')
                        dataset.close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')
    user = input('User:\n')
    password = input('Password:\n')

    xmpp = Server(user, password)
    # td = 'dataset_%s.txt' % user
    # try:
    #     open(td, "r")
    #     print('archivo existe')

    # except IOError:
    #     print("Error: File does not appear to exist.")

    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0004')  # Data Forms
    xmpp.register_plugin('xep_0060')  # PubSub
    xmpp.register_plugin('xep_0199')  # XMPP Ping
    xmpp.register_plugin('xep_0100')  # XMPP Add contact
    xmpp.register_plugin('xep_0030')  # XMPP Delete account
    op = input('Que desea hacer\n1. Enviar mensaje\n2.Recibir mensaje\n3.Salir\n')

    if op == '1':

        xmpp.connect(disable_starttls=True)

        xmpp.process(timeout=20)

        f = open(PATH_TO_TOPOLOGY, "r")
        data = json.load(f)

        G = nx.Graph()

        for key, value in data["config"].items():
            for i in value:

                G.add_edge(key, i)

        # Cambiar nombre de los nodos
        # names = open("names.txt", 'r')
        # new_names = json.load(names)

        # G = nx.relabel_nodes(G, new_names['nodes'], copy=False)

        orig = user

        to = input('Destino del mensaje\n')
        msg = input('Introduzca su mensaje:\n')
        neigh = list(G.neighbors(orig))

        for i in range(len(neigh)):
            res = orig+'|'+neigh[i]+'|'+to+'|'+msg
            xmpp.send_message(mto=neigh[i], mbody=res, mtype='chat')
        xmpp.process()
    if op == '2':

        xmpp.connect(disable_starttls=True)

        xmpp.process()
    else:
        exit()