#import stuff:
import sys, os, ConfigParser, glob
from twisted.internet import reactor
from twisted.internet.protocol import Protocol,ClientFactory,Factory
try:
	import psyco
	psyco.full()
except ImportError:
	print "No psyco import!"
os.chdir(sys.path[0]+"/Server")

#Globals:
Host = "213.138.175.204"
Version = "Alpha v0.4"
StepFrequency = 1.0/15#seconds
GAdmins = None#A list of global admins
Connections = 0
UsersOnline = {}
Plugins = []
Config = ConfigParser.ConfigParser()
with open("Settings.ini") as f:
	Config.readfp(f)
class Object: pass
UpdateMainServer = None

#World:
class World():
	def __init__(self):
		self.Saved = True#False if world have been changed since last time it was saved
		self.Chunks = {}#Map is stored here
		self.Spawn = (0,0,0,0)#[cX,cY,x,y]
		reactor.callLater(600,self.AutoSave)
		
		#Load save into memory:
		if os.path.exists("World/Config.txt"):
			with open("World/Config.txt","r") as Handle:
				File = Handle.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
				self.Spawn = tuple(map(int, File[0].split("x")))
		else:
			self.Spawn = (0,0,0,0)
		for i in map(lambda x: x.split(os.path.join("l","l")[1])[-1], glob.glob("World/*.chunk")):
				print "Loading",i,"into memory..."
				
				Handle = open("World/"+i,"r")
				File = Handle.read()
				Handle.close()
				
				i = map(int,i.split(".")[0].split("x"))
				if i[0] not in self.Chunks.keys():
					self.Chunks[i[0]] = {}
				if i[1] not in self.Chunks[i[0]].keys():
					self.Chunks[i[0]][i[1]] = []
				
				for x in range(16):
					yl = []
					for y in range(16):
						Ground = ord(File[48*y+3*x]) >> 4
						Sound = ord(File[48*y+3*x]) & 0x0F
						Object = ord(File[48*y+3*x+1])
						Tile = ord(File[48*y+3*x+2])
						
						yl.append([Ground,Sound,Object,Tile])
					self.Chunks[i[0]][i[1]].append(yl)
		if not self.Chunks:#If there was no map:
			print "Welcome to Navi Network server."
			print "To be able to host a server, you have to make a map:"
			print "Choose a map-type:"
			print "    0: Plain"
			print "    1: Branch center"
			while 1:
				Mode = raw_input('Enter number here: ')
				if Mode == "0":
					print "Choose the wanted ground color:"
					print "    0: Green"
					print "    1: Blue"
					print "    2: Lightblue"
					print "    3: Yellow"
					print "    4: Black"
					print "    5: Nothing (Not recomended)"
					print "    6: Pink"
					print "    7: Red"
					print "    8: Gray"
					print "    9: White"
					Color = 1337
					while Color not in range(10):
						Color = raw_input('Enter number here: ')
						if Color not in map(str,range(10)):
							print "Invalid input!"
						else:
							Color = int(Color)
					
					print "Good, now tell me how many chunks(16x16) you want in width:"
					Found = False
					while not Found:
						Width = raw_input('Enter number here: ')
						try:
							Width = int(Width)
							Found = True
						except:
							print "Invalid input!"
					
					print "Good, now tell me how many chunks you want in height:"
					Found = False
					while not Found:
						Height = raw_input('Enter number here: ')
						try:
							Height = int(Height)
							Found = True
						except:
							print "Invalid input!"
					
					print "Creating map..."
					for cX in range(Width):
						for cY in range(Height):
							if cX not in self.Chunks:
								self.Chunks[cX] = {}
							if cY not in self.Chunks[cX]:
								self.Chunks[cX][cY] = [[[Color,0,0,0] for i in xrange(16)] for i in xrange(16)]
					break
				elif Mode == "1":
					print "Enter the amount of chunks(16x16) you want in width each direction:"
					Found = False
					while not Found:
						Width = raw_input('Enter number here: ')
						try:
							Width = int(Width)
							Found = True
						except:
							print "Invalid input!"
					
					print "Good, now tell me how many chunks you want in height each direction:"
					Found = False
					while not Found:
						Height = raw_input('Enter number here: ')
						try:
							Height = int(Height)
							Found = True
						except:
							print "Invalid input!"
					
					print "Creating map..."
					for cX in range(Width*2):
						cX -= Width
						for cY in range(Height*2):
							cY -= Height
							if cX not in self.Chunks:
								self.Chunks[cX] = {}
							if cY not in self.Chunks[cX]:
								self.Chunks[cX][cY] = [[[5,0,0,0] for i in xrange(16)] for i in xrange(16)]
					for x in range(3):
						for y in range(3):
							self.Chunks[0][0][x][y][0] = 1
					self.Chunks[0][0][1][1][0] = 0
					self.Spawn = (0,0,1,1)
					break
				else:
					print "Invalid input!"
			self.Saved = False
			self.Save()
		else:
			print "World loaded!"
	def AutoSave(self):
		reactor.callLater(600,self.AutoSave)
		self.Save()
	def Save(self):
		if not self.Saved:
			print "Saving world..."
			self.Saved = True
			with open("World/Config.txt","w") as File:
				File.write("x".join(map(str,self.Spawn))+"\n")#Spawn
			Range16 = range(16)
			for cX in self.Chunks:
				for cY in self.Chunks[cX]:
					with open("World/"+str(cX)+"x"+str(cY)+".chunk","w") as File:
						write = []
						for y in Range16:
							for x in Range16:
								write.append(chr(self.Chunks[cX][cY][x][y][0]<<4 | self.Chunks[cX][cY][x][y][1]))
								write.append(chr(self.Chunks[cX][cY][x][y][2]))
								write.append(chr(self.Chunks[cX][cY][x][y][3]))
						File.write("".join(write))
			print "Saved world succesfully!"
	#====
	def GetCell(self,cX,cY,x,y):
		return self.Chunks[cX][cY][x][y][:]
	def SetCell(self,cX,cY,x,y,Ground=-1,Sound=-1,Object=-1,Tile=-1):#Only changed if value is above -1
		global UsersOnline
		self.Saved = False
		
		#Set the new cell:
		if Ground >= 0: self.Chunks[cX][cY][x][y][0] = Ground
		if Sound  >= 0: self.Chunks[cX][cY][x][y][1] = Sound
		if Object >= 0: self.Chunks[cX][cY][x][y][2] = Object
		if Tile   >= 0: self.Chunks[cX][cY][x][y][3] = Tile
		
		#Send change to clients:
		send = "\x01T"+"x".join(map(str,(cX,cY,x,y)))+" "+"-".join(map(str,self.Chunks[cX][cY][x][y]))
		for i in UsersOnline.values(): i.Send(send)
	def GetChunk(self,cX,cY):#Returns all the cells of the wanted chunk
		return self.Chunks[cX][cY]
	def SetChunk(self,cX,cY,Content):
		self.Saved = False
		
		#Set the new chunk:
		if cX not in self.Chunks.keys():
			self.Chunks[cX] = {}
		self.Chunks[cX][cY] = Content
		
		#Send change to clients:
		send = [str(cX)+"x"+str(cY)]
		for y in xrange(16):
			for x in xrange(16):
				send.extend((" ","-".join(map(str,Content[x][y]))))
		send = "\x01C"+"".join(send)
		for i in UsersOnline.values(): i.Send(send)
	def GetAvailableChunks(self):#Returns a list of the chunks available
		ret = []
		for cX in self.Chunks.keys():
			for cY in self.Chunks[cX].keys():
				ret.append((cX,cY))
		return ret

#Chat and popup:
def PostChat(Messagelist,To=None):#Posts a messeage to chat
	global UsersOnline
	if not To:
		for i in UsersOnline.values():
			i.Chat.append(Messagelist)
	else:	
		for i in list(To):
			UsersOnline[i].Chat.append(Messagelist)
def PostPopup(Type,Args=(),To=None):#Sends a popup to wanted users
	global UsersOnline
	Data = ""
	if Type == 1:#Text box
		if len(Args):
			Data = "\x01"+str(Args[0])
		else:
			return False
	else:#Not supported
		return False
	
	if not To:
		for i in UsersOnline.values():
			i.Popup.append(Data)
	else:	
		for i in list(To):
			UsersOnline[i].Popup.append(Data)
	return True

#Protocols:
class GameClient(Protocol):
	def __init__(self):
		self.Buffer = ""#To cut of the input at the right place
		
		self.ID = False
		self.User = Object()
		self.User.Direction = "S"
		self.User.Position = (0,0)
		self.User.Walking = 0
		self.User.Running = 0
		self.User.CellPos = (0,0,0,0)
		self.Chat = []#Messages to send to client
		self.Popup = []#Popups to send to client
		self.LoggedOf = []#IDs with users who logged of to send to client
		self.OldPositions = {}#Used to only send the position of a user if it has changed
	def connectionMade(self):
		global Connections, World, UpdateMainServer
		Connections += 1
		if Connections > Config.getint("Server","OnlineLimit"):#Dissconnect if server is full
			self.transport.loseConnection()
			Connections -= 1
		if UpdateMainServer: UpdateMainServer()
		self.Connected = True
		reactor.callLater(StepFrequency, self.Step)
		
		#Send world to client:
		for cX, cY in World.GetAvailableChunks():
			send = [str(cX)+"x"+str(cY)]
			for y in xrange(16):
				for x in xrange(16):
					send.extend((" ","-".join(map(str,World.Chunks[cX][cY][x][y]))))
			self.Send("\x01C"+"".join(send))
	def connectionLost(self, reason):
		global Connections, UsersOnline, Plugins, World
		Connections -= 1
		self.Connected = False
		if self.ID:
			for i in UsersOnline.values():
				i.LoggedOf.append(self.ID)
				if i.ID in self.OldPositions:
					del self.OldPositions[i.ID]
			
			Found = False
			for i in Plugins:
				if i[0] == "\x03":
					if i[1]("",self.ID,UsersOnline):
						Found = True
			if not Found:
				PostChat((0xFFFF00,self.User.Username+" jacked out..."))
				print "[INFO]",self.User.Username,"jacked out..."
			
			del UsersOnline[self.ID]
		if Connections == 0:
			World.Save()
		if UpdateMainServer: UpdateMainServer()
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			for i in self.Buffer.split("\x7F")[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer.split("\x7F")[-1]
	#===
	def ParseData(self,Data):
		global UsersOnline, World
		
		if Data[0] == "\x01":#Recieve client info
			Data = Data[1:].split("\0")
			self.User.Username = Data[0]
			self.User.Character = Data[1]
			self.User.Color = Data[2]
			
			self.ID = 1
			while self.ID in UsersOnline.keys():
				self.ID += 1
			UsersOnline[self.ID] = self
			
			self.SetPlayerPosition(World.Spawn[0],World.Spawn[1],World.Spawn[2],World.Spawn[3])
			self.Send("\x01S")
			
			Found = False
			for i in Plugins:
				if i[0] == "\x02":
					if i[1]("",self.ID,UsersOnline):
						Found = True
			if not Found:
				print "[INFO]",self.User.Username,"jacked in!"
				PostChat((0xFFFF00,self.User.Username+" jacked in!"))
		elif Data[0] == "\x02":#Movement
			Data = Data[1:].split(" ")
			self.User.Direction = Data[0]
			self.User.Position = (int(Data[1]),int(Data[2]))
			self.User.Walking = int(Data[3])
			self.User.Running = int(Data[4])
			self.User.CellPos = (int(Data[5]),int(Data[6]),int(Data[7]),int(Data[8]))
		elif Data[0] == "\x03":#Request playerdata
			i = int(Data[1:])
			if i in self.OldPositions:
				del self.OldPositions[i]
			if i in UsersOnline:
				self.Send("\x03"+"\0".join((Data[1:],UsersOnline[i].User.Username,str(UsersOnline[i].User.Character),str(UsersOnline[i].User.Color))))
		#elif Data[0] == "\x04":#RESERVED - Something about logging out
		elif Data[0] == "\x05":#Recieved a message in the chat.
			self.ParseChat(Data[1:])
		elif Data[0] == "\x06":#World change
			Change = [-1,-1,-1,-1]
			
			#Read info from client:
			Data = Data[1:].split(" ")#(cX,cY,x,y,type,ID)
			cX = int(Data[0])
			cY = int(Data[1])
			x = int(Data[2])
			y = int(Data[3])
			Change[int(Data[4])] = int(Data[5])
			
			#Set the change in world:
			World.SetCell(cX,cY,x,y,Change[0],Change[1],Change[2],Change[3])
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):
		if not self.Connected: return
		global StepFrequency, UsersOnline
		reactor.callLater(StepFrequency, self.Step)
		
		#Move players:
		if self.ID:
			send = ["\2"]
			for i in UsersOnline.values():
				if i.ID <> self.ID:
					if i.ID not in self.OldPositions:
						self.OldPositions[i.ID] = ""
					
					temp = ".".join((str(i.ID),i.User.Direction,str(i.User.Position[0]),str(i.User.Position[1]),str(i.User.Walking),str(i.User.Running)))
					if temp <> self.OldPositions[i.ID]:
						self.OldPositions[i.ID] = temp
						send.append(temp)
						send.append(" ")
			if len(send) > 1:
				self.Send("".join(send[:-1]))
		
		#Log off players:
		if self.LoggedOf:
			for i in self.LoggedOf:
				self.Send("\x04"+str(i))
			self.LoggedOf = []
		
		#Chat:
		if self.Chat:
			for Line in self.Chat:
				send = []
				for i in range(len(Line)/2):
					i *= 2
					send.append(str(Line[i])+"\0")
					
					#For ascii-signs with a value over 127:
					for j in Line[i+1]:
						if ord(j) >= 128:
							send.append("\1")
							send.append(chr(ord(j)-128))
							continue
						send.append(j)
					send.append("\0")
				
				self.Send("\x05"+"".join(send[:-1]))
			self.Chat = []
		
		#Popups:
		if self.Popup:
			for i in self.Popup:
				self.Send("\x06"+i)
			self.Popup = []
	def SetPlayerPosition(self,cX,cY,x,y):
		self.Send("\x01M"+"x".join(map(str,(cX,cY,x,y))))
	#====
	def ParseChat(self,RawString):#Scan through to check if any plugins should be called instead of posting to the chat.
		global Plugins, UsersOnline, GAdmins
		
		#For ascii-signs with a value over 127:
		String = []
		WasZero = False
		for i in RawString:
			if i == "\0" and not WasZero:
				WasZero = True
				continue
			if WasZero:
				String.append(chr(ord(i)+128))
				WasZero = False
			else:
				String.append(i)
		String = "".join(String)
		
		#If users is a global admin:
		if self.User.Username in GAdmins:
			#Check if a commando is called:
			for i in ("/gsay ","/gkick "):
				if len(i) > len(String): continue
				if i == String[:len(i)]:
					String = String[len(i):]
					if i == "/gsay ":#A /say for global admins:
						print "[ADMN] "+self.User.Username+":",String
						PostChat((0x80FFDD,"G-Admin: "+String))
					if i == "/gkick ":#A /kick for Global Admins:
						print "[ADMN] "+self.User.Username,"kicked",String
						Found = False
						for i in UsersOnline.values():
							if String == i.User.Username:
								PostChat((0x80FFDD,"[G-Admin] "+String+" got kicked by "+self.User.Username))
								i.transport.loseConnection()
								Found = True
						if not Found:
							PostChat((0x80FFDD,"\""+String+"\" was not found! No kick"),[self.ID])
					return
		
		#Check with the plugins if a commando is called:
		chat = None
		for i in Plugins:
			if i[0] == "\x01":#Found a plugin replacing the chat
				chat = i[1]
			if len(i[0]) > len(String): continue
			temp = i[0][:]
			if len(i[0])+1 <= len(String): temp += " "
			if temp == String[:len(temp)]:
				i[1](String[len(temp):],self.ID,UsersOnline)
				return
		
		#No function called, post in chat:
		if chat:#If a plugins replaces the chat:
			chat(String,self.ID,UsersOnline)
		else:#Built-in chat:
			print "[CHAT]",self.User.Username+":",String
			PostChat((0xFFFFFF,"".join((self.User.Username,": ",String))))
class ServerProtocol(Protocol):
	def connectionMade(self):
		global Port, UsersOnline, Name, UpdateMainServer, Version
		self.Buffer = ""#To cut of the input at the right place
		self.factory.Connected = True
		self.Connected = True
		UpdateMainServer = self.UpdateOnlineCount
		self.Ping = False
		reactor.callLater(60, self.Step)
		self.Send("\x03"+Version)
		self.Send("\x01"+Config.get("Server","Port")+" "+str(Connections).zfill(2)+"/"+Config.get("Server","OnlineLimit")+" "+Config.get("Server","Name"))
		print "Connected to main server!"
	def connectionLost(self, reason):
		global UsersOnline,UpdateMainServer
		if not self.factory.Outdated:
			print "Lost connection to main server!"
			reactor.callLater(90,self.factory.Reconnect)
		self.factory.Connected = False
		self.Connected = False
		UpdateMainServer = None
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			for i in self.Buffer.split("\x7F")[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer.split("\x7F")[-1]
	#===
	def ParseData(self,Data):
		global GAdmins
		
		if Data == "Ping":
			self.Send("Pong")
			self.Ping = True
			return
		
		if Data[0] == "\x02":
			GAdmins = Data[1:].split("\0")
		elif Data[0] == "\x03":
			self.factory.Outdated = True
			print
			print "This server is outdated! Please go to pbsds.tk and update."
			reactor.stop()
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):
		if not self.Connected: return
		if not self.Ping:
			print "Main server has stopped pinging, dissconnect."
			self.transport.loseConnection()
			return
		self.Ping = False
		reactor.callLater(60, self.Step)
	def UpdateOnlineCount(self):
		global UsersOnline
		self.Send("\x02"+str(Connections).zfill(2)+"/"+Config.get("Server","OnlineLimit").zfill(2))
class ServerFactory(ClientFactory):
	Outdated = False
	Connected = False
	Reconnecting = False
	def startedConnecting(self, connector):
		if not self.Reconnecting:
			print "Connecting to the main server..."
		self.Reconnecting = False
	def buildProtocol(self, addr):
		ret = ServerProtocol()
		ret.factory = self
		return ret
	def clientConnectionFailed(self, connector, reason):
		print 'Failed connecting to main server!'
		reactor.callLater(90,self.Reconnect)
	def Reconnect(self):
		global Host
		print "Reconnecting to the main server..."
		reactor.connectTCP(Host,31338,self)
		self.Reconnecting = True
#Plugins:
def LoadPlugins():
	print "Loading plugins..."
	global Plugins, World, PostChat, PostPopup
	
	#Backup and change sys.path:
	old = (sys.path[0],os.getcwd())
	sys.path[0] = os.getcwd()+"/Plugins"
	
	#Load plugins:
	for i in map(lambda x: x.split(os.path.join("l","l")[1])[-1][:-3], glob.glob("Plugins/*.py")):
		Plugins.extend(__import__(i).Init(reactor,World,PostChat,PostPopup))
	
	#Restore old sys.path:
	sys.path[0] = old

if __name__ == "__main__":
	print "                             Navi Network Server"
	print "                                 ",Version
	print "\\______________________________________________________________________________/"
	World = World()
	LoadPlugins()
	
	GameFactory = Factory()
	GameFactory.protocol = GameClient
	reactor.listenTCP(Config.getint("Server","Port"),GameFactory)
	reactor.connectTCP(Host,31338,ServerFactory())
	reactor.run()
	
	World.Save()