#Vanilla plugin for Navi Network servers
#
#This plugin has basic commands and was intended to be used as an example when you make you'r own
#
#Init() is called when the plugin is loaded, and comes with the Twisted reactor,
#the World() object(used to make changes the world), PostChat() (used to write something in the chat)
#and PostPopup() (used to send a popup to the wanted user/s)
#Init() must return a list with the chat commands or events you want to register,
#and the function to call when it get triggered/called.
#
#The function called when a command or event is called, parameters are given:
#-The text after the command, or an empty string if event. Ex: it is "pbsds" when the player wrote "/kick pbsds"
#-ID of the person who called the command/event, 0 if called by server.
#-A dictionary where the keys are the userIDs and contains the protocol.
#
#You can register any kind of caht command you want, but some strings are automatically
#called by the server(i'll call these events from now on)
#Here's a list of the event's available:
#
#	\x01 - replaces the built-in chat
#	\x02 - called when a user logs in and replaces the built-in login message, can be used as MOTD
#	\x03 - Called when a user logs out and replaces the built-in logout message
#
#Keep in mind:
#
#The working directory is set to the folder where Server.py lies!

with open("Plugins/OP.txt","r") as f:#I'm trying to make people with special rights be stored in OP.txt for all plugins!
	OPs = f.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
Kicked = []#Used to know who's been kicked, to not display the "jacked out" message.
reactor = None
World = None
PostChat = None
PostPopup = None

def Init(p1,p2,p3,p4):
	global reactor, World, PostChat, PostPopup
	reactor = p1
	World = p2
	PostChat = p3
	PostPopup = p4
	print "Navi Network vanilla plugin was loaded!"
	return (("\x01",Chat),("\x02",Login),("\x03",Logout),#Events
			("/help",Help),("/spawn",Spawn),("/motd",MOTD),("/msg",Msg),("/who",Who),("/me",Me),#commands
			("/tp",TP),("/tphere",TPHere),("/setspawn",SetSpawn),("/say",Say),("/kick",Kick))#OP commands

#Events:
def Chat(Data, UserID, UsersOnline):#Replaces the built-in chat design
	global OPs
	Color = 0xBBBBBB
	if UsersOnline[UserID].User.Username in OPs:
		Color = 0x40FF40
	
	print "[CHAT] <"+UsersOnline[UserID].User.Username+">",Data
	PostChat((Color,UsersOnline[UserID].User.Username+": ",0xFFFFFF,Data))
def Login(Data, UserID, UsersOnline):#Replaces the built-in login message
	MOTD(Data, UserID, UsersOnline, False)
	
	global PostChat
	print "[INFO]",UsersOnline[UserID].User.Username,"jacked in!"
	PostChat((0xFFFF00,UsersOnline[UserID].User.Username+" jacked in!"))
	return True#To replace the built-in "jacked in" message
def Logout(Data, UserID, UsersOnline):#Replaces the built-in logout message
	global Kicked
	if UsersOnline[UserID].User.Username in Kicked:
		Kicked.remove(UsersOnline[UserID].User.Username)
	else:
		print "[INFO]",UsersOnline[UserID].User.Username,"jacked out..."
		PostChat((0xFFFF00,UsersOnline[UserID].User.Username+" jacked out."))
	return True#To replace the built-in "jacked out" message

#User commands:
def Help(Data, UserID, UsersOnline):#Show a list of available commands
	global OPs
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /help"
	PostChat((0xFF9090,"Here is a list of the available commands to you:"),[UserID])
	
	if UsersOnline[UserID].User.Username in OPs:
		PostChat((0x88B0FF,"/help, /kick, /motd, /me, /msg, /say, /setspawn, /tp, /tphere and /who"),[UserID])
	else:
		PostChat((0x88B0FF,"/help, /motd, /me, /msg and /who"),[UserID])
def MOTD(Data, UserID, UsersOnline, PostCMD = True):#Message of the day, also called by Login()
	global PostChat, PostPopup
	if PostCMD: print "[CMD]  "+UsersOnline[UserID].User.Username+" /motd"
	PostPopup(1,["Welcome to\nthis server!\n\nKeep in mind:\nNavi Network\nis currently in\nalpha, so\ndon't expect it\nto be bugless!"],[UserID])
	PostChat((0xFF9090,"Hello "+UsersOnline[UserID].User.Username+"! Welcome to this server!"),[UserID])

def Spawn(Data, UserID, UsersOnline):#Teleports user to spawn
	global World
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /spawn"
	PostChat((0x88B0FF,"You've been teleported to Spawn"),[UserID])
	UsersOnline[UserID].SetPlayerPosition(World.Spawn[0],World.Spawn[1],World.Spawn[2],World.Spawn[3])
def Who(Data, UserID, UsersOnline):#Shows who's online
	global OPs, PostChat
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /who"
	PostChat((0xFF9090,"There are "+str(len(UsersOnline))+" players online:"),[UserID])
	string = []
	for i in UsersOnline.values():
		if i.User.Username in OPs:
			string.extend((0x88FFB0,"[OP]"+i.User.Username,0xFFFFFF,", "))
		else:
			string.extend((0x88B0FF,i.User.Username,0xFFFFFF,", "))
	PostChat(string[:-2],[UserID])
def Me(Data, UserID, UsersOnline):#A tweet-ish function
	if not Data:
		print "[CMD]  "+UsersOnline[UserID].User.Username+" /me",Data
		PostChat((0xFF9090,"Usage of /me: /me <text>"),[UserID])
		return
	
	print "[CHAT] *",UsersOnline[UserID].User.Username,Data
	PostChat((0xFFFFFF,"* ",0x40FF40,UsersOnline[UserID].User.Username+" ",0xFFFFFF,Data))
def Msg(Data, UserID, UsersOnline):#Send a personal message to someone
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /msg",Data
	if not Data:
		PostChat((0xFF9090,"Usage of /msg: /msg <username> <text>"),[UserID])
		return
	
	try:
		Data = Data.split(" ")
		Reciever = Data[0]
		Message = " ".join(Data[1:])
	except:
		PostChat((0xFF9090,"Invalid input! Usage of /msg: /msg <username> <text>"),[UserID])
		return
	if Reciever == UsersOnline[UserID].User.Username:
		PostChat((0xFF9090,"You can't send a message to yourself!"),[UserID])
		return
	
	for i in UsersOnline.values():
		if i.User.Username == Reciever:
			PostChat((0x88B0FF,"["+UsersOnline[UserID].User.Username+" -> "+Reciever+"] ",0xFFFFFF, Message),(i.ID,UserID))
			return
	PostChat((0xFF9090,"Could not find the user \""+Reciever+"\""),[UserID])

#OP stuff
def TP(Data, UserID, UsersOnline):#Teleports you to others
	global OPs
	if UsersOnline[UserID].User.Username not in OPs:
		print "[CMD] ",UsersOnline[UserID].User.Username,"tried to access the OP command /tp",Data
		PostChat((0xFF8080,"You're not allowed to use /tp"),[UserID])
		return
	print "[CMD] ",UsersOnline[UserID].User.Username,"/tp",Data
	if not Data:
		PostChat((0xFF9090,"Usage of /tp: /tp <username>"),[UserID])
		return
	if Data == UsersOnline[UserID].User.Username:
		PostChat((0xFF9090,"You can't TP to yourself!"),[UserID])
		return
	for i in UsersOnline.values():
		if i.User.Username == Data:
			UsersOnline[UserID].SetPlayerPosition(i.User.CellPos[0],i.User.CellPos[1],i.User.CellPos[2],i.User.CellPos[3])
			PostChat((0x88B0FF,"You teleported to "+i.User.Username),[UserID])
			PostChat((0x88B0FF,UsersOnline[UserID].User.Username+" teleported to you."),[i.ID])
			return
	PostChat((0xFF9090,"Could not find the user \""+Data+"\""),[UserID])
def TPHere(Data, UserID, UsersOnline):#Teleports others to you
	global OPs
	if UsersOnline[UserID].User.Username not in OPs:
		print "[CMD] ",UsersOnline[UserID].User.Username,"tried to access the OP command /tphere",Data
		PostChat((0xFF8080,"You're not allowed to use /tphere"),[UserID])
		return
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /tphere",Data
	if not Data:
		PostChat((0xFF9090,"Usage of /tphere: /tphere <username>"),[UserID])
		return
	if Data == UsersOnline[UserID].User.Username:
		PostChat((0xFF9090,"You can't TP yourself!"),[UserID])
		return
	for i in UsersOnline.values():
		if i.User.Username == Data:
			i.SetPlayerPosition(UsersOnline[UserID].User.CellPos[0],UsersOnline[UserID].User.CellPos[1],UsersOnline[UserID].User.CellPos[2],UsersOnline[UserID].User.CellPos[3])
			PostChat((0x88B0FF,"You've been teleported to "+UsersOnline[UserID].User.Username),[i.ID])
			PostChat((0x88B0FF,i.User.Username+" has been teleported to you."),[UserID])
			return
	PostChat((0xFF9090,"Could not find the user \""+Data+"\""),[UserID])
def Say(Data, UserID, UsersOnline):#A red message with the "Server: " prefix
	global OPs
	if UsersOnline[UserID].User.Username not in OPs:
		print "[CMD] ",UsersOnline[UserID].User.Username,"Tried to access the OP command /say"
		PostChat((0xFF8080,"You're not allowed to use /say"),[UserID])
		return
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /say",Data
	if not Data:
		PostChat((0xFF9090,"Usage of /say: /say <text>"),[UserID])
		return
	
	PostChat((0xFF9090,"Server: "+Data))
def Kick(Data, UserID, UsersOnline):#Kicks a user
	global OPs, Kicked
	if UsersOnline[UserID].User.Username not in OPs:
		print "[CMD] ",UsersOnline[UserID].User.Username,"tried to access the OP command /kick "+Data
		PostChat((0xFF8080,"You're not allowed to use /kick"),[UserID])
		return
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /kick",Data
	if not Data:
		PostChat((0xFF9090,"Usage of /kick: /kick <username>"),[UserID])
		return
	
	Found = False
	for i in UsersOnline.values():
		if Data == i.User.Username:
			Found = True
			Kicked.append(Data)
			i.transport.loseConnection()
			PostChat((0xFF8080,Data+" was kicked by "+UsersOnline[UserID].User.Username))
	
	if not Found:
		PostChat((0xFF8080,"The user \""+Data+"\" was not found, no kick."),[UserID])#only sent to the person who called this command
def SetSpawn(Data, UserID,UsersOnline):#Move Spawn to the player who calls this
	global OPs, World, PostChat
	if UsersOnline[UserID].User.Username not in OPs:
		print "[CMD] ",UsersOnline[UserID].User.Username,"Tried to access the OP command /setspawn"
		PostChat((0xFF8080,"You're not allowed to use /setspawn"),[UserID])
		return
	print "[CMD]  "+UsersOnline[UserID].User.Username+" /setspawn"
	World.Spawn = UsersOnline[UserID].User.CellPos
	PostChat((0xFF8080,"Spawn has been set!"))