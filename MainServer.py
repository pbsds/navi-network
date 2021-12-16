'''
Info table:

__DEC___Game clients:______Server clients:__
|     |                  |                  \
|   1 | Log in           | Info Update
|   2 | Request servers  | 
|   3 |                  | 
|   4 |                  | 
|   5 |                  | 
|   6 |                  | 
|_____|__________________|__________________/
'''

#import stuff:
if __name__ == "__main__": print "Importing the needed modules..."
import hashlib, sys, os, ConfigParser, cgi
from twisted.internet import reactor
from twisted.internet.protocol import Protocol,Factory
from twisted.web import server as WebServer, resource as WebResource
try:
	import psyco
	psyco.full()
except ImportError:
	print "No psyco import!"
if __name__ == "__main__": print "Changing working dir..."
os.chdir(sys.path[0]+"/MainServer")

#Hash computing:
if __name__ == "__main__": print "Defining global functions and variables..."
def MakeMD5(Data):#returns in hex
	return hashlib.md5(Data).hexdigest()
def MakeSHA1(Data):#returns in hex
	return hashlib.sha1(Data).hexdigest()

#Globals:
with open("Admins.txt","r") as f:
	Admins = f.read().replace("\r\n", "\n").replace("\r", "\n").split("n")
Connections = 0
Port = 31337
UsersOnline = {}
Servers = {}
Version = "Alpha v0.4"
class Dummy: pass

#Protocol:
if __name__ == "__main__": print "Defining protocols..."
class GameClient(Protocol):
	def __init__(self):
		self.Buffer = ""#To cut of the input at the right place
		self.Connected = False
		self.LoggedIn = False
		self.User = Dummy()
		self.User.Username = ""
		self.INI = None
		self.CheckedDate = False
		self.Pong = True
	def connectionMade(self):
		global Connections
		Connections += 1
		reactor.callLater(30, self.Step)
		self.Connected = True
		print "Client",self.transport.getPeer().host,"connected."
	def connectionLost(self, reason):
		global Connections, UsersOnline
		Connections -= 1
		self.Connected = False
		if self.LoggedIn:
			self.UpdateINI()
			del UsersOnline[self.User.Username[:]]
		print "Client",self.transport.getPeer().host,"disconnected."
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			self.Buffer = self.Buffer.split("\x7F")
			for i in self.Buffer[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer[-1]
	#===
	def ParseData(self,Data):
		global Servers
		if Data == "Pong":
			self.Pong = True
			return
		
		if Data[0] == "\x01":#Login
			temp = Data[1:].split("\0")
			self.Login(temp[0],temp[1])
		elif Data[0] == "\x02":#Request public servers
			for i in Servers.values():
				self.Send("\x02%s %i %s %s" % (i[1],i[2],i[3],i[0]))#(IP, Port, OnlineCount, Name)
		elif Data[0] == "\x03":#Change apperance
			self.User.Character = map(int,Data[1:].split("\0"))
		elif Data[0] == "\x04":#Check if client is outdated
			global Version
			if Data[1:] == Version:
				self.CheckedDate = True
			else:
				self.Send("\x04")
				print "Client",self.transport.getPeer().host," is outdated."
		elif Data[0] == "\x05":#Client wants to logout
			self.Logout()
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):#Called every half minute automatically
		if not self.Connected: return
		if not self.Pong:
			print "Client",self.transport.getPeer().host,"not responding, dissconnect."
			self.transport.loseConnection()
			return
		reactor.callLater(30, self.Step)
		self.UpdateINI()
		self.Send("Ping")
		self.Pong = False
	#===
	def UpdateINI(self):
		if not self.LoggedIn: return
		
		if not self.INI.has_section("Main"): self.INI.add_section("Main")
		if not self.INI.has_section("Skin"): self.INI.add_section("Skin")
		for i in range(len(self.User.Inventory)):
			if not self.INI.has_section("Item"+str(i+1)): self.INI.add_section("Item"+str(i+1))
		
		self.INI.set("Main","HP",str(self.User.HP))
		self.INI.set("Main","Zennies",str(self.User.Zennies))
		self.INI.set("Main","BugFrags",str(self.User.BugFrags))
		self.INI.set("Skin","Character",str(self.User.Character[0]))
		self.INI.set("Skin","Color",str(self.User.Character[1]))
		self.INI.set("Main","ItemCount",str(len(self.User.Inventory)))
		
		j = 1
		for i in self.User.Inventory:
			self.INI.set("Item"+str(j),"x",str(i[0]))
			self.INI.set("Item"+str(j),"y",str(i[1]))
			self.INI.set("Item"+str(j),"ID",str(self.User.Inventory[i][0]))
			self.INI.set("Item"+str(j),"Attributes",str(self.User.Inventory[i][1]))
			j += 1
		
		Handle = open("Users/"+self.User.Username+".ini","w")
		self.INI.write(Handle)
		Handle.close()
	def Login(self,Username,Password):
		global UsersOnline
		#if trying to log in without checking if outdated(Happens with the first client):
		if not self.CheckedDate:
			self.transport.loseConnection()
			return
			
		#Check if the username is registered and if not already logged on:
		if re.match(r'^[a-zA-Z0-9_\-]+$',Username) and os.path.exists("Users/"+Username+".ini") and Username not in UsersOnline:
			handle = open("Users/"+Username+".ini","r")
			INI = ConfigParser.ConfigParser()
			INI.readfp(handle)
			handle.close()
			#Check if it is the correct password:
			if INI.get("Password","Hash1") == MakeMD5(Password).lower() and INI.get("Password","Hash2") == MakeSHA1(Password).lower():
				UsersOnline[Username] = self
				self.LoggedIn = True
				self.INI = INI
				
				#Read User:
				self.User.Username = Username
				self.User.HP = INI.getint("Main","HP")
				self.User.Zennies = INI.getint("Main","Zennies")
				self.User.BugFrags = INI.getint("Main","BugFrags")
				self.User.Character = [INI.getint("Skin","Character"),INI.getint("Skin","Color")]
				
				self.User.Inventory = {}
				
				for i in range(INI.getint("Main","ItemCount")):
					temp = (INI.getint("Item"+str(i+1),"x"),INI.getint("Item"+str(i+1),"y"))
					self.User.Inventory[temp] = (INI.getint("Item"+str(i+1),"ID"),INI.getint("Item"+str(i+1),"Attributes"))
				
				#Creating the data to return:
				ret = []
				ret.append(str(self.User.HP))
				ret.append(str(self.User.Zennies))
				ret.append(str(self.User.BugFrags))
				ret.append(str(self.User.Character[0]))
				ret.append(str(self.User.Character[1]))
				ret.append(str(len(self.User.Inventory)))
				for i in self.User.Inventory:
					ret.append(str(i[0]) + "x" + str(i[1]) + "-" + str(self.User.Inventory[i][0]) + "-" + str(self.User.Inventory[i][1]))
				
				#Return data to client:
				print "Client",self.transport.getPeer().host,"logged on as",Username
				self.Send("\x01Y"+" ".join(ret))
				return
		print "Client",self.transport.getPeer().host," failed to log on as",Username
		self.Send("\x01N")
	def Logout(self):
		if self.LoggedIn:
			print "Client",self.transport.getPeer().host,"logged off as",self.User.Username
			self.LoggedIn = False
			self.UpdateINI()
			del UsersOnline[self.User.Username]
			self.User.Username = ""
			del self.User.HP
			del self.User.Zennies
			del self.User.BugFrags
			del self.User.Character
			del self.User.Inventory
			self.Send("\x05")
		else:
			print "Client",self.transport.getPeer().host,"failed to logg off as",self.User.Username
class ServerClient(Protocol):
	def __init__(self):
		self.Buffer = ""#To cut of the input at the right place
		self.ID = None
		self.CheckedDate = False
		self.Connected = False
		self.Pong = True
	def connectionMade(self):
		global Connections, Admins
		Connections += 1
		print "Server",self.transport.getPeer().host,"connected."
		self.Connected = True
		reactor.callLater(30, self.Step)
		
		#Send admins:
		self.Send("\x02"+"\0".join(Admins))
	def connectionLost(self, reason):
		global Connections, UsersOnline, Servers
		Connections -= 1
		self.Connected = False
		if self.ID:
			del Servers[self.ID]
		print "Server",self.transport.getPeer().host,"disconnected."
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			self.Buffer = self.Buffer.split("\x7F")
			for i in self.Buffer[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer[-1]
	#===
	def ParseData(self,Data):
		global Servers
		if Data == "Pong":
			self.Pong = True
			return
		
		if Data[0] == "\x01":#Get info
			if not self.CheckedDate:
				self.transport.loseConnection()
				return
			if self.CheckedDate == 2:
				return
			
			Data = Data[1:].split(" ")
			Data = (" ".join(Data[2:]),self.transport.getPeer().host,int(Data[0]),Data[1],self)#(Name, IP, Port, OnlineNum, protocol)
			if not self.ID:
				self.ID = 1
				while self.ID in Servers:
					self.ID += 1
				print "Server",self.transport.getPeer().host,"registered as:",Data[0]
			Servers[self.ID] = Data
		elif Data[0] == "\x02":#Online count update
			Servers[self.ID] = (Servers[self.ID][0],Servers[self.ID][1],Servers[self.ID][2],Data[1:],Servers[self.ID][4])
		elif Data[0] == "\x03":#Check if server is outdated
			global Version
			if Data[1:] == Version:
				self.CheckedDate = True
			else:
				self.CheckedDate = 2
				self.Send("\x03")
				print "Server",self.transport.getPeer().host,"is outdated."
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):
		if not self.Connected: return
		if not self.Pong:
			print "Server",self.transport.getPeer().host,"not responding, dissconnect."
			self.transport.loseConnection()
			return
		reactor.callLater(30, self.Step)
		self.Send("Ping")
		self.Pong = False
		
#Website:
class Website(WebResource.Resource):
	isLeaf = False
	
	def render_GET(self, request):
		if request.prepath == [""]:
			return """		<html>
			<body><center>
				<h1><u>Navi Network</u></h1>
				<h2>Register for Navi Network:</h2>
				<form enctype="multipart/form-data" action="register" method="POST">
					<strong>Username:</strong><br/>
					<input name="usr" type="text" maxlength="15" /><br/>
					<strong>Password:</strong><br/>
					<input name="psw" type="password" maxlength="15" /><br/>
					<br/>
					<input type="submit" value="Register!" />
				</form>
			</center></body>
			</html>"""
		else:
			request.setResponseCode(404)
			return ""
	def render_POST(self,request):
		if request.prepath == ["register"]:
			try:
				usr = request.args['usr'][0]
				psw = request.args['psw'][0]
			except:
				return "<html><body><center><br/><br/><h1>Error - missing arguments!</h1></center></body></html>"
			if os.path.exists("Users/"+usr+".ini"):
				return "<html><body><center><br/><br/><h1>Error - Username taken!</h1></center></body></html>"
			if not re.match(r'^[a-zA-Z0-9_\-]+$',usr):
				return "<html><body><center><br/><br/><h1>Error - Username invalid!</h1></center></body></html>"
			
			INI = ConfigParser.ConfigParser()
			INI.add_section("Main")
			INI.add_section("Password")
			INI.add_section("Skin")
			
			INI.set("Main","HP","25")
			INI.set("Main","Zennies","0")
			INI.set("Main","BugFrags","0")
			INI.set("Main","ItemCount","0")
			
			INI.set("Password","hash1",MakeMD5 (psw))
			INI.set("Password","hash2",MakeSHA1(psw))
			
			INI.set("Skin","Character","0")
			INI.set("Skin","Color","0")
			
			Handle = open("Users/"+usr+".ini","w")
			INI.write(Handle)
			Handle.close()
			return "<html><body><center><br/><br/><h1>Success!</h1><p>Your user <strong>"+cgi.escape(usr)+"</strong> was successfully registered.</p></center></body></html>"
		else:
			request.setResponseCode(404)
			return ""
	def getChild(self, name, request):
		return self

if __name__ == "__main__":
	print "Starting up server..."
	GameFactory = Factory()
	GameFactory.protocol = GameClient
	SubServerFactory = Factory()
	SubServerFactory.protocol = ServerClient
	
	reactor.listenTCP(Port,GameFactory)
	reactor.listenTCP(Port+1,SubServerFactory)
	reactor.listenTCP(81, WebServer.Site(Website()))
	
	print "Run!"
	print
	reactor.run()
