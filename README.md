# Python Xmpp Routing Algotithm simulator
#### Author: [@campeon19](https://github.com/campeon19), [@JJHH06](https://github.com/JJHH06),[@MarcoRamirezGT](https://github.com/MarcoRamirezGT)

This is an XMPP protocol chat client that simulates the flooding, Dijkstra Link State and Distance Vector algorithms used in the Network layer of the OSI model. Made for the Networks class at the Universidad Del Valle de Guatemala.

# Usage
This is a project built with Python 3.9.10. And uses the slixmpp, sleekxmpp so if you don't have these installed you need to install them through pip as following:
```
pip install <library name>
```
# Requirements
You need to have a topology file in the same directory as the program. The topology file should be in the following format:
```
{"type":"topo", "config":{<jid of each node>: [<neighbors of the node>] ...}}
```

## Run each program
First you need to login with an account that exists inside the topology file. Then you need to write the topology file when asked.  

Note: _You need to have running all the clients that are needed in the topology._

After the authentication is done, you need to decide if your program will receive and forward messages to its final destination (option 2 of the menu) or if it will be in charged of sending the messages(option 1 of the menu).  

**Important:  You need to run first all the programs in charged of receiving and forwarding of messages before sending a message with a client**

To send a message you need to write the JID of the destination and the message you want to send. ** but you cannot include '||' characters inside the message or it will create unexpected behaviour**  

Every time you want to send another message it is best if you close each terminal and start over.**For the flooding algorithm** : it will generate dataset file in the path that you need to delete before running it again.
