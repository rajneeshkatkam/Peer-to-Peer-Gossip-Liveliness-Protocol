# CS765 Blockchain : Project Part - I

* Team Members:

|     Name             |
|:--------------------:|
|   Sagar Tyagi        |
|   Rajneesh Katkam    |
|   Vipin Mahawar      |



* Disclaimer
    1. Please use different ports for each seed and peer if running on a single system.
    2. If running on a single system make sure that no two peers or seed are running in same directory otherwise Output files will conflict

----------------------------------------------------------------------------------------------------------------------------------------------

* Steps to run the programs
1.  First run the seeds using following syntax
    python3 seed.py <port_number>
    (eg. python3 seed.py 9999)

2.  After running required no of seeds (>=1), Create a config.txt file which will have seeds information one at each line in following format
    IP1:PORT1
    IP2:PORT2
    eg.
        192.168.0.100:9999
        192.168.0.101:9999

3.  Now run the required number of peers using following command
    python3 peer.py <port_number>
    (eg. python3 peer.py 9998)

----------------------------------------------------------------------------------------------------------------------------------------------

# Files Information:

* Input Files
    config.txt          -- this file contains the information of seeds seperated by lines (IP:PORT)

* Output Files Created.
    * Every Seed will create the following files in current working directory
        1. outputfile.txt       --contain the information about the peers the seed is connected to.

    * Every Peer will create the following files in current working directory
        1. dead_node_list.txt   --contain the information of dead nodes the peer have.
        2. gossip_message.txt   --contains the gossip message generated by the peer or reveived by the peer first time.
        3. seed_peer_list.txt   --contains the seed reply (peer list of seed) while connecting to the seed.
    
----------------------------------------------------------------------------------------------------------------------------------------------

# Additional Features

* Interactive Shell:
Both Seed and Peer have a interactive shell which will be invocked automatically when executed.
Below are commands supported by these shells:
    1. "list" :: to get the connected peers list
    2. "exit" :: to exit the Peer
    3. "msgs" :: to get the message hash list 
