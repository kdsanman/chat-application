#Kimberly D. Santiago
#kds2152
#UdpChat.py

import socket, sys, os, signal, time
from select import select

class AlarmException(Exception):
    pass

def alarmHandler(signum, frame):
    raise AlarmException

#get command line arguments
args = sys.argv

#check server CLI
if len(args) < 2:
    print 'Usage: ', args[0], ' [-c|-s] for more information'
    sys.exit()
elif args[1] == '-s':
    if len(args) is not 3:
        print 'Usage: ', args[0], ' -s <listening port>'
        sys.exit()
    mode = 'server'
    try:
        serverPort = int(args[2])
    except ValueError:
        print 'Server Port is invalid. Please enter a numeric value.'
        sys.exit()
    if serverPort > 65535 or serverPort < 1025:
        print 'Server Port is invalid. Please enter a port number between 1025 and 65535 inclusive'
        sys.exit()
    serverName = '127.0.0.1'

elif args[1] == '-c':
    if len(args) is not 6:
        print 'Usage: ', args[0], ' -c <nick-name> <server IP> <server port> <client port>'
        sys.exit()
    mode = 'client'
    username = args[2]
    serverName = args[3]

    try:
        serverPort = int(args[4])
    except ValueError:
        print 'Server Port is invalid. Please enter a numeric value.'
        sys.exit()

    try:
        clientPort = int(args[5])
    except ValueError:
        print 'Client Port is invalid. Please enter a numeric value.'
        sys.exit()

    if clientPort > 65535 or clientPort < 1025:
        print 'Client Port is invalid. Please enter port number between 1025 and 65535 inclusive.'
        sys.exit()

else:
    print 'Usage: ', args[0], ' [-c|-s] for more information'
    sys.exit()
#execute depending on mode
if mode == 'server':
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Create server socket
    try:
        serverSocket.bind((serverName, serverPort))
    except socket.error as msg:
        print 'Socket bind failed.'
        sys.exit()
    print 'Server', serverName,'is online on port', serverPort
    registrar = {}
    activeClients = 0
    saved_msgs = {}
    mail = []
    new_msg = []

    try: 
        while True:
            try:
                originalMessage, clientAddress = serverSocket.recvfrom(2048) #receive msg from client
                print 'Received message', originalMessage
                message = originalMessage.strip().split()

            except socket.timeout:
                continue
            
            #### iDENTIFY SENDER ####
            clientIP = clientAddress[0]
            clientSocket = clientAddress[1]
            command = ''
            if len(message) > 1:
                command = message[0]
                username = message[1]

            if command == 'dereg':
                userInfo = [clientIP, clientSocket, 'no']
                registrar[username] = userInfo
                serverSocket.sendto('>>> [You are Offline. Bye.]\n>>>', clientAddress)
                #activeClients -= 1
                print 'Sent', username, 'BYE\n'
                print username, ' has disconnected'

            elif command == 'reg':
                '''Check current status. Is someone already logged in?'''
                if username in registrar:
                    usInf = registrar[username]
                    status = usInf[2]
                    if 'yes' in status:
                        serverSocket.sendto('>>> [Welcome, You have not been registered. Username is already connected.]\n>>>', clientAddress)
                        continue
                
                userInfo = [clientIP, clientSocket, 'yes']
                
                if username not in registrar:
                    registrar[username] = userInfo
                    activeClients += 1
                    print username, ' has registered'
                    serverSocket.sendto('>>> [Welcome, You are registered.]\n>>>', clientAddress)
                    
                else: #Set client to online
                    registrar[username] = userInfo
                                        
                    print username, ' has connected'
                    serverSocket.sendto('>>> [Welcome back]\n>>>', clientAddress)
                    #### CHECK FOR SAVED MESSAGES ####
                    if username in saved_msgs:
                        serverSocket.sendto('[You have messages.]\n', clientAddress)
                        '''Wait for ACK'''
                        serverSocket.settimeout(4)
                        try:
                            ackk, clientAddress = serverSocket.recvfrom(2048)
                        except socket.timeout:
                            continue
                        '''Sends # of messages to client '''
                        saved_messages = saved_msgs[username]
                        numberOfMessages = len(saved_messages)
                        serverSocket.sendto(str(numberOfMessages), clientAddress)

                        ####Retrieves messages####
                        saved_messages = saved_msgs[username]
                        print 'Saved_messages variables is:', saved_messages
                        for mess in saved_messages:
                            mSender = mess[0]
                            mTime   = mess[1]
                            mMess   = mess[2]
                            serverSocket.sendto('{}: {} {}'.format(mSender, mTime, mMess), clientAddress)

                        del saved_msgs[username]
            
            #print 'Active clients are', activeClients
            
            elif command == 'send':
                #serverSocket.sendto('ack', clientAddress) #Send ack to sender
                recp = username
                recpInfo = registrar[recp]
                recpIP = recpInfo[0]
                recpPort = recpInfo[1]
                recp_online = (recpInfo[2] == 'yes')

                #### PING INTENDED RECP ####
                if recp_online:
                    serverSocket.sendto('ping', (recpIP, recpPort))
                try:
                    serverSocket.settimeout(.5)
                    recpClientMessage, recpClientAddress = serverSocket.recvfrom(2048)
                    if 'ack' in recpClientMessage:
                        recp_online = True

                except socket.timeout:
                    recp_online = False

                if recp_online:
                    serverSocket.sendto('>>> [Client',recp,'exists.]\n>>> ', clientAddress)
                    continue

                else: #recp is actually offline
                    #Determine sender of offine message
                    for client in registrar.keys():
                        clientInfo = registrar[client]
                        if clientInfo[1] == clientSocket:
                            sender = client

                    registrar[recp] = [recpIP, recpPort, 'no']
                    timestamp = time.asctime(time.localtime(time.time()))
                    size = len(command) + len(recp) + 1
                    msg = originalMessage[size:]
                    new_msg = [sender, timestamp, msg]

                    if recp in saved_msgs:
                        old_mail = saved_msgs[recp] #list
                        mail = old_mail
                        mail.append(new_msg)
                        
                    else:
                        mail = []
                        mail.append(new_msg)

                    saved_msgs[recp] = mail
                    #print 'Saved message:', originalMessage, 'sent by', username
                    #print 'Saved messages dict:', saved_msgs
                    
                    serverSocket.sendto('[Messages received by the server and saved.]\n>>> ', clientAddress)
                    #print 'Told client', clientAddress, 'that I saved the messages'
            
            print saved_msgs

            for client in registrar.keys():
               clientInfo = registrar[client]
               if clientInfo[2] == 'yes':
                   serverSocket.sendto(str(int(activeClients-1)), (clientInfo[0], clientInfo[1]))
                   print 'Sent', client, 'that I will be sending', str(int(activeClients-1)), 'clients'

            print registrar
            #send table
            if activeClients > 0:
                for client1 in registrar.keys():
                    client1_online = False 
                    userInfo1 = registrar[client1]
                    
                    if userInfo1[2] == 'yes': #Check if user is online
                        client1_online = True

                    for client2 in registrar.keys():
                        if client2 is not client1 and client1_online:
                            print 'Sending', client1, 'info on', client2
                            #Send client2s information to client1
                            serverSocket.sendto(client2, (userInfo1[0], userInfo1[1]))#username
                            userInfo2 = registrar[client2]
                            serverSocket.sendto(userInfo2[0], (userInfo1[0], userInfo1[1]))#IP
                            serverSocket.sendto(str(userInfo2[1]), (userInfo1[0], userInfo1[1]))#Socket
                            serverSocket.sendto(userInfo2[2], (userInfo1[0], userInfo1[1]))#status
                print 'Table sent to all online clients'
                
            #serverSocket.sendto('>>>', clientAddress)
            
    #Server shutdown Ctrl+C
    except KeyboardInterrupt:
        print '\n--- Server offline'
        serverSocket.close()
        registrar = {}
        sys.exit()

elif mode == 'client':
    #At this point, serverPort and clientPort are validated, show prompt and send to server
    #clientMessage = raw_input('>>> ').strip().split() #message is a list
    try:
        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Create client socket

        except socket.error as msg:
            print 'Client socket failed to create.\n'
            sys.exit()
        
        ack = False
        table = {}
        timeout = 1
        
        ''' START REGISTRATION -------------------------------------------------------'''
               
        firstLine = raw_input('>>> ') #reg command expected

        while len(firstLine.split()) < 2:
            print '>>> [You are not online, please register first. Usage: reg', username, ']'
            firstLine = raw_input('>>> ')

        command = (firstLine.split())[0]
        check_username = (firstLine.split())[1]

        while (command == 'reg') == False:
            print '>>> [You are not online, please register first. Usage: reg', username,']'
            firstLine = raw_input('>>> ')
            command = (firstLine.split())[0]
            
        while (username == check_username) == False and len(firstLine.split()) < 2:
            print '>>> [You can only register using your username:',username,']\n>>> [Usage: reg', username,']'
            firstLine = raw_input('>>> ')
            if len(firstLine.split()) > 1:
                check_username = (firstLine.split())[1]
            
        #Send registration to server, try 5 times and then consider offline
        try:
            clientSocket.sendto(firstLine, (serverName, serverPort))
            clientSocket.settimeout(.5)
            serverMessage, serverAddress = clientSocket.recvfrom(2048)

        except socket.timeout:
            for tries in range(0,5):
                    try:
                        clientSocket.sendto(firstLine, (serverName, serverPort))
                        serverMessage, serverAddress = clientSocket.recvfrom(2048)
                        if 'welcome' in serverMessage:
                            ack = True
                            break
                    except socket.timeout:
                        continue
            
            if not ack:
                print '>>> [Server not responding]'
                print '>>> [Exiting]'
                clientSocket.close()
                sys.exit()
                
        print serverMessage,

        #Check if table needs to be downloaded, receive info of other clients
        try:
            clientSocket.settimeout(.5)
            otherClients, serverAddress = clientSocket.recvfrom(2048)
            otherClients = int(otherClients)
            if otherClients > 0:
                for i in range(0, otherClients):
                    nameOtherClient, serverAddress = clientSocket.recvfrom(2048)
                    IPOtherClient, serverAddress = clientSocket.recvfrom(2048)
                    socketOtherClient, serverAddress = clientSocket.recvfrom(2048)
                    statusOtherClient, serverAddress = clientSocket.recvfrom(2048)
                    table[nameOtherClient] = [IPOtherClient, int(socketOtherClient), statusOtherClient]
                print '[Client table updated.] --', table, '\n>>> ',

        except socket.timeout:
            pass

        except ValueError:
            if 'You have messages' in otherClients:
                print otherClients,
                clientSocket.sendto('ack', serverAddress)
                try:
                    numberOfMessages, serverAddress = clientSocket.recvfrom(2048)
                    numberOfMessages = int(numberOfMessages)
                    for i in range(0, numberOfMessages):
                        try:
                            incomingMessage, serverAddress = clientSocket.recvfrom(2048)
                        except socket.timeout:
                            print '>>> [Failed to receive incoming message.]',
                            continue
                    
                        print '>>>',incomingMessage,'\n',
                    print '>>>',
                except socket.timeout:
                    print '[Failed to receive messages.]\n>>> ',
                    pass
                except ValueError:
                    pass
                    

        ''' END REGISTRATION ---------------------------------------------------'''
        timeout = 1 #Needs to be an integer
        signal.signal(signal.SIGALRM, alarmHandler)
        noMessageSent = True
        originalServer = serverAddress
        online = True
        while True:
            try:
                #print 'Waiting for server'
                signal.alarm(0)
                clientSocket.settimeout(2)
                serverMessage, serverAddress = clientSocket.recvfrom(2048)
                #print 'message is', serverMessage, 'from', serverAddress
                '''
                if serverAddress == originalServer:
                    for k in table.keys():
                        if k in serverMessage:
                            print '>>>', serverMessage,'\n',
                            clientSocket.sendto('ack', serverAddress)
                '''

                if 'You have messages' in serverMessage and serverAddress == originalServer:
                    print serverMessage,
                    clientSocket.sendto('ack', serverAddress)
                    try:
                        clientSocket.settimeout(1)
                        numberOfMessages, serverAddress = clientSocket.recvfrom(2048)
                        numberOfMessages = int(numberOfMessages)
                        if numberOfMessages > 0:
                            clientSocket.settimeout(5)
                            for i in range(0, numberOfMessages):
                                try:
                                    incomingMessage, serverAddress = clientSocket.recvfrom(2048)
                                except socket.timeout:
                                    print '>>> [Failed to receive incoming message.]',
                                    continue

                                print '>>>',incomingMessage,'\n',
                            print '>>>',

                    except socket.timeout:
                        print '>>> [Failed to finish downloading messaged. Request timed out.]\n>>>',
                        continue
                    except ValueError:
                        pass
     
                if 'ping' in serverMessage:
                    clientSocket.sendto('ack', serverAddress)
                
                try:
                    otherClients = int(serverMessage) #Check if its server is sending table
                    #print 'About to receive', otherClients, 'clients'
                    if otherClients > 0:
                        clientSocket.settimeout(None)
                        #print 'stuck in table'
                        for i in range(0, otherClients):
                            nameOtherClient, serverAddress = clientSocket.recvfrom(2048)
                            IPOtherClient, serverAddress = clientSocket.recvfrom(2048)
                            socketOtherClient, serverAddress = clientSocket.recvfrom(2048)
                            statusOtherClient, serverAddress = clientSocket.recvfrom(2048)
                            table[nameOtherClient]=[IPOtherClient,int(socketOtherClient),statusOtherClient]
                        print '[Client table updated.] --', table, '\n>>>',
                        
                except ValueError:
                    pass
                
                #Check if serverAddress is actually a client on their local table
                recMessage = False
                sender = 'unknown'

                for otherC, otherCInfo in table.items():
                    if otherCInfo[1] == serverAddress[1]:
                        recMessage = True
                        sender = otherC
                
                if sender is not 'unknown' and recMessage: #Need to send ack to sender
                    if 'ack' in serverMessage:
                        print '>>> [Message received by', sender, ']\n>>>',
                    else:
                        clientSocket.sendto('ack', serverAddress)
                        print sender, ':', serverMessage, '\n>>>',
                    recMessage = False
                    sender = 'unknown'
                    serverAddress = originalServer
                    
            except socket.timeout:
                pass

            signal.alarm(timeout)
            try:
                clientMessage = ''
                clientMessage = raw_input() 
                #print 'User input was:', clientMessage
                signal.alarm(0)
                user_command = ''
                
                if len(clientMessage.split()) > 0:
                    user_command = (clientMessage.split())[0]
                else:
                    continue
                
                ''' HANDLE USER INPUT '''
                if 'dereg' in user_command:
                    #print 'user is trying to dereg'
                    if len(clientMessage.split()) > 1:
                        check_username = (clientMessage.split())[1]
                    else:
                        print '>>> [Invalid dereg command.]\n>>> ',
                        continue
                    while (check_username == username) == False:
                        print '>>> [You need to dereg using your own username.]'
                        print '>>> [Usage: dereg', username, ']'
                        clientMessage = raw_input('>>> ')
                        if len(clientMessage.split()) > 1:
                            check_username = (clientMessage.split())[1]
                    
                    try:
                        clientSocket.sendto(clientMessage, originalServer)
                        clientSocket.settimeout(.5)
                        serverMessage, serverAddress = clientSocket.recvfrom(2048)
                        #print 'User 1st try successfull'
                        print serverMessage,
                        if 'Bye' in serverMessage:
                            online = False
                            firstLine = raw_input() #BLOCKING CALL
                            command = (firstLine.split())[0]
                            check_username = ''
                            
                            if len(firstLine.split()) > 1:
                                check_username = (firstLine.split())[1]

                            if (command == 'reg') == False:
                                print '>>> [You are not online, please register first. Usage: reg', username,']'
                                firstLine = raw_input('>>> ')

                            while (username == check_username) == False:
                                print '>>> [You can only register using your username:',username,']\n>>> [Usage: reg', username,']'
                                firstLine = raw_input('>>> ')
                                check_username = (firstLine.split())[1]
            
                            #Send registration to server, try 5 times and then consider offline
                            try:
                                clientSocket.sendto(firstLine, (serverName, serverPort))
                                serverMessage, serverAddress = clientSocket.recvfrom(2048)
                                if 'welcome' in serverMessage:
                                    ack = True
                                    online = True
                                print serverMessage,
  #                              print 'Stuck after receiving welcome'
                                continue
                                
                            except socket.timeout:
                                for tries in range(0,5):
                                    try:
                                        clientSocket.sendto(firstLine, (serverName, serverPort))
                                        serverMessage, serverAddress = clientSocket.recvfrom(2048)
                                        if 'welcome' in serverMessage:
                                            ack = True
                                            online = True
                                            break
                                    except socket.timeout:
                                        continue
            
                                if not ack:
                                    print '>>> [Server not responding]'
                                    print '>>> [Exiting]'
                                    clientSocket.close()
                                    sys.exit() 
                                continue

                    except socket.timeout:
                        #print 'User 1st try unsuccessful, in first except block, server timed out'
                        dereg_ack = False
                        for tries in range(0, 5):
                            try:
                                clientSocket.sendto(clientMessage, serverAddress)
                                clientSocket.settimeout(.5)
                                serverMessage, serverAddress = clientSocket.recvfrom(2048)
                                #print 'User 2nd try successfull'
                                if 'Bye' in serverMessage:
                                    dereg_ack = True
                                    online = False
                                    print serverMessage,
                                    break

                            except socket.timeout:
                                continue
                        #print 'dereg ack is', dereg_ack
                        if dereg_ack == False:    
                            print '>>> [Server not responding]'
                            print '>>> [Exiting]'
                            clientSocket.close()
                            sys.exit()
                        
                        else:
                            online = False
                            firstLine = raw_input('>>> ') #reg command expected
                            command = (firstLine.split())[0]
                            check_username = ''
                            if len(firstLine.split()) > 1:
                                check_username = (firstLine.split())[1]
                            
                            while (command == 'reg') == False:
                                print '>>> [You are not online, please register first. Usage: reg', username,']'
                                firstLine = raw_input('>>> ')
                                command = (firstLine.split())[0]

                            while (username == check_username) == False:
                                print '>>> [You can only register using your username:',username,']\n>>> [Usage: reg', username,']'
                                firstLine = raw_input('>>> ')
                                if len(firstLine.split()) > 1:
                                    check_username = (firstLine.split())[1]
                                            
                            #Send registration to server, try 5 times and then consider offline
                            try:
                                clientSocket.sendto(firstLine, (serverName, serverPort))
                                serverMessage, serverAddress = clientSocket.recvfrom(2048)
                                if 'welcome' in serverMessage:
                                    ack = True
                                    online = True
                                    print serverMessage,
                                    
                            except socket.timeout:
                                for tries in range(0,5):
                                    try:
                                        clientSocket.sendto(firstLine, (serverName, serverPort))
                                        serverMessage, serverAddress = clientSocket.recvfrom(2048)

                                        if 'welcome' in serverMessage:
                                            ack = True
                                            online = True
                                            print serverMessage,
                                            break
                                    except socket.timeout:
                                        continue
                                                        
                                if not ack:
                                    print '>>> [Server not responding]'
                                    print '>>> [Exiting]'
                                    clientSocket.close()
                                    sys.exit()
                                else:
                                    continue
    
                elif 'send' in user_command:
                    clientMessageList = clientMessage.strip().split()
                    if len(clientMessageList) > 1:
                        recp = clientMessageList[1]
                    else:
                        print '[Invalid send command.]\n>>> ',
                        continue

                    #print username, 'is sending', clientMessageList[1], 'a message'
                    recp = clientMessageList[1]
                    if recp == username:
                        print '>>> [You fool! Try again. This time don\'t send a message to yourself.]\n>>>',
                        continue
                    if recp not in table:
                        print '>>> [', recp, 'is not in table. Try again.]\n>>>',
                        continue
                        
                    recpInfo = table[recp]
                    recpIP = recpInfo[0]
                    recpPort = recpInfo[1]
                    size = len(clientMessageList[0]) + len(recp) + 1
                    originalCM = clientMessage #Save a copy for if need to send to server
                    clientMessage = clientMessage[size:]
                    recp_status = recpInfo[2]

                    try:
                        if 'yes' in recp_status:
                            clientSocket.sendto(clientMessage, (recpIP,recpPort))
                        clientSocket.settimeout(2)
                        #print username, 'waiting for ack from', recp
                        recpMessage, recpAddress = clientSocket.recvfrom(2048)
                        if 'ack' in recpMessage:
                            print '>>> [Message received by', recp, ']\n>>>',
                            noMessageSent = False
                            
                    except socket.timeout:
                        #Send message to server, need to tell server that its an offline chat messg
                        print '>>> [No ACK from', recp, ', message sent to server.]\n>>> ',
                        try:
                            clientSocket.sendto(originalCM, originalServer)
                            clientSocket.settimeout(1)
                            serverMessage, serverAddress = clientSocket.recvfrom(2048)
                            print serverMessage,
                            if 'received' in serverMessage:
                                continue
                            
                        except socket.timeout:
                            #print '[Server is not responding. Will try again]\n>>> ',
                            for i in range(0,5):
                                try:
                                    clientSocket.sendto(originalCM, originalServer)
                                    serverMessage, serverAddress = clientSocket.recvfrom(2048)
                                    print serverMessage,
                                    if 'received' in serverMessage:
                                        ack = True
                                        break
                                except socket.timeout:
                                    continue
                            if not ack:
                                print '[Server not responding.]'
                                print '>>> [Exiting]'
                                clientSocket.close()
                                sys.exit()
                        pass
                else:
                    print '[Please enter an available command: dereg or send.]\n>>>',
            except AlarmException:
                pass

    except KeyboardInterrupt:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        print '\n--- Logging off'
        clientSocket.close()
        sys.exit()

    
