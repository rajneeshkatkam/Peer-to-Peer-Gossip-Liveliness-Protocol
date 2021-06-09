import socket
import sys
import threading
import time
import random
from queue import Queue
import calendar
from hashlib import sha256

    
class Peer:
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.dead_counter=0

def clear_out_files():
    files = ["dead_node_list.txt", "gossip_message.txt", "seed_peer_list.txt"]
    for out_file in files:
        with open(out_file, "w") as file:
            pass


# Socket Functionalities Below --------------------------
if len(sys.argv) >1:
    port = int(sys.argv[1])
else:
    print("Please provide port number as argument for peer")
    sys.exit()

# creating object of socket
def create_socket():
    try:
        global server_socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(5)
    except socket.error as msg:
        print("Socket creation error: "+str(msg))


# binding the socket
def bind_socket():
    try:
        print("Binding the port: "+str(port))
        server_socket.bind(('', port))
        server_socket.listen(5)

    except socket.error as msg:
        print("Error binding with port:"+str(port)+" Please exit and try other port")
        time.sleep(5)
        bind_socket()




# Handling connections from multiple clients and saving to a list
# Closing previous connections if any
def accepting_connections():
    '''
    This is a function for a Thread which will run for the entire life or program and accept connections on the provided port.
    Then it'll also process according to the received response.
    '''
    global thread_run
    global myip
    thread_run=True

    while thread_run:
        try:
            conn, address = server_socket.accept()
            client_response = str(conn.recv(1024).decode("utf-8"))

            if("New Connection Request Peer" in client_response ): # New Connection Request
                if(len(final_peer_object_list) < 4):
                    connected_peer_port = client_response[client_response.find(":")+2:]
                    peer_object = Peer(address[0], int(connected_peer_port))
                    final_peer_object_list.append(peer_object)
                    conn.send(bytes("New Connection Accepted","utf-8"))
                else:
                    conn.send(bytes("New Connection Failed","utf-8"))


            elif("Gossip Message" in client_response): # Gossip Message
                conn.send(bytes("Gossip Message Received","utf-8"))
                #Thread created for gossip_forward_protocol function
                t4=threading.Thread(target=gossip_forward_protocol, args=(client_response,))
                t4.daemon = True
                t4.start()


            elif("Liveness Request" in client_response ): # Liveness Message
                _, sender_ts, sender_ip = client_response.split(':')
                msg="Liveness Reply: "+str(sender_ts)+":"+str(sender_ip)+":"+str(myip)
                conn.send(bytes(msg,"utf-8"))

            conn.close()

        except socket.error as msg :
            if "timed out" not in str(msg):
                print("accepting_connections() Error: "+ str(msg))
            continue

# Socket Functionalities End --------------------------


# Final Peer List Formation Functions -----------------------

# Global variables for peer functionality
message_list = []
final_peer_object_list=[]
union_peer_object_list=[]
final_seed_list=[]


def connecting_to_seeds_and_union_list():
    '''
    This function will first read the config.txt file and select floor(n/2) + 1 seeds.
    Then try to connect with them and make a union of provided peers list from those seeds.
    It'll also print terminal if a seed in config is down.
    '''
    global union_peer_object_list
    global final_peer_object_list
    global final_seed_list
    global myip
    myip= ''

    config_file = open("config.txt", "r")
    all_seeds = config_file.readlines()
    k = int(len(all_seeds)/2) + 1
    final_seed_list = random.sample(all_seeds, k)
    final_seed_list = [ seed.strip("\n") for seed in final_seed_list ]
    union_set_peers = set()
    print("Selected Seed List:", final_seed_list)
    for seed in final_seed_list:
        try:
            seed = str(seed).strip()   #to remove the "\n" character
            seed_address = seed.split(':')
            client_socket=socket.socket()
            client_socket.connect((seed_address[0],int(seed_address[1],10))) # at index 0 - host, at index 1 - port.
            client_socket.send(bytes("New Connection Request Seed: "+ sys.argv[1],"utf-8"))  #give info to seed about the new connection of peer.
            client_socket_response = str(client_socket.recv(1024).decode("utf-8"))
            with open("seed_peer_list.txt", "a") as file:
                file.write("Seed: " + str(seed) + " => Peer List:" + str(client_socket_response) + "\n\n")
            splited_response = client_socket_response.split('#')
            if "Success" in splited_response[0]:
                myip=splited_response[1]
                client_socket_response=splited_response[2]
                peers_list_of_seed = client_socket_response.strip('][').split(', ')  #considering seed will send the format as  'IP:PORT'
                if len(peers_list_of_seed)>0:
                    for peer in peers_list_of_seed:
                        if len(str(peer))>0:
                            union_set_peers.add(peer)
            client_socket.close()
        except socket.error as msg:
            print("Seed =>"+str(seed)+" doesn't exist")

    if len(union_set_peers) > 0:
        union_peer_object_list = create_union_peer_object_list(union_set_peers)         
    if len(union_peer_object_list) > 0:
        final_peer_object_list = creating_final_peer_object_list(union_peer_object_list)
    
    #print("Length of final_peer_object_list is: "+str(len(final_peer_object_list)))
            

#creating peer objects for union_peer_list            
def create_union_peer_object_list(union_set_peers):
    '''
    This Function will just return Peer Objects (Class) from provided list of peers in IP:PORT format
    '''
    temp_union_peer_object_list = []
    for peer in union_set_peers:
        peer=str(peer).strip("'")
        address = peer.split(':')
        peer_object = Peer(address[0],int(address[1]))
        temp_union_peer_object_list.append(peer_object)

    return temp_union_peer_object_list

#creating final_peer_object_list
def creating_final_peer_object_list(union_peer_object_list):
    '''
    This function will try to establish connection with a selected peers from the union peer object list.
    If a peer deny to connect (Already connected with 4 peers) then it'll simply skip that peer and try with the next peer.
    And return the final coonected peers object list of atmost 4.
    '''
    temp_final_peer_object_list = []
    random_max_number = random.randint(1,4)   # generate random number between 1 and 4
    for peer_object in union_peer_object_list:
        try:
            client_socket=socket.socket()
            client_socket.connect((peer_object.ip,peer_object.port))
            client_socket.send(bytes("New Connection Request Peer: "+sys.argv[1],"utf-8"))
            client_socket_response = str(client_socket.recv(1024).decode("utf-8"))
            if(client_socket_response == "New Connection Failed"):
                print("Failed with Seed Response: "+str(client_socket_response))
                client_socket.close()
                continue
            elif(client_socket_response == "New Connection Accepted"):
                temp_final_peer_object_list.append(peer_object)
            
            if(len(temp_final_peer_object_list) == random_max_number):
                client_socket.close()
                break
            client_socket.close()
        except socket.error as msg:
            print("Failed connecting with Peer =>"+str(peer_object.ip)+":"+str(peer_object.port))
            delete_node_request_to_seeds(peer_object)

    return temp_final_peer_object_list    

    
# Final Peer List Formation Functions End-----------------------




# Gossip Functions -----------------------

def get_hash(msg):
    '''
    This function will take a string msg as parameter and return it's hexdigested SHA256 hash
    '''
    return sha256(msg.encode()).hexdigest()


def gossip_forward_protocol(client_response):
    '''
    This function will take the Gossip Message Received as input.
    And check if it's already sent then simply discard it or else put it in the message list and forward it to all connected peers
    '''
    _, msg = client_response.split(':', 1)
    hash_msg = get_hash(msg)
    if hash_msg not in message_list:
        message_list.append(hash_msg)
        with open('gossip_message.txt', 'a') as file:
            file.write("Forwarded Msg:"+client_response+'\n')
        for peer in final_peer_object_list:
            try:
                client_socket=socket.socket()
                client_socket.connect((peer.ip,peer.port))
                client_socket.send(bytes(client_response, "utf-8"))
                client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
                print("Forwarded Msg:", client_response)
                client_socket.close()
            except socket.error as msg:
                print("gossip_forward_protocol(): "+ str(client_response))
                gossip_forward_protocol(client_response)


# This will be running in gossip generating thread
def gossip_generate_protocol():
    '''
    This is a function run by an independent thread to generate and send gossip messages.
    '''
    global thread_run
    thread_run=True
    for i in range(10):
        if thread_run:
            ts = calendar.timegm(time.gmtime())
            msg=str(ts)+':'+str(myip)+ ':'+str(port) +'#Msg'+str(i+1)+'#'
            final_msg = "Gossip Message:" + msg
            with open('gossip_message.txt', 'a') as file:
                file.write("Generated Msg: " + final_msg+'\n')
            message_list.append(get_hash(msg))
            print("Generated Msg:", final_msg)
            # Sending new message to all the final_peer_object_list
            for peer in final_peer_object_list:
                try:
                    client_socket=socket.socket()
                    client_socket.connect((peer.ip,peer.port))
                    client_socket.send(bytes(final_msg, "utf-8"))
                    client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
                    client_socket.close()
                except socket.error as msg:
                    print("gossip_forward_protocol(): "+ str(msg))
            time.sleep(5)   # sleeps for 5 seconds and then again starts new gossip again

# Gossip Functions End------------------------------





# Liveness Functions ---------------------------------

def liveliness_protocol():
    '''
    This function will be run by an independent thread which will send and process liveness requests.
    '''
    global thread_run
    thread_run=True
    global myip
    while thread_run:
        for peer in final_peer_object_list:
            try:
                client_socket=socket.socket()
                ts = calendar.timegm(time.gmtime())
                client_socket.connect((peer.ip,peer.port))
                msg="Liveness Request: "+ str(ts) +":"+str(myip)
                print(msg+":"+str(peer.port))
                client_socket.send(bytes(msg, "utf-8"))
                client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
                print(client_socket_response)
                if("Liveness Reply:" in client_socket_response):
                    client_socket.close()
                    peer.dead_counter = 0
                    continue
                else:
                    peer.dead_counter+=1
                    if(peer.dead_counter>=3):
                        delete_node_request_to_seeds(peer)   # Removing from Seed's Peer List
                        final_peer_object_list.remove(peer) # Removing from final_peer_object_list 
                client_socket.close()

            except socket.error as msg:
                peer.dead_counter+=1 # Dead count increases if the adjacent peer didn't respond.
                print("Peer =>"+ str(peer.ip)+":"+str(peer.port)+ " didn't respond. Dead Counter value of the peer is: " +str(peer.dead_counter))
                if(peer.dead_counter>=3):
                    delete_node_request_to_seeds(peer)   # Removing from Seed's Peer List
                    final_peer_object_list.remove(peer) # Removing from final_peer_object_list 

        time.sleep(13)  # sleeps for 13 seconds and then again starts liveness again




def delete_node_request_to_seeds(peer):
    '''
    Argument: peer

    This function will broadcast this peer as dead to all the connected seeds
    '''
    global myip
    count = 0
    print("delete_node_request_to_seeds() start")
    print(final_seed_list)
    for seed in final_seed_list:
        try:
            client_socket=socket.socket()
            seed = str(seed).strip()   #to remove the "\n" character
            seed_address = seed.split(':')
            ts = calendar.timegm(time.gmtime())
            client_socket.connect((seed_address[0],int(seed_address[1],10))) # at index 0 - host, at index 1 - port.
            msg="Dead Node:"+str(peer.ip)+":"+str(peer.port)+":"+str(ts)+":"+str(myip)
            client_socket.send(bytes(msg,"utf-8"))  #give info to seed about deletion of dead peer.
            if count == 0:
                with open("dead_node_list.txt", "a") as file:
                    file.write(msg + "\n")
                count = 1
            client_socket_response=str(client_socket.recv(1024).decode("utf-8"))
            print(client_socket_response + " Seed =>" + str(seed))
            client_socket.close()
        except socket.error as msg:
            print("delete_node_request_to_seeds() Error: "+str(msg))

                
        

# Liveness Functions Ends---------------------------------



def listening_connections():
    create_socket()
    bind_socket()
    accepting_connections()


# Custom Shell with some functionalities
# Type "list" in the terminal to get the connected peers list
# Type "exit" in the terminal to exit the Peer
# Type "msgs" in the terminal to get the message hash list 
def start_shell():
    global thread_run
    thread_run=True

    while thread_run:
        cmd=input("shell> ")
        if cmd == 'list':
            list_connections()
        
        elif( 'msgs' in cmd ):
            print(message_list)

        elif 'exit' in cmd:
            thread_run=False
            print("Exiting Peer...")
            break
        else:
            print("Command not recognised")

def list_connections():
    '''
    This function will print all the connected peers on terminal.
    '''
    print("------- My Connected Peer List ------")
    for i, peer in enumerate(final_peer_object_list):
        print("  "+str(i+1) + ". "+ str(peer.ip)+":"+str(peer.port))



# Cleaning / Ceating all the output files
clear_out_files()

#This is the first task to be executed. After this final_peer_object_list is loaded with peer objects that are connected to this peer.
connecting_to_seeds_and_union_list()


if myip != '':

    #Custom shell Thread
    t1= threading.Thread(target=start_shell)
    t1.daemon=True
    t1.start()


    #Peer Listening Thread
    t2=threading.Thread(target=listening_connections)
    t2.daemon=True
    t2.start()

    #Liveness Thread
    t3=threading.Thread(target=liveliness_protocol)
    t3.daemon=True
    t3.start()

    #Gossip Thread
    t4=threading.Thread(target=gossip_generate_protocol)
    t4.daemon=True
    t4.start()


    t4.join()
    t3.join()
    t1.join()
    t2.join()

else:
    print("No seed available to connect\nExiting...")