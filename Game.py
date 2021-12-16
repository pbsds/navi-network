#============================#
#========Navi Network========#
#=under development by pbsds=#
#============================#
#                            #
# This game requires at      #
# Python, pygame and Twisted #
# It won't work without them!#
#                            #
#============================#

#Globals:
Host = "navinet.pbsds.net"
Port = 31337
SendFrequency = 1.0/15#How often to send your position to the server
Version = "Alpha v0.4"

#Init:
print "Importing the needed modules..."
import os, sys, glob, ConfigParser, pygame, glob
from pygame.locals import *
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientFactory
try:
	import psyco
	psyco.full()
except ImportError:
	print "No psyco import!"
if len(sys.argv) >= 2:#Videodriver
	print "Changing video driver to",sys.argv[1]+"..."
	os.environ['SDL_VIDEODRIVER'] = sys.argv[1]
print "Changing working directory..."
RootPath = ""#Path to the folder containing this game
if hasattr(sys, 'frozen'):#Compiled archive directory
	RootPath = os.path.dirname(sys.executable)
	os.chdir(os.path.dirname(sys.executable)+"/Files")
elif os.path.exists(sys.path[0]+"/Files/font.ttc"):#First module folders
	RootPath = sys.path[0]
	os.chdir(sys.path[0]+"/Files")
elif os.path.exists(os.path.dirname(__file__)+"/Files"):#Script directory
	RootPath = os.path.dirname(__file__)
	os.chdir(os.path.dirname(__file__)+"/Files")
else:#Current workingdir
	RootPath = os.getcwd()
	os.chdir("Files")

#GameGlobals:
print "Initalizing pygame..."
pygame.init()
pygame.font.init()
temp = pygame.image.load("icon.bmp").convert(32); temp.set_colorkey(temp.get_at((0,0))); pygame.display.set_icon(temp); del temp; pygame.display.set_caption("Navi Network")
Window = pygame.display.set_mode((640,480))
Timer = pygame.time.Clock()
Mixer = pygame.mixer.init(44100)
GameSurface = pygame.Surface((420,368)).convert()
print "Setting up the global functions and settings..."
def QUITGame():
	print "Exiting..."
	reactor.stop()
def DrawSurface(Surface,Parent,Pos=(0,0)):
	return Parent.blit(Surface, Pos)
def UpdateWindow():
	pygame.display.flip()
def ListFolderContent(Path):
	ret = []
	if "*" not in Path: Path += os.path.join("l","l")[1]+"*"
	for i in glob.glob(Path):
		ret.append(i.split(os.path.join("l","l")[1])[-1])
	ret.sort()
	return ret
def Clamp(i,Min,Max):
	return min((max((i,Min)),Max))
def FixNewlines(string):#Fixes the problems with newlines on the different platforms
	return string.replace("\r\n", "\n").replace("\r", "\n")
with open(RootPath+"/Settings.ini","r") as f:
	GameSettings = ConfigParser.ConfigParser()
	GameSettings.readfp(f)

#Resources:
print "Loading graphic into memory..."
def LoadImage(FilePath,Alpha=True):
	ret = pygame.image.load(FilePath).convert()
	if Alpha: ret.set_colorkey(pygame.surfarray.pixels3d(ret)[0][-1])
	return ret
def LoadImageSheet(FilePath,Width,Height,Alpha=True):
	ret = []
	RawImage = pygame.image.load(FilePath).convert()
	RawWidth = RawImage.get_width()
	for i in range(int(RawWidth/Width)):
		ret.append(RawImage.subsurface((i*Width,0,Width,Height)).convert())
		if Alpha: ret[-1].set_colorkey(pygame.surfarray.pixels3d(ret[-1])[0][-1])
	return tuple(ret)
class Text():
	def __init__(self):
		self.Fonts = (pygame.font.Font("font.ttc",16),pygame.font.Font("font.ttc",12))
	def Create(self,Input,Color=(255,255,255)):
		return self.Fonts[0].render(Input, False, Color)
	def CreateS(self,Input,Color=(255,255,255)):
		return self.Fonts[1].render(Input, False, Color)
#--\
Characters = []
Backgrounds = []
Object = None
Text = Text()
LoginBoxResources =(LoadImage("GUI/LoginBox.bmp"),                           #0
					LoadImageSheet("GUI/LoginButton.bmp",84,30,False),       #1
					LoadImage("GUI/Logo.bmp"))								 #2
MainMenuImages = (LoadImageSheet("GUI/ServerListBox.bmp",256,24,False),      #0
				  LoadImageSheet("GUI/MainMenuButtons.bmp",126,38,False),    #1
				  LoadImage("GUI/LoadingScreen.bmp",False),                  #2
				  LoadImage("GUI/MenuScreen.bmp",False),                     #3
				  LoadImageSheet("GUI/MainMenuSideButtons.bmp",36,36,False), #4
				  LoadImageSheet("GUI/NaviThumbs.bmp",72,16,False),			 #5
				  LoadImageSheet("GUI/NaviThumbsGray.bmp",72,16,False),		 #6
				  LoadImage("GUI/NaviThumbsMarker.bmp"),					 #7
				  LoadImage("GUI/NaviCustBG.bmp"),							 #8
				  LoadImageSheet("GUI/NaviColorSwap.bmp",11,18))			 #9
GUIimages = (LoadImage("GUI/HUD.bmp",False),							     #0
			 LoadImage("GUI/MouseCursor.bmp"),								 #1
			 LoadImageSheet("GUI/PopupX.bmp",15,15),						 #2
			 LoadImage("GUI/TextPopup.bmp"),						 	     #3
			 LoadImageSheet("GUI/JackOut.bmp",85,30,False),					 #4
			 LoadImage("GUI/ItemInfoBox.bmp"),								 #5
			 LoadImageSheet("GUI/ItemInfoBoxTypes.bmp",70,23))				 #6
MessageImages = (LoadImage("GUI/Messages/MainConnectLost.bmp"),				 #0
			     LoadImage("GUI/Messages/LoginFail.bmp"),				     #1
				 LoadImage("GUI/Messages/ConnectionLost.bmp"),				 #2
				 LoadImage("GUI/Messages/CharacterSaved.bmp"),				 #3
				 LoadImage("GUI/Messages/OutdatedClient.bmp"))				 #4
#--/
DrawSurface(MainMenuImages[2],Window); UpdateWindow()
def LoadImages():#I use a def to minimize memory usage
	global Characters, Backgrounds, Object
	class Dummy: pass
	#Characters:
	Config = ConfigParser.ConfigParser()
	for i in open("Navis/Content.txt","r").read().split("-"):
		Config.readfp(open("Navis/"+i+"/Config.ini"))
		Char = Dummy()
		Char.Name = i
		Char.ImageSpeed = float(Config.getint("Config","ImageSpeed"))/30
		Char.Speed = Config.getint("Config","WalkingSpeed")
		Char.Size = (Config.getint("Config","Width"),Config.getint("Config","Height"))
		
		temp = LoadImage("Navis/"+i+"/Mask.bmp")
		Char.Mask = pygame.mask.from_surface(temp)
		Char.MaskPos = (Config.getint("Config","MaskX"),Config.getint("Config","MaskY"))
		Char.MaskSize = temp.get_size()
		
		Char.Styles = [Config.get("Colors","Col"+str(j)) for j in range(Config.getint("Colors","Num"))]
		
		Char.Sprites = []#[Color][Direction(0-7, or 8 for the mugshot)][Walking? 0 or 1][Animation image index]
		for j in Char.Styles:
			Char.Sprites.append([])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandN.bmp" ,Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandNE.bmp",Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandE.bmp" ,Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandSE.bmp",Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandS.bmp" ,Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandSW.bmp",Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandW.bmp" ,Char.Size[0],Char.Size[1])])
			Char.Sprites[-1].append([LoadImageSheet("Navis/"+i+"/"+j+"/StandNW.bmp",Char.Size[0],Char.Size[1])])
			Char.Sprites[-1][0].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkN.bmp" ,Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][1].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkNE.bmp",Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][2].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkE.bmp" ,Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][3].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkSE.bmp",Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][4].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkS.bmp" ,Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][5].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkSW.bmp",Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][6].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkW.bmp" ,Char.Size[0],Char.Size[1]))
			Char.Sprites[-1][7].append(LoadImageSheet("Navis/"+i+"/"+j+"/WalkNW.bmp",Char.Size[0],Char.Size[1]))
			Char.Sprites[-1].append(LoadImageSheet("Navis/"+i+"/"+j+"/Talk.bmp",40,48))
		Char.Sprites = tuple(Char.Sprites)
		
		Characters.append(Char)
	Characters = tuple(Characters)
	
	#Backgrounds:
	for i in ListFolderContent("Backgrounds"):
		Config.readfp(open("Backgrounds/"+i+"/Config.ini"))
		Background = Dummy()
		
		Background.Size = (Config.getint("Config","Width"),Config.getint("Config","Height"))
		Background.Sprite = LoadImageSheet("Backgrounds/"+i+"/Background.bmp",Background.Size[0],Background.Size[1],False)
		Background.Speed = float(Config.getint("Config","Speed"))/30
		
		Backgrounds.append(Background)
	Backgrounds = tuple(Backgrounds)
	
	#Objects:
	Object = Dummy(); Object.Inventory = Dummy()
	Object.CellM = pygame.mask.from_surface(LoadImage("Objects/mask.bmp"))#Mask for the ground
	Object.Ground = LoadImageSheet("Objects/ground.bmp",64,36)#The different colors on the ground
	Object.Tile = {}#Tiles to put above the ground
	Object.Object = {}#Objects to put above the tiles
	Object.Inventory.Icons = {}#A icon for each inventory BG
	Object.Inventory.BGs = {"1x1":LoadImageSheet("Objects/Inventory/1x1BG.bmp",16,16),#Colored background for the grid in the Inventory
							"2x1":LoadImageSheet("Objects/Inventory/2x1BG.bmp",32,16),
							"1x2":LoadImageSheet("Objects/Inventory/1x2BG.bmp",16,32),
							"2x2":LoadImageSheet("Objects/Inventory/2x2BG.bmp",32,32)}
	for i in ListFolderContent("Objects/Tile/*.bmp"):#Tiles
		Object.Tile[int(i.split(".")[0])] = LoadImage("Objects/Tile/"+i)
	with open("Objects/Objects/ID.txt","r") as File:#Objects
		for i in FixNewlines(File.read()).split("\n"):
			i = i.split(":")
			RawMask = LoadImage("Objects/Objects/"+i[1]+"/Mask.bmp")
			Mask = pygame.mask.from_surface(RawMask)
			Sprite = LoadImageSheet("Objects/Objects/"+i[1]+"/Main.bmp",RawMask.get_width(),RawMask.get_height())
			with open("Objects/Objects/"+i[1]+"/Info.txt") as f:
				File = FixNewlines(f.read()).split("\n")
				Center = map(int,File[0].split("x"))
				Description = File[1:]
			Object.Object[int(i[0])] = [Sprite,Mask,Center[:2],float(Center[2])/30,Description]#[Sprites,Mask,Center,AnimSpeed,Description]
	with open("Objects/Inventory/ID.txt") as File:#Inventory icons
		for i in FixNewlines(File.read()).split("\n"):
			if i[0] == ";": continue
			i = i.split("-")
			Object.Inventory.Icons[int(i[0])] = (i[3], LoadImage("Objects/Inventory/Icons/"+i[3]+".bmp"), (int(i[1]),int(i[2])), i[4])#(Name, Icon sprite, (ID, Type), BG size)
LoadImages(); del LoadImages

#GameObjects:
print "Defining objects types..."
class NaviObj():
	def __init__(self):
		self.Username = ""
		self.Character = 0#Index to the "Characters" variable
		self.Color = 0
		self.Position = [0,0]
		self.Direction = "S"
		self.Walking = 0
		self.Running = 0
		self.Active = True
		
		self.CellPos = [0,0,0,0]#[cX,cY,x,y]
		self.CalcCellPos()
		
		self.ReadKey = True
		self.DrawName = False
		self.DirToSprInd = {"N":0,"NE":1,"E":2,"SE":3,"S":4,"SW":5,"W":6,"NW":7}
		self.SpriteIndx = 0#Index in animation sequence
	def Step(self):
		global Characters, Mouse, Area
		
		#Check mousepos:
		if Clamp(Mouse.InGamePos[0],self.Position[0],self.Position[0]+Characters[self.Character].Size[0]) == Mouse.InGamePos[0] and Clamp(Mouse.InGamePos[1],self.Position[1],self.Position[1]+Characters[self.Character].Size[1]) == Mouse.InGamePos[1]:
			self.DrawName = True
		else:
			self.DrawName = False
			
		if self.ReadKey:
			#Get the pressed keys:
			Keys = pygame.key.get_pressed()
			
			#check the keys, then execute the needed tasks:
			Dir = ["",""]
			if Keys[pygame.K_w] in (1,2):#Up
				Dir[0] = "N"
				self.Walking = 1
			elif Keys[pygame.K_s] in (1,2):#Down
				Dir[0] = "S"
				self.Walking = 1
			if Keys[pygame.K_d] in (1,2):#Right
				Dir[1] = "E"
				self.Walking = 1
			elif Keys[pygame.K_a] in (1,2):#Left
				Dir[1] = "W"
				self.Walking = 1
			if Keys[pygame.K_SPACE] in (1,2):#Space
				self.Running = 1
			else:
				self.Running = 0
			if Dir <> ["",""]: self.Direction = "".join(Dir)
			
			#If no keys are pressed:
			if not (Keys[pygame.K_w] in (1,2) or Keys[pygame.K_s] in (1,2) or Keys[pygame.K_d] in (1,2) or Keys[pygame.K_a] in (1,2)):
				self.Walking = 0
		else:
			self.Running = 0
			self.Walking = 0
		
		#Animation step:
		self.SpriteIndx += (Characters[self.Character].ImageSpeed,Characters[self.Character].ImageSpeed*1.5)[self.Running]
		if self.SpriteIndx >= len(Characters[self.Character].Sprites[self.Color][self.DirToSprInd[self.Direction]][self.Walking]):
			self.SpriteIndx = 0
		
		#Move:
		if self.Walking:
			Area.NaviMove(self)
			if not self.CalcCellPos():
				print "New cell not found!"
	def Draw(self,Parent):
		global Characters, View
		Parent.blit(Characters[self.Character].Sprites[self.Color][self.DirToSprInd[self.Direction]][self.Walking][int(self.SpriteIndx)],
		(0-int(View.DrawPos[0])+int(self.Position[0]),0-int(View.DrawPos[1])+int(self.Position[1])))
		return self.DrawName
	def RenderName(self,Parent):
		global Text, Characters
		Size = Text.Fonts[1].size(self.Username)
		Shadow = Text.CreateS(self.Username,(80,80,80))
		
		x = 0-View.DrawPos[0] + self.Position[0] + Characters[self.Character].Size[0]/2 - Size[0]/2
		y = 0-View.DrawPos[1] + self.Position[1] + Characters[self.Character].Size[1]
		
		for i in ((2,1),(2,2),(1,2),(0,2),(0,1),(0,0),(1,0),(2,0)):
			Parent.blit(Shadow,(x+i[0],y+i[1]))
		Parent.blit(Text.CreateS(self.Username,(255,255,255)),(x+1,y+1))
	def CalcCellPos(self):
		global Object, Characters
		mX = (self.CellPos[0]-self.CellPos[1])*512+(self.CellPos[2]-self.CellPos[3])*32
		mY = (self.CellPos[0]+self.CellPos[1])*256+(self.CellPos[2]+self.CellPos[3])*16
		Pos = (int(self.Position[0]+Characters[self.Character].MaskPos[0]+Characters[self.Character].MaskSize[0]/2),int(self.Position[1]+Characters[self.Character].MaskPos[1]+Characters[self.Character].MaskSize[1]/2))
		
		#Check the last cell:
		if Clamp(Pos[0]-mX,0,63) == Pos[0]-mX and Clamp(Pos[1]-mY,0,32) == Pos[1]-mY:
			if Object.CellM.get_at((Pos[0]-mX,Pos[1]-mY)): return True
		
		#Check neighbors
		NewPos = self.CellPos[:]
		for x, y in ((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)):
			if Clamp(Pos[0]-(mX+(x-y)*32),0,63) == Pos[0]-(mX+(x-y)*32) and Clamp(Pos[1]-(mY+(x+y)*16),0,32) == Pos[1]-(mY+(x+y)*16):
				if Object.CellM.get_at((Pos[0]-(mX+(x-y)*32),Pos[1]-(mY+(x+y)*16))):
					NewPos[2] += x
					NewPos[3] += y
					if NewPos[2] < 0:
						NewPos[2] = 15
						NewPos[0] -= 1
					elif NewPos[2] > 15:
						NewPos[2] = 0
						NewPos[0] += 1
					if NewPos[3] < 0:
						NewPos[3] = 15
						NewPos[1] -= 1
					elif NewPos[3] > 15:
						NewPos[3] = 0
						NewPos[1] += 1
					self.CellPos = NewPos
					return True
		
		#Not found
		return False
	def SetCellPos(self,cX,cY,x,y):
		global Characters
		self.Position[0] = 32 + (cX-cY)*512+(x-y)*32 - Characters[self.Character].MaskPos[0] - Characters[self.Character].MaskSize[0]/2
		self.Position[1] = 19 + (cX+cY)*256+(x+y)*16 - Characters[self.Character].MaskPos[1] - Characters[self.Character].MaskSize[1]/2
		self.CellPos = [cX,cY,x,y]
class ExternalNaviObj():#Other players, can also be used by NPCs
	def __init__(self):
		self.Username = ""
		self.Character = 0#Index to the "Characters" variable
		self.Color = 0
		self.Position = [0,0]
		self.Direction = "S"
		self.Walking = 0
		self.Running = 0
		self.Active = True
		
		self.DrawName = False
		self.DirToSprInd = {"N":0,"NE":1,"E":2,"SE":3,"S":4,"SW":5,"W":6,"NW":7}
		self.SpriteIndx = 0#Index in animation sequence
	def Step(self):
		global Characters, Mouse
		
		#Check mousepos:
		if Clamp(Mouse.InGamePos[0],self.Position[0],self.Position[0]+Characters[self.Character].Size[0]) == Mouse.InGamePos[0] and Clamp(Mouse.InGamePos[1],self.Position[1],self.Position[1]+Characters[self.Character].Size[1]) == Mouse.InGamePos[1]:
			self.DrawName = True
		else:
			self.DrawName = False
		
		#Move:
		if self.Walking:
			Area.NaviMove(self)
		
		#Animation step:
		self.SpriteIndx += (Characters[self.Character].ImageSpeed,Characters[self.Character].ImageSpeed*1.5)[self.Running]
		if self.SpriteIndx >= len(Characters[self.Character].Sprites[self.Color][self.DirToSprInd[self.Direction]][self.Walking]):
			self.SpriteIndx = 0
	def Draw(self,Parent):
		global Characters, View
		Parent.blit(Characters[self.Character].Sprites[self.Color][self.DirToSprInd[self.Direction]][self.Walking][int(self.SpriteIndx)],
		(0-int(View.DrawPos[0])+int(self.Position[0]),0-int(View.DrawPos[1])+int(self.Position[1])))
		return self.DrawName
	def RenderName(self,Parent):
		global Text, Characters
		Size = Text.Fonts[1].size(self.Username)
		Shadow = Text.CreateS(self.Username,(80,80,80))
		
		x = 0-View.DrawPos[0] + self.Position[0] + Characters[self.Character].Size[0]/2 - Size[0]/2
		y = 0-View.DrawPos[1] + self.Position[1] + Characters[self.Character].Size[1]
		
		for i in ((2,1),(2,2),(1,2),(0,2),(0,1),(0,0),(1,0),(2,0)):
			Parent.blit(Shadow,(x+i[0],y+i[1]))
		Parent.blit(Text.CreateS(self.Username,(255,255,255)),(x+1,y+1))
class AreaObj():#Including background
	def __init__(self):
		global Backgrounds
		self.Chunks = {}#Map is stored here
		self.Spawn = (0,0,0,0)
		self.Online = False
		self.ObjectImgIdx = {}#Animation index for each object
		self.World = pygame.Mask((128,128))#Mask used to check for collisions
		self.Preview = [0,None,0,0,0,0]#[ID,Type,cX,cY,x,y]
		
		#Background:
		self.BG = Backgrounds[5]
		self.BGImageIndex = 0
		self.BGPos = [0,0]
	def Load(self,Data=None):#Data is for online use
		global Sound, LoopMode, Navis
		
		if self.Online:
			if Data[0] == "M":#Move player
				Data = map(int,Data[1:].split("x"))
				Navis[0].SetCellPos(Data[0],Data[1],Data[2],Data[3])
			elif Data[0] == "S":#Finnished
				print "Recieved all chunks from server. Start!"
				LoopMode = 2
				Sound.JackIn("PublicWeb")
			elif Data[0] == "T":#Single block change
				Data = Data[1:].split(" ")
				cX, cY, x, y = map(int,Data[0].split("x"))
				self.Chunks[cX][cY][x][y] = map(int,Data[1].split("-"))#[Ground,Sound,Object,Tile]
				if self.Chunks[cX][cY][x][y][2] and self.Chunks[cX][cY][x][y][2] not in self.ObjectImgIdx.keys(): self.ObjectImgIdx[self.Chunks[cX][cY][x][y][2]] = 0
			elif Data[0] == "C":#Recieve a Chunk
				Data = Data[1:].split(" ")
				
				cX, cY = map(int,Data[0].split("x"))
				if cX not in self.Chunks.keys():
					self.Chunks[cX] = {}
				self.Chunks[cX][cY] = []
				
				for x in range(16):
					yl = []
					for y in range(16):
						yl.append(map(int,Data[1+x+y*16].split("-")))#[Ground,Sound,Object,Tile]
						if yl[-1][2] and yl[-1][2] not in self.ObjectImgIdx.keys(): self.ObjectImgIdx[yl[-1][2]] = 0
					self.Chunks[cX][cY].append(yl)
				
				print "Got chunk",str(cX)+"x"+str(cY),"from server!"
		else:
			if os.path.exists("Save/Config.txt"):
				with open("Save/Config.txt","r") as Handle:
					File = Handle.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
					self.Spawn = map(int, File[0].split("x"))
					
					Navis[0].SetCellPos(self.Spawn[0],self.Spawn[1],self.Spawn[2],self.Spawn[3])
			else:
				self.Spawn = (0,0,0,0)
			for i in ListFolderContent("Save/*.chunk"):
				with open("Save/"+i,"r") as Handle:
					File = Handle.read()
				
				i = map(int,i.split(".")[0].split("x"))
				if i[0] not in self.Chunks.keys():
					self.Chunks[i[0]] = {}
				if i[1] not in self.Chunks[i[0]].keys():
					self.Chunks[i[0]][i[1]] = []
				
				for x in range(16):
					yl = []
					for y in range(16):
						Ground = ord(File[48*y+3*x]) >> 4
						Music = ord(File[48*y+3*x]) & 0x0F
						Object = ord(File[48*y+3*x+1])
						Tile = ord(File[48*y+3*x+2])
						
						if Object and Object not in self.ObjectImgIdx.keys(): self.ObjectImgIdx[Object] = 0
						yl.append([Ground,Music,Object,Tile])
					self.Chunks[i[0]][i[1]].append(yl)
	def Unload(self):
		global Navis, View
		
		if not self.Online and len(self.Chunks):#Save the world to save
			print "Saving world..."
			with open("Save/Config.txt","w") as File:
				File.write("x".join(map(str,self.Spawn))+"\n")#Spawn
			Range16 = range(16)
			for cX in self.Chunks:
				for cY in self.Chunks[cX]:
					with open("Save/"+str(cX)+"x"+str(cY)+".chunk","w") as File:
						write = []
						for y in Range16:
							for x in Range16:
								write.append(chr(self.Chunks[cX][cY][x][y][0]<<4|self.Chunks[cX][cY][x][y][1]))
								write.append(chr(self.Chunks[cX][cY][x][y][2]))
								write.append(chr(self.Chunks[cX][cY][x][y][3]))
						File.write("".join(write))
			print "Saved world succesfully!"
		
		for i in self.Chunks.keys():
			del self.Chunks[i]
		del self.Chunks
		del self.ObjectImgIdx
		
		self.Chunks = {}
		self.ObjectImgIdx = {}
		self.Preview = [0,None,0,0,0,0]
		Navis[0].Position = [0,0]
		Navis[0].Direction = "S"
		Navis[0].CellPos = [0,0,0,0]
		View.DrawPos = [0,0]
	#=====
	def NaviMove(self,Navi):
		global Characters, Object
		
		#Get player's mask pos
		PosX = int(Navi.Position[0])+Characters[Navi.Character].MaskPos[0]
		PosY = int(Navi.Position[1])+Characters[Navi.Character].MaskPos[1]
		
		#Create a 128x128 mask of the area around the player:
		self.World.fill()#Fill the mask
		Range16 = range(16)# <- faster
		for i in self.Chunks.keys():
			for j in self.Chunks[i].keys():
				cX = 0-(PosX-64)+(i-j)*512
				cY = 0-(PosY-64)+(i+j)*256
				if not (cX < -542 or cX > 640 or cY < -542 or cY > 640):
					for x in Range16:
						for y in Range16:
							dX, dY = cX+(x-y)*32, cY+(x+y)*16
							#Erase part of mask which is ground:
							if self.Chunks[i][j][x][y][0] <> 5:
								if not (dX <= -63 or dX >= 191 or dY <= -32 or dY >= 139):
									self.World.erase(Object.CellM,(dX, dY))
							#Add part of mask which is object:
							if self.Chunks[i][j][x][y][2]:
								dX -= Object.Object[self.Chunks[i][j][x][y][2]][2][0]
								dY -= Object.Object[self.Chunks[i][j][x][y][2]][2][1]
								mW, mH = Object.Object[self.Chunks[i][j][x][y][2]][1].get_size()
								if not (dX+32 <= -mW+1 or dX+32 >= 127+mW or dY+19 <= -mH+1 or dY+19 >= 127+mH):
									self.World.draw(Object.Object[self.Chunks[i][j][x][y][2]][1],(dX+32, dY+19))
		
		#Move the player within the mask's limits:
		Movement = [0,0]
		Float = ((Navi.Position[0]+Characters[Navi.Character].MaskPos[0])-PosX, (Navi.Position[1]+Characters[Navi.Character].MaskPos[1])-PosY)
		mX = 0
		mY = 0
		if Navi.Direction[0] == "N":
			mY = -1
		if Navi.Direction[0] == "S":
			mY = 1
		if Navi.Direction[-1] == "E":
			mX = 1
		if Navi.Direction[-1] == "W":
			mX = -1
		if mX:
			mY *= 0.5
		if Navi.Running:
			mX *= 1.5
			mY *= 1.5
		if self.World.overlap_area(Characters[Navi.Character].Mask, (64+int(mX*Characters[Navi.Character].Speed+Float[0]),64+int(mY*Characters[Navi.Character].Speed+Float[1]))):
			for i in xrange(Characters[Navi.Character].Speed):
				if self.World.overlap_area(Characters[Navi.Character].Mask, (64+int(Movement[0]+mX+Float[0]),64+int(Movement[1]+mY+Float[1]))):
					break
				Movement[0] += mX
				Movement[1] += mY
		else:
			Movement[0] = mX*Characters[Navi.Character].Speed
			Movement[1] = mY*Characters[Navi.Character].Speed
		Navi.Position[0] += Movement[0]
		Navi.Position[1] += Movement[1]
	def Step(self):
		global Object
		
		#Background:
		self.BGPos[0] += 1
		self.BGPos[1] += 1
		if self.BGPos[0] >= self.BG.Size[0]: self.BGPos[0] = 0
		if self.BGPos[1] >= self.BG.Size[1]: self.BGPos[1] = 0
		self.BGImageIndex += self.BG.Speed
		if self.BGImageIndex >= len(self.BG.Sprite):
			self.BGImageIndex = 0
		
		#Animation step for objects:
		for i in self.ObjectImgIdx.keys():
			self.ObjectImgIdx[i] += Object.Object[i][3]
			if int(self.ObjectImgIdx[i]) >= len(Object.Object[i][0]):
				self.ObjectImgIdx[i] -= len(Object.Object[i][0])
	#=====
	def Draw(self, Parent):
		global Backgrounds, View
		
		#Background:
		for y in range(10):
			for x in range(10):
				Parent.blit(self.BG.Sprite[int(self.BGImageIndex)],
				(self.BGPos[0] - self.BG.Size[0] + x*self.BG.Size[0],
				self.BGPos[1] - self.BG.Size[1] + y*self.BG.Size[1]))
		
		#Ground:
		Range16 = range(15,-1,-1)
		if self.Preview[1] == 0:
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in Range16:
							for y in Range16:
								if self.Preview[2:] == [i,j,x,y]:
									Parent.blit(Object.Ground[self.Preview[0]],(cX+(x-y)*32,cY+(x+y)*16))
								else:
									Parent.blit(Object.Ground[self.Chunks[i][j][x][y][0]],(cX+(x-y)*32,cY+(x+y)*16))
		else:
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in Range16:
							for y in Range16:
								Parent.blit(Object.Ground[self.Chunks[i][j][x][y][0]],(cX+(x-y)*32,cY+(x+y)*16))
		
		#Tiles: <- Need to make it only run if there are tiles on the chunk
		Range16 = range(16)
		if self.Preview[1] == 3:
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in Range16:
							for y in Range16:
								if self.Preview[2:] == [i,j,x,y]:
									if self.Preview[0]: Parent.blit(Object.Tile[self.Preview[0]],(cX+(x-y)*32,cY+(x+y)*16))
								elif self.Chunks[i][j][x][y][3]:
									Parent.blit(Object.Tile[self.Chunks[i][j][x][y][3]],(cX+(x-y)*32,cY+(x+y)*16))
		else:
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in Range16:
							for y in Range16:
								if self.Chunks[i][j][x][y][3]:
									Parent.blit(Object.Tile[self.Chunks[i][j][x][y][3]],(cX+(x-y)*32,cY+(x+y)*16))
	def ObjectPositions(self):
		ret = []
		if self.Preview[1] == 2:
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in range(15,-1,-1):
							for y in range(15,-1,-1):
								if self.Preview[0] and self.Preview[2:] == [i,j,x,y]:
									pos = (32+cX+(x-y)*32,17+cY+(x+y)*16)
									ret.append((pos,i,j,x,y))
								elif self.Chunks[i][j][x][y][2]:
									pos = (32+cX+(x-y)*32,17+cY+(x+y)*16)
									ret.append((pos,i,j,x,y))
		else:
			ret = []
			for i in self.Chunks:
				for j in self.Chunks[i]:
					cX = 0-int(View.DrawPos[0])+(i-j)*512
					cY = 0-int(View.DrawPos[1])+(i+j)*256
					if not (cX < -552 or cX > 942 or cY < -552 or cY > 890):
						for x in range(15,-1,-1):
							for y in range(15,-1,-1):
								if self.Chunks[i][j][x][y][2]:
									pos = (32+cX+(x-y)*32,17+cY+(x+y)*16)
									ret.append((pos,i,j,x,y))
		return ret
	def DrawObject(self, Parent, cX, cY, x, y):
		if self.Preview[1] == 2:
			if self.Preview[2:] == [cX,cY,x,y]:
				ID = self.Preview[0]
			else:
				ID = self.Chunks[cX][cY][x][y][2]
		else:
			ID = self.Chunks[cX][cY][x][y][2]
		if not ID: return
		
		dX = 0-int(View.DrawPos[0])+(cX-cY)*512+(x-y)*32+32 - Object.Object[ID][2][0]
		dY = 0-int(View.DrawPos[1])+(cX+cY)*256+(x+y)*16+17 - Object.Object[ID][2][1]
		Parent.blit(Object.Object[ID][0][int(self.ObjectImgIdx[ID])],(dX, dY))
	#=====
	def SetCell(self,cX,cY,x,y,type,ID):
		global SubConnection
		
		if cX not in self.Chunks:
			return False
		if cY not in self.Chunks[cX]:
			return False
		
		if self.Online and SubConnection:
			SubConnection.Send("\x06"+" ".join(map(str,(cX,cY,x,y,type,ID))))
		else:
			self.Chunks[cX][cY][x][y][type] = ID
		return True
class Sound():#BGM and SFX
	def __init__(self):
		self.Playing = []
		self.Sounds = {}
		for i in ListFolderContent("Music/*.wav"):
			self.Sounds[i[:-4]] = pygame.mixer.Sound("Music/"+i)
	def StopAll(self):
		for i in self.Playing:
			self.Sounds[i].stop()
		self.Playing = []
	def JackIn(self,Next=None,Fade = 1):
		global GameSettings
		if not GameSettings.getint("Settings","Sound"): return
		#Fade out the other songs
		for i in self.Playing:
			self.Sounds[i].fadeout(830)
		self.Playing = ["Jack in"]
		
		#set up AfterJackIn()
		self.Next = Next
		self.Fade = Fade
		reactor.callLater(0.83,self.AfterJackIn)
		
		#Play
		self.Sounds["Jack in"].play()
	def AfterJackIn(self):#Automatically called
		if not self.Next: return
		self.Sounds[self.Next].play((0,-1)[self.Fade],0,1519*self.Fade)
		self.Playing.append(self.Next)
	def SwapBGM(self,BGM):#With fade
		global GameSettings
		if not GameSettings.getint("Settings","Sound"): return
		for i in self.Playing:
			self.Sounds[i].fadeout(1500)
		self.Playing = [BGM]
		self.Sounds[BGM].play(-1,0,1500)
	def SetBGM(self,BGM,Loop = -1):#Without fade
		global GameSettings
		if not GameSettings.getint("Settings","Sound"): return
		self.StopAll()
		self.Playing.append(BGM)
		self.Sounds[BGM].play(Loop,0)
Navis = {0:NaviObj()}#To store your Navi and other player's Navis and NPCs(used for step and draw)
Area = AreaObj()
Sound = Sound()

#GUIObjects
class Mouse():
	def __init__(self):
		pygame.mouse.set_visible(False)
		
		self.Pos = (0,0)
		self.InGamePos = (0,0)
		
		self.Button = [0,0]#        [Left,Right]
		self.ButtonPressed = [0,0]# [Left,Right]
		self.ButtonReleased = [0,0]#[Left,Right]
		
		self.Focused = True
	def Step(self):
		global View
		self.Pos = pygame.mouse.get_pos()
		self.InGamePos = (View.DrawPos[0]+self.Pos[0],View.DrawPos[1]+self.Pos[1])
		self.Focused = pygame.mouse.get_focused()
		
		temp = list(pygame.mouse.get_pressed());del temp[1]
		self.ButtonPressed = [0,0]
		self.ButtonReleased = [0,0]
		if temp[0] and not self.Button[0]: self.ButtonPressed[0] = 1
		if temp[1] and not self.Button[1]: self.ButtonPressed[1] = 1
		if not temp[0] and self.Button[0]: self.ButtonReleased[0] = 1
		if not temp[1] and self.Button[1]: self.ButtonReleased[1] = 1
		self.Button = temp
	def Draw(self,Parent):
		global GUIimages
		if self.Focused: Parent.blit(GUIimages[1],self.Pos)
class Button():#Sub-Object (to be used by other classes)
	def __init__(self,Sprite,Sprite2,Pos=(0,0),Event=None):
		self.Sprite = (Sprite,Sprite2)#(unmarked,marked)
		self.Size = Sprite.get_size()
		self.Event = Event#A funtion to call when clicked at.
		self.Pos = Pos
		self.Marked = 0#0 false, 1 true, 2 true and clicked at
	def Draw(self,Parent):
		Parent.blit(self.Sprite[(0,1,1)[self.Marked]],self.Pos)
	def Step(self,NotUsed = None):#The NotUsed variable is just there to be able to put the Button class in the same list as TextInput and call Step()
		global Mouse
		self.Marked = 0
		
		if Clamp(Mouse.Pos[0],self.Pos[0],self.Pos[0]+self.Size[0]) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],self.Pos[1],self.Pos[1]+self.Size[1]) == Mouse.Pos[1]:
			self.Marked = 1
			if Mouse.ButtonPressed[0]:
				self.Marked = 2
				if self.Event: self.Event()
				return 1
		return 0
class TextInput():#Sub-Object (to be used by other classes)
	def __init__(self,Pos,Size,Limit = 1024,Color=(255,255,255)):
		self.Text = ""
		self.Pos = Pos
		self.Size = Size
		self.Active = False
		self.Limit = Limit
		self.Password = False
		self.Color = Color
		self.Marker = ["_",15]
		
		self.Events = {}
		self.SkipStep = False#Activate to skip the next step
	def Draw(self,Parent):
		Marker = ""
		if self.Active: Marker = self.Marker[0]
		if self.Password:
			Parent.blit(Text.Create("*"*len(self.Text)+Marker,self.Color), (self.Pos[0],self.Pos[1]+self.Size[1]/2-9))
		else:
			Parent.blit(Text.Create(self.Text+Marker,self.Color), (self.Pos[0],self.Pos[1]+self.Size[1]/2-9))
	def Step(self,Events):#Events shall be the output of pygame.event.get()
		global Mouse
		if not self.SkipStep:
			Mouse.ButtonPressed[0]
			if Mouse.ButtonPressed[0]:
				if Clamp(Mouse.Pos[0],self.Pos[0],self.Pos[0]+self.Size[0]) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],self.Pos[1],self.Pos[1]+self.Size[1]) == Mouse.Pos[1]:
					self.Active = True
					self.Marker = ["_",15]
				else:
					self.Active = False
			
			if self.Active:
				for Event in Events:
					if Event.type == KEYDOWN:
						if Event.unicode and (Event.unicode not in ("\r","\n","\b","\t")) and len(self.Text) < self.Limit:
							self.Text += Event.unicode
						elif Event.unicode == "\b":
							self.Text = self.Text[:-1]
						if Event.unicode in self.Events: self.Events[Event.unicode](self)
				
				self.Marker[1] -= 1
				if not self.Marker[1]:
					self.Marker[1] = 15
					if not self.Marker[0]:
						self.Marker[0] = "_"
					else:
						self.Marker[0] = ""
		else:
			self.SkipStep = False
	def Activate(self,Other=None):#Use when activating or in self.Event for buttons like tab and return/enter
		if Other:
			Other.Active = False
			Other.SkipStep = True
		self.Active = True
		self.Marker = ["_",15]
		self.SkipStep = True
class View():#The in-game camera
	def __init__(self):
		self.Mode = 0
		self.FollowNavi = 0#Index to the navi which the camera will follow(Used in mode 0)
		self.XYCenter = [0,0]#X and Y position which will be center of camera(Used in mode 1)
		
		self.DrawPos = [0,0]
		self.CameraSpeed = 10#Smaller = faster, 1 being the smallest
	def Update(self):#To be called between step and draw
		if self.Mode == 0:
			global Characters, Navis
			Goto = Navis[self.FollowNavi].Position[:]
			Goto[0] += Characters[Navis[self.FollowNavi].Character].Size[0]/2
			Goto[1] += Characters[Navis[self.FollowNavi].Character].Size[1]/2
			Goto[0] -= 210
			Goto[1] -= 184
			
			Goto = (Goto[0]-self.DrawPos[0],Goto[1]-self.DrawPos[1])
			self.DrawPos[0] += Goto[0]/self.CameraSpeed
			self.DrawPos[1] += Goto[1]/self.CameraSpeed
class HUD():#Handles all GUI-ish stuff happening in-game(chat, items, popups, etc...)
	class TextMessage():#Popup
		def __init__(self):
			self.Text = ""
			self.Pos = [266,10]
			self.Close = False
			
			self.Scroll = 0.0
			self.XButtonMarked = 0#1 and 0 instead of True and False
			self.Held = False
			self.HeldPos = [0,0]
		def Draw(self,Parent):
			global GUIimages, Text
			temp = pygame.Surface((113,65)).convert()
			temp.set_colorkey((0,0,0))
			Pos = int(0-(14*self.Scroll))
			for i in self.Text.split("\n"):
				temp.blit(Text.Create(i,(30,30,30)),(1,Pos+1))
				temp.blit(Text.Create(i),(0,Pos))
				Pos += 14
			
			Parent.blit(GUIimages[3],self.Pos)
			Parent.blit(temp,(self.Pos[0]+7,self.Pos[1]+7))
			Parent.blit(GUIimages[2][self.XButtonMarked],(self.Pos[0]+122,self.Pos[1]+32))
		def Step(self, AboveMarked):#Set the AboveMarked variable to True if a popup above this one has the mouse within itself, False if not.
			global Mouse
			ret = False
			
			#if mouse is within the textbox:
			if not AboveMarked and ((Clamp(Mouse.Pos[0],self.Pos[0],self.Pos[0]+128) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],self.Pos[1],self.Pos[1]+80) == Mouse.Pos[1]) or (Clamp(Mouse.Pos[0],self.Pos[0]+128,self.Pos[0]+144) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],self.Pos[1]+26,self.Pos[1]+54) == Mouse.Pos[1])):
				ret = True
				
				#If within the X button:
				if Clamp(Mouse.Pos[0],self.Pos[0]+122,self.Pos[0]+137) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],self.Pos[1]+32,self.Pos[1]+47) == Mouse.Pos[1]:
					self.XButtonMarked = True
					if Mouse.ButtonPressed[0]:
						self.Close = True
				else:#If not
					self.XButtonMarked = False
					if Mouse.ButtonPressed[0]:#Check if moved by mouse
						self.Held = True
						self.HeldPos[0] = Mouse.Pos[0]-self.Pos[0]
						self.HeldPos[1] = Mouse.Pos[1]-self.Pos[1]
					elif not self.Held:#Scroll
						if Mouse.Pos[1] < self.Pos[1]+30:
							self.Scroll = max((0,self.Scroll-(0.5-(float(Mouse.Pos[1]-self.Pos[1])/60))))
						elif Mouse.Pos[1] > self.Pos[1]+49:
							self.Scroll += float(Mouse.Pos[1]-self.Pos[1]-49)/62
							if self.Scroll > self.Text.count("\n")-3:
								self.Scroll = max((0,float(self.Text.count("\n")-3)))
			else:
				self.XButtonMarked = False
				
			#If mousebutton was released:
			if Mouse.ButtonReleased[0]:
				self.Held = False
				
			#Move with the mouse if held
			if self.Held:
				self.Pos[0] = Mouse.Pos[0]-self.HeldPos[0]
				self.Pos[1] = Mouse.Pos[1]-self.HeldPos[1]
			
			return ret
	def __init__(self):
		global GUIimages
		
		#Inventory and item placement:
		self.Inventory = [[[0,0] for i in xrange(17)] for i in xrange(11)]#[x][y] = [ID(0 = empty), marked(0 or 1)]
		self.ItemSizes = {"1x1":(0,0),"1x2":(0,16),"2x1":(16,0),"2x2":(16,16)}
		self.MarkedItem = None#(x,y) but None if a item isn't marked
		self.ItemInfo = False#[ItemID,x,y]
		
		#Chat:
		self.ChatSurface = pygame.Surface((526,85)).convert(); self.ChatSurface.set_colorkey((72,72,72))
		self.ChatInput = TextInput((27,458),(477,16),1024,(72,72,72))
		self.ChatInput.Events["\r"] = self.Send
		self.ChatInput.Events["\n"] = self.Send
		self.ChatLines = []
		self.ChatScroll = 0.0
		
		#Popups:
		self.Popups = []
		
		#Buttons:
		self.JackoutButton = Button(GUIimages[4][0],GUIimages[4][1],(544,370),self.JackoutBtn)
		
		#Add items to inventory(will be removed, since resources will be limited in the future):
		self.Inventory[1][0][0] = 5
		self.Inventory[2][0][0] = 7
		self.Inventory[3][0][0] = 6
		self.Inventory[4][0][0] = 8
		self.Inventory[5][0][0] = 11
		self.Inventory[6][0][0] = 10
		self.Inventory[7][0][0] = 13
		self.Inventory[8][0][0] = 12
		self.Inventory[9][0][0] = 9
		
		self.Inventory[0][ 2][0] = 25
		self.Inventory[2][ 2][0] = 24
		self.Inventory[0][ 4][0] = 37
		self.Inventory[2][ 4][0] = 36
		self.Inventory[1][ 6][0] = 21
		self.Inventory[2][ 6][0] = 20
		self.Inventory[0][ 6][0] = 26
		self.Inventory[0][ 7][0] = 27
		self.Inventory[0][ 8][0] = 28
		self.Inventory[2][ 8][0] = 32
		self.Inventory[2][ 9][0] = 33
		self.Inventory[0][10][0] = 29
		self.Inventory[2][10][0] = 34
		self.Inventory[2][11][0] = 35
		self.Inventory[0][12][0] = 30
		self.Inventory[2][12][0] = 22
		self.Inventory[0][14][0] = 31
		self.Inventory[2][14][0] = 23
		
		self.Inventory[7][2][0] = 60
		self.Inventory[9][2][0] = 61
		self.Inventory[7][3][0] = 62
		self.Inventory[9][3][0] = 63
		self.Inventory[7][4][0] = 64
		self.Inventory[9][4][0] = 65
		self.Inventory[7][5][0] = 67
		self.Inventory[9][5][0] = 66
		
		self.Inventory[7][15][0] = 1
		self.Inventory[7][16][0] = 2
		self.Inventory[9][15][0] = 3
	def Draw(self,Parent):
		global Object, GUIimages, Mouse, Area
		
		#Chat:
		self.ChatSurface.fill((72,72,72))
		y = int(68 + self.ChatScroll*16)
		for Line in self.ChatLines:
			x = 0
			for i in range(len(Line)/2):
				i *= 2
				temp = Text.Create(Line[i+1],Line[i])
				self.ChatSurface.blit(Text.Create(Line[i+1],(30,30,30)),(x+1,y+1))#Shadow
				self.ChatSurface.blit(temp,(x,y))
				x += temp.get_width()
			y -= temp.get_height()
		Parent.blit(self.ChatSurface,(4,371))
		self.ChatInput.Draw(Parent)
		
		#Inventory:
		for x in range(11):
			for y in range(17):
				if self.Inventory[x][y][0]:
					if self.MarkedItem == (x,y):
						Parent.blit(Object.Inventory.BGs[Object.Inventory.Icons[self.Inventory[x][y][0]][3]][2],(440+x*16,37+y*16))
					else:
						Parent.blit(Object.Inventory.BGs[Object.Inventory.Icons[self.Inventory[x][y][0]][3]][self.Inventory[x][y][1]],(440+x*16,37+y*16))
					Parent.blit(Object.Inventory.Icons[self.Inventory[x][y][0]][1],(440+x*16,37+y*16))
		
		#Buttons:
		self.JackoutButton.Draw(Parent)
		
		#Popups:
		for i in self.Popups: i.Draw(Parent)
		
		#Inventory item info:
		if self.ItemInfo:
			#BG:
			Parent.blit(GUIimages[5],(self.ItemInfo[1],self.ItemInfo[2]))
			
			#Name:
			y = Text.Fonts[0].size(Object.Inventory.Icons[self.ItemInfo[0]][0])[0]/2#Name width
			Parent.blit(Text.Create(Object.Inventory.Icons[self.ItemInfo[0]][0],(30,30,30)), (self.ItemInfo[1]+61-y,self.ItemInfo[2]+17))#Name shadow
			Parent.blit(Text.Create(Object.Inventory.Icons[self.ItemInfo[0]][0]),            (self.ItemInfo[1]+60-y,self.ItemInfo[2]+16))#Name text
			
			if not Object.Inventory.Icons[self.ItemInfo[0]][2][1]:#		Ground
				Parent.blit(GUIimages[6][0],(self.ItemInfo[1]+115,self.ItemInfo[2]+95))
				Parent.blit(Object.Ground[Object.Inventory.Icons[self.ItemInfo[0]][2][0]],(self.ItemInfo[1]+118,self.ItemInfo[2]+42))
				if Object.Inventory.Icons[self.ItemInfo[0]][2][0] <> 5:
					Description = ("A plate with","a color which","is needed to","walk around")
				else:
					Description = ("This will","remove any","ground cell","you want!")
			elif Object.Inventory.Icons[self.ItemInfo[0]][2][1] == 2:#	Object
				Parent.blit(GUIimages[6][1],(self.ItemInfo[1]+115,self.ItemInfo[2]+95))
				
				if Object.Inventory.Icons[self.ItemInfo[0]][2][0]:
					temp = Object.Object[Object.Inventory.Icons[self.ItemInfo[0]][2][0]][0][0].get_size()
					if Object.Inventory.Icons[self.ItemInfo[0]][2][0] not in Area.ObjectImgIdx: Area.ObjectImgIdx[Object.Inventory.Icons[self.ItemInfo[0]][2][0]] = 0
					Parent.blit(Object.Object[Object.Inventory.Icons[self.ItemInfo[0]][2][0]][0][int(Area.ObjectImgIdx[Object.Inventory.Icons[self.ItemInfo[0]][2][0]])], (self.ItemInfo[1]+150-temp[0]/2, self.ItemInfo[2]+56-temp[1]/2))
					Description = Object.Object[Object.Inventory.Icons[self.ItemInfo[0]][2][0]][4]
				else:
					Description = ("This will","remove any","kind of object","you want!")
			else:#														Tile
				Parent.blit(GUIimages[6][2],(self.ItemInfo[1]+115,self.ItemInfo[2]+95))
				if Object.Inventory.Icons[self.ItemInfo[0]][2][0]:
					Parent.blit(Object.Tile[Object.Inventory.Icons[self.ItemInfo[0]][2][0]],(self.ItemInfo[1]+118,self.ItemInfo[2]+42))
				
				if Object.Inventory.Icons[self.ItemInfo[0]][2][0]:
					Description = ("A texture.","Ground cell","beneath is","needed to","walk on it")
				else:
					Description = ("This will","remove any","kind of tile","you want!")
			
			#Draw description:
			y = 37
			for i in Description:
				Parent.blit(Text.Create(i,(30,30,30)),(self.ItemInfo[1]+9,self.ItemInfo[2]+y+1))
				Parent.blit(Text.Create(i),(self.ItemInfo[1]+8,self.ItemInfo[2]+y))
				y += 16
	def Step(self,Events):
		global Navis, Mouse, Object, Area, View
		
		#Popups:
		AboveMarked = False
		NewPopups = []
		for i in range(len(self.Popups)-1,-1,-1):
			if self.Popups[i].Step(AboveMarked): AboveMarked = True
			if not self.Popups[i].Close:
				NewPopups.append(self.Popups[i])
		NewPopups.reverse()
		self.Popups = NewPopups
		
		#Buttons:
		if AboveMarked:
			self.JackoutButton.Marked = False
		else:
			self.JackoutButton.Step()
		
		#Inventory:
		GotMarked = False
		self.ItemInfo = False
		for x in range(11):#Check each inventory box:
			for y in range(17):
				if self.Inventory[x][y][0]:#if slot has item in it:
					#If mouse is within the box:
					temp = self.ItemSizes[Object.Inventory.Icons[self.Inventory[x][y][0]][3]]
					if Clamp(Mouse.Pos[0],440+x*16,455+x*16+temp[0]) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],37+y*16,52+y*16+temp[1]) == Mouse.Pos[1] and not AboveMarked:
						self.Inventory[x][y][1] = 1
						self.ItemInfo = (self.Inventory[x][y][0],275+x*16+temp[0]/2,53+y*16+temp[1])
						if Mouse.ButtonPressed[0]:
							if self.MarkedItem == (x,y):
								self.MarkedItem = None
							else:
								self.MarkedItem = (x,y)
							GotMarked = True
					#if not:
					else:
						if self.Inventory[x][y][0]: self.Inventory[x][y][1] = 0
				elif Mouse.ButtonPressed[0] and not GotMarked:#if not:
					if Clamp(Mouse.Pos[0],440+x*16,455+x*16) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],37+y*16,52+y*16) == Mouse.Pos[1] and not AboveMarked:
						self.MarkedItem = None
		if Mouse.ButtonPressed[0] and not AboveMarked:#Check if you clicked outside the slots, but within the item "window"
			if Clamp(Mouse.Pos[0],420,640) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],0,330) == Mouse.Pos[1]:
				if not (Clamp(Mouse.Pos[0],440,616) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],37,309) == Mouse.Pos[1]):
					self.MarkedItem = None
		
		#Find in-game mouse position for placing objects:
		if self.MarkedItem and not AboveMarked and Mouse.Focused:
			if Clamp(Mouse.Pos[0],0,420) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],0,368) == Mouse.Pos[1]:
				Range16 = range(16)#Faster
				Found = False
				for i in Area.Chunks:
					for j in Area.Chunks[i]:
						cX = (i-j)*512
						cY = (i+j)*256
						if not (0-int(View.DrawPos[0])+cX < -552 or 0-int(View.DrawPos[0])+cX > 942 or 0-int(View.DrawPos[1])+cY < -552 or 0-int(View.DrawPos[1])+cY > 890):
							for x in Range16:
								for y in Range16:
									pos = (cX+(x-y)*32,cY+(x+y)*16)
									if Clamp(Mouse.InGamePos[0],pos[0],pos[0]+63) == Mouse.InGamePos[0] and Clamp(Mouse.InGamePos[1],pos[1]+2,pos[1]+32) == Mouse.InGamePos[1]:
										if Object.CellM.get_at((Mouse.InGamePos[0]-pos[0],Mouse.InGamePos[1]-pos[1])):
											Area.Preview[0] = Object.Inventory.Icons[self.Inventory[self.MarkedItem[0]][self.MarkedItem[1]][0]][2][0]
											Area.Preview[1] = Object.Inventory.Icons[self.Inventory[self.MarkedItem[0]][self.MarkedItem[1]][0]][2][1]
											Area.Preview[2] = i
											Area.Preview[3] = j
											Area.Preview[4] = x
											Area.Preview[5] = y
											if Mouse.ButtonPressed[0]:
												Area.SetCell(i,j,x,y,Area.Preview[1],Area.Preview[0])
											Found = True
											break
								if Found: break
							if Found: break
					if Found: break
				if not Found: Area.Preview[1] = None
			else:
				Area.Preview[1] = None
		else:
			Area.Preview[1] = None
		
		#Chat:
		for Event in Events:
			if Event.type == KEYDOWN:
				if Event.unicode in ("t","T","\r","\n") and not self.ChatInput.Active:
					self.ChatInput.Activate()
					AboveMarked = False
		if self.ChatInput.Active and Navis[0].ReadKey:
			Navis[0].ReadKey = False
		elif not self.ChatInput.Active and  not Navis[0].ReadKey:
			Navis[0].ReadKey = True
		self.ChatInput.Step(Events)
		if AboveMarked: self.ChatInput.Active = False
		self.ChatScroll -= self.ChatScroll/8
	#Chat functions:
	def Send(self,Textbox):#Sends the content of the given textbox in the chat
		global SubConnection
		
		Textbox.Active = False
		if Textbox.Text:
			if SubConnection:#Online
				#For ascii-signs with a value over 127:
				send = []
				for i in Textbox.Text:
					if ord(i) >= 128:
						send.append("\0")
						send.append(chr(ord(i)-128))
						continue
					send.append(i)
				SubConnection.Send("\x05"+"".join(send))
			else:#Offline
				self.Add("16777215\0"+Textbox.Text)
			Textbox.Text = ""
	def Add(self,Data):#Recieved a message in chat
		Data = Data.split("\0")
		Line = []
		for i in range(len(Data)/2):
			i *= 2
			Line.append((int(Data[i]) >> 16, int(Data[i]) >> 8 & 0xFF, int(Data[i])&0xFF))
			Line.append([])
			
			#For ascii-signs with a dec value over 127:
			WasOne = False
			for j in Data[i+1]:
				if j == "\1" and not WasOne:
					WasOne = True
					continue
				if WasOne:
					Line[-1].append(chr(ord(j)+128))
					WasOne = False
				else:
					Line[-1].append(j)
			Line[-1] = "".join(Line[-1])
		
		self.ChatLines.insert(0, tuple(Line))
		self.ChatScroll += 1
		if len(self.ChatLines) > 20: del self.ChatLines[-1]
	#Button functions:
	def JackoutBtn(self):
		global SubConnection, Area
		if Area.Online:
			SubConnection.Quitting = True
			SubConnection.transport.loseConnection()
		else:
			MainMenu.GotoMenu()
class MainMenu():#Everything on the main menu
	def __init__(self):
		global MainMenuImages
		self.MenuMode = 0#0 = Select server or offline, 2 = Options
		self.Connecting = False#True when connecting to a subserver.
		
		self.ConnectFail = False#If connecting to a server failed or was lost
		self.ListSurface = pygame.Surface((256,149)).convert(); self.ListSurface.set_colorkey((255,128,128))
		self.Scroll = 0.0
		self.Selected = 0
		self.JackInButton =  Button(MainMenuImages[1][3],MainMenuImages[1][2],(322,286),self.JackInBtn)
		self.NavicustButton =Button(MainMenuImages[1][1],MainMenuImages[1][0],(192,286),self.NavicustBtn)
		self.IPButton =      Button(MainMenuImages[4][3],MainMenuImages[4][2],(153,210),self.IPBtn)
		self.RefreshButton = Button(MainMenuImages[4][1],MainMenuImages[4][0],(451,210),self.RefreshBtn)
		self.LogoutButton =  Button(MainMenuImages[4][5],MainMenuImages[4][4],(601,210),self.LogoutBtn)
		
		#Option stuff here
		self.SelectedNavi = [0,None]#[Chosen, marked]
		self.NaviColor = 0
		self.NaviPreviewSurf = pygame.Surface((40,55)).convert(); self.NaviPreviewSurf.set_colorkey((0,0,0))
		self.NaviPreviewImgIdx = 0
		self.ShowSaved = 0
		self.SaveButton =       Button(MainMenuImages[1][7],MainMenuImages[1][6],(322,286),self.SaveBtn)
		self.ServersButton =    Button(MainMenuImages[1][5],MainMenuImages[1][4],(192,286),self.ServersBtn)
		self.ColorSwapButton = [Button(MainMenuImages[9][0],MainMenuImages[9][1],(246,209),self.ColorLeftBtn),
								Button(MainMenuImages[9][2],MainMenuImages[9][3],(337,209),self.ColorRightBtn)]
	def Step(self,Events):
		global Mouse, MainConnection, Characters
		
		if self.MenuMode == 0 and not self.Connecting:
			#Scroll:
			if Mouse.Focused:	
				if Mouse.Pos[1] < 132:
					self.Scroll -= float(132-Mouse.Pos[1])/132/2
				if Mouse.Pos[1] > 324:
					self.Scroll += float(Mouse.Pos[1]-324)/156/2
				if self.Scroll > len(MainConnection.Servers)-5:
					self.Scroll = float(len(MainConnection.Servers)-5)
				if self.Scroll < 0.0:
					self.Scroll = 0.0
			
			#Check if anything in the list was clicked:
			if Mouse.ButtonPressed[0]:
				if Clamp(Mouse.Pos[0],192,448) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],132,281) == Mouse.Pos[1]:
					Pos = 132-int(25*self.Scroll)
					for i in range(len(MainConnection.Servers)+1):
						if Clamp(Mouse.Pos[1],Pos,Pos+24) == Mouse.Pos[1]:
							self.Selected = i
							self.ConnectFail = False
						Pos += 25
			
			#Step the buttons:
			self.JackInButton.Step()
			self.NavicustButton.Step()
			#self.IPButton.Step()
			self.RefreshButton.Step()
			self.LogoutButton.Step()
		elif self.MenuMode == 1:
			#Check with each navi button:
			self.SelectedNavi[1] = None
			for i in range(len(Characters)):
				y = 136+18*i
				if Clamp(Mouse.Pos[0],374,446) == Mouse.Pos[0] and Clamp(Mouse.Pos[1],y, y+16) == Mouse.Pos[1]:
					self.SelectedNavi[1] = i#Mark it
					if Mouse.ButtonPressed[0]:#if mousebutton is pressed:
						self.SelectedNavi[0] = i#Select it
						self.NaviColor = 0
			
			#Animate navi preview image:
			self.NaviPreviewImgIdx += Characters[self.SelectedNavi[0]].ImageSpeed
			if int(self.NaviPreviewImgIdx) >= len(Characters[self.SelectedNavi[0]].Sprites[self.NaviColor][3][1]):
				self.NaviPreviewImgIdx = 0.0
			
			#"Navi was saved:"
			if self.ShowSaved:
				self.ShowSaved -= 1
			
			#Step buttons:
			self.LogoutButton.Step()
			self.SaveButton.Step()
			self.ServersButton.Step()
			self.ColorSwapButton[0].Step()
			self.ColorSwapButton[1].Step()
	def Draw(self,Parent):
		global MainMenuImages, MessageImages, Characters, Text
		
		if self.MenuMode == 0:
			#Draw serverlist:
			self.ListSurface.fill((255,128,128))
			Pos = 0-int(25*self.Scroll)
			Num = 0
			for i in [("Local area","None")]+map(lambda x: (x[3],str(x[2])),MainConnection.Servers):
				if Pos > -25 and Pos < 150:
					if self.Selected == Num:
						self.ListSurface.blit(MainMenuImages[0][0],(0,Pos))
					else:
						self.ListSurface.blit(MainMenuImages[0][1],(0,Pos))
					self.ListSurface.blit(Text.Create(i[0],(0,0,0)),(4,Pos+5))
					self.ListSurface.blit(Text.Create(i[1],(0,0,0)),(212,Pos+5))
				Num += 1
				Pos += 25
			Parent.blit(self.ListSurface,(192,132))
			
			#Draw the buttons:
			self.JackInButton.Draw(Parent)
			self.NavicustButton.Draw(Parent)
			#self.IPButton.Draw(Parent)
			self.RefreshButton.Draw(Parent)
			self.LogoutButton.Draw(Parent)
			
			#Draw error(if any):
			if self.ConnectFail: DrawSurface(MessageImages[2],Window,(195,337))
		elif self.MenuMode == 1:
			Char = Characters[self.SelectedNavi[0]]
			
			#Draw the selected navi's preview:
			Parent.blit(MainMenuImages[8],(195,136))#BG
			Parent.blit(Char.Sprites[self.NaviColor][8][0],(198,139))#Mugshot
			self.NaviPreviewSurf.fill((0,0,0))
			self.NaviPreviewSurf.blit(Char.Sprites[self.NaviColor][3][1][int(self.NaviPreviewImgIdx)],(21-Char.MaskSize[0]/2-Char.MaskPos[0],49-Char.MaskSize[1]/2-Char.MaskPos[1]))
			Parent.blit(self.NaviPreviewSurf,(198,189))#Draw navi preview
			Parent.blit(Text.Create(Char.Name,(44,44,44)),(241,140))#Draw text
			temp = Text.Create(Char.Styles[self.NaviColor],(44,44,44))
			Parent.blit(temp,(297-temp.get_width()/2,210))#Draw color
			
			#Draw "select navi" buttons:
			for i in range(len(Characters)):
				y = 136+18*i
				if i in self.SelectedNavi:
					Parent.blit(MainMenuImages[5][i],(374,y))
				else:
					Parent.blit(MainMenuImages[6][i],(374,y))
				
				if i == self.SelectedNavi[0]:
					Parent.blit(MainMenuImages[7],(352,y))
			
			#"Navi was saved":
			if self.ShowSaved:
				DrawSurface(MessageImages[3],Window,(195,337))
			
			#Draw buttons:
			self.LogoutButton.Draw(Parent)
			self.SaveButton.Draw(Parent)
			self.ServersButton.Draw(Parent)
			self.ColorSwapButton[0].Draw(Parent)
			self.ColorSwapButton[1].Draw(Parent)
	#======
	def JackInBtn(self):
		global Window, LoopMode, MainMenuImages, Sound
		
		if self.Selected == 0:#Offline
			DrawSurface(MainMenuImages[2],Window)
			UpdateWindow()
			
			LoopMode = 2
			Area.Online = False
			Area.Unload()
			Area.Load()
			Sound.JackIn("PublicWeb")#TEMP
		else:#online
			Area.Online = True
			Area.Unload()
			self.Connecting = True
			reactor.connectTCP(MainConnection.Servers[self.Selected-1][0], int(MainConnection.Servers[self.Selected-1][1]), SubFactory())
	def NavicustBtn(self):
		global Navis
		self.SelectedNavi[0] = Navis[0].Character
		self.NaviColor = Navis[0].Color
		
		self.MenuMode = 1
		self.NaviPreviewImgIdx = 0
	def IPBtn(self):#Invisible(WIP)
		print "IP button"
	def RefreshBtn(self):
		self.Scroll = 0.0
		self.Selected = 0
		MainConnection.Servers = []
		MainConnection.Send("\x02")
	def LogoutBtn(self):
		MainConnection.Send("\x05")
	def ServersBtn(self):
		self.MenuMode = 0
		self.ShowSaved = 0
	def SaveBtn(self):
		Navis[0].Character = self.SelectedNavi[0]
		Navis[0].Color = self.NaviColor
		MainConnection.Send("\x03"+str(self.SelectedNavi[0])+"\0"+str(self.NaviColor))
		self.ShowSaved = 75# 2 and a half second in 30 fps
	def ColorLeftBtn(self):
		global Characters
		self.NaviColor -= 1
		if self.NaviColor < 0:
			self.NaviColor = len(Characters[self.SelectedNavi[0]].Styles)-1
	def ColorRightBtn(self):
		global Characters
		self.NaviColor += 1
		if self.NaviColor >= len(Characters[self.SelectedNavi[0]].Styles):
			self.NaviColor = 0
	#======
	def GotoMenu(self):#Called after logging in, when the connection to a subserver is lost or when you jack out
		global LoopMode, Sound, MainConnection, Area, Navis
		Area.Unload()
		HUD.Popups = []
		HUD.ChatLines = []
		HUD.ChatScroll = 0.0
		HUD.MarkedItem = None
		LoopMode = 1
		self.MenuMode = 0
		self.Connecting = False
		self.ConnectFail = False
		self.Scroll = 0.0
		self.Selected = 0
		MainConnection.Servers = []
		MainConnection.Send("\x02")
		Sound.SetBGM("MainMenu")
Mouse = Mouse()
View = View()
HUD = HUD()
MainMenu = MainMenu()

#Networking
print "Defining Networking protocols..."
class MainProtocol(Protocol):
	def __init__(self):
		self.CallIf = {}#put an function here, and it will be called when input from server starts with the dictionary index.
		self.Buffer = ""
		self.State = 0#0 = connecting, 1 = connected, 2 = Connetion lost, 3 = Connetion failed
		self.Mode = 0#0 = Not logged in, 1 = Logging in, 2 = Logged in
		self.LoginFailed = False
		self.Servers = []#Add public servers here.
		self.Outdated = False#True if the client is outdated
		self.Ping = False
	def connectionMade(self):
		global Version
		print 'Connected to main server!'
		self.State = 1
		self.Send("\4"+Version)
		reactor.callLater(60, self.Step)
	def connectionLost(self, reason):
		print "Lost connection to main server!!"
		self.State = 2
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			for i in self.Buffer.split("\x7F")[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer.split("\x7F")[-1]
	#====
	def ParseData(self,Data):
		if Data[0] in self.CallIf:
			self.CallIf[Data[0]](Data[1:])
		if -1 in self.CallIf:
			self.CallIf[-1](Data[1:])
		
		if Data == "Ping":
			self.Send("Pong")
			self.Ping = True
			return
		
		if Data[0] == "\1":#get login result
			self.GetLogin(Data[1:])
		elif Data[0] == "\2":#Get a public server
			Data = Data[1:].split(" ")
			self.Servers.append((Data[0],Data[1],Data[2]," ".join(Data[3:])))#(IP, Port, OnlineCount, Name)
		elif Data[0] == "\4":#Client is outdated
			self.Outdated = True
		elif Data[0] == "\5":#You've been logged out
			self.Logout()
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):
		if self.State in (2,3): return
		if not self.Ping:
			print "Main server has stopped pinging, dissconnect."
			self.transport.loseConnection()
			return
		self.Ping = False
		reactor.callLater(60, self.Step)
	#====
	def Login(self, TextEvent=None):
		if TextEvent:
			TextEvent.Active = False
			TextEvent.SkipStep = True
		
		if not (LoginData[1].Text or LoginData[2].Text): return
		print "Sending login request..."
		global LoginData
		self.Send("\x01" + LoginData[1].Text + "\0" + LoginData[2].Text)
		self.Mode = 1
		self.LoginFailed = False
	def GetLogin(self,Data):#WIP
		if Data[0] == "Y":# <- WIP
			global Navis, MainMenu
			Data = Data[1:].split(" ")#[HP, Zennies, Bugfrags, CharIdx, CharColor, ItemCount, Item*]
			
			Navis[0].Username = LoginData[1].Text
			Navis[0].Character = int(Data[3])
			Navis[0].Color = int(Data[4])
			
			self.Mode = 2
			MainMenu.GotoMenu()
		if Data[0] == "N":
			global LoginData
			self.Mode = 0
			LoginData[1].Active = True
			LoginData[2].Text = ""
			LoginData[2].Active = False
			self.LoginFailed = True
	def Logout(self):
		global LoginData, LoopMode
		self.Mode = 0
		self.LoginFailed = False
		LoopMode = 0
		
		Sound.SetBGM("LoginScreen",0)
		LoginData[1].Active = True
		LoginData[2].Text = ""
		LoginData[2].Active = False
MainConnection = MainProtocol()
class MainFactory(ClientFactory):
	def startedConnecting(self, connector):
		print 'Started connecting to the main server...'
	def buildProtocol(self, addr):
		global MainConnection
		return MainConnection
	def clientConnectionFailed(self, connector, reason):
		print 'Could not connect to the main server!'
		global MainConnection
		MainConnection.State = 3
class SubProtocol(Protocol):
	def __init__(self):
		self.CallIf = {}#put an function here, and it will be called when input from server starts with the dictionary index.
		self.Buffer = ""
		self.ContinueStep = True
		self.Quitting = False#To see if connection was lost or stopped
		
		self.OldPosition = None#Used to only send your position if it has changed
	def connectionMade(self):
		print 'Successfully connected to the sub server!'
		global SendFrequency, Navis
		reactor.callLater(SendFrequency, self.Step)
		self.Send("\x01"+"\0".join((Navis[0].Username,str(Navis[0].Character),str(Navis[0].Color))))
	def connectionLost(self, reason):
		global Navis, SubConnection
		print "Lost connection to sub server!"
		self.ContinueStep = True
		SubConnection = None
		for i in Navis.keys():
			if i: del Navis[i]
		MainMenu.GotoMenu()
		if not self.Quitting: MainMenu.ConnectFail = True
		self.Quitting = False
	def dataReceived(self, Data):
		self.Buffer += Data
		if "\x7F" in self.Buffer:
			for i in self.Buffer.split("\x7F")[:-1]:
				self.ParseData(i)
			self.Buffer = self.Buffer.split("\x7F")[-1]
	#====
	def ParseData(self,Data):
		global HUD
		
		if Data[0] in self.CallIf:
			self.CallIf[Data[0]](Data[1:])
		if -1 in self.CallIf:
			self.CallIf[-1](Data[1:])
		
		if Data[0] == "\x01":#Recieve a map change(The whole world is sent through this at login)
			Area.Load(Data[1:])
		elif Data[0] == "\x02":#Get Players movement
			self.ParseMovement(Data[1:])
		elif Data[0] == "\x03":#Get a Player's data
			self.GetPlayer(Data[1:])
		elif Data[0] == "\x04":#Someone logged off
			del Navis[int(Data[1:])]
		elif Data[0] == "\x05":#Recieve a line in the chat
			HUD.Add(Data[1:])
		elif Data[0] == "\x06":#Recieve a popup
			if Data[1] == "\x01":#Text popup
				Popup = HUD.TextMessage()
				Popup.Text = Data[2:]
				HUD.Popups.append(Popup)
	def Send(self,Data):
		self.transport.write(str(Data+"\x7F"))
	def Step(self):
		global SendFrequency, Navis
		if self.ContinueStep <> 0: reactor.callLater(SendFrequency, self.Step)
		
		#Send position:
		temp = (Navis[0].Direction,
				str(int(Navis[0].Position[0])),
				str(int(Navis[0].Position[1])),
				str(Navis[0].Walking),
				str(Navis[0].Running),
				str(Navis[0].CellPos[0]),
				str(Navis[0].CellPos[1]),
				str(Navis[0].CellPos[2]),
				str(Navis[0].CellPos[3]))
		if self.OldPosition <> temp:
			self.Send("\x02"+" ".join(temp))
			self.OldPosition = temp
	#====
	def ParseMovement(self,Data):
		global Navis
		for i in Data.split(" "):
			i = i.split(".")
			if int(i[0]) in Navis:
				Navis[int(i[0])].Direction = i[1]
				Navis[int(i[0])].Position = [int(i[2]),int(i[3])]
				Navis[int(i[0])].Walking = int(i[4])
				Navis[int(i[0])].Running = int(i[5])
			else:#Don't know the ID, ask the server to send info:
				self.Send("\3"+i[0])
	def GetPlayer(self,Data):
		Data = Data.split("\0")
		Navis[int(Data[0])] = ExternalNaviObj()
		Navis[int(Data[0])].Username = Data[1]
		Navis[int(Data[0])].Character = int(Data[2])
		Navis[int(Data[0])].Color = int(Data[3])
SubConnection = None
class SubFactory(ClientFactory):
	def startedConnecting(self, connector):
		print 'Started connecting to a sub server...'
	def buildProtocol(self, addr):
		global SubConnection
		SubConnection = SubProtocol()
		return SubConnection
	def clientConnectionFailed(self, connector, reason):
		print 'Could not connect to the sub server!'
		global SubConnection, MainMenu
		MainMenu.Connecting = False
		MainMenu.ConnectFail = True

#Loops
print "Defining game loops..."
#	Mode list:
#		0 = Login screen
#		1 = Menu screen
#		2 = Game
LoopMode = 0
Sound.SetBGM("LoginScreen",0)
#Stores the GUIobjects for the login screen:
LoginData = [Button(LoginBoxResources[1][0],LoginBoxResources[1][1],(224+96,179+83),MainConnection.Login),
			 TextInput((237,219),(165,16),15),
			 TextInput((237,245),(165,16),15)]
LoginData[1].Events["\n"] = LoginData[2].Activate
LoginData[1].Events["\r"] = LoginData[2].Activate
LoginData[1].Events["\t"] = LoginData[2].Activate
LoginData[2].Password = True
LoginData[2].Events["\n"] = MainConnection.Login
LoginData[2].Events["\r"] = MainConnection.Login
LoginData[2].Events["\t"] = LoginData[1].Activate

def MainLoop():#Keeps the FPS and calls the needed sub-loop controlled by LoopMode
	global LoopMode, MainConnection, Timer
	
	#Framerate
	reactor.callLater(1.0/(31.5),MainLoop)
	Timer.tick(30)
	
	#update userinput:
	pygame.event.pump()
	Mouse.Step()
	Events = pygame.event.get()
	
	#Run the loop:
	if MainConnection.State in (2,3):#No connection to main server:
		#read input:
		for i in Events:
			if i.type == QUIT:
				QUITGame()
		DrawSurface(MainMenuImages[2],Window)
		DrawSurface(MessageImages[0],Window,(195,208))
		DrawSurface(Text.Create(Version,( 30, 30, 30)),Window,(31,15))
		DrawSurface(Text.Create(Version,(255,255,255)),Window,(30,14))
	else:#Connected to main server:
		(LoginLoop,MenuLoop,GameLoop)[LoopMode](Events)
	
	#Draw mouse on window and refresh it:
	Mouse.Draw(Window)
	UpdateWindow()
def LoginLoop(Events):
	#read input:
	for i in Events:
		if i.type == QUIT:
			QUITGame()
	
	if MainConnection.State == 1 and MainConnection.Mode == 0 and not MainConnection.Outdated:#Connected to server
		#Step objects:
		for i in LoginData: i.Step(Events)
		
		#Draw Screen:
		DrawSurface(MainMenuImages[2],Window)
		DrawSurface(LoginBoxResources[0],Window,(224,179))
		DrawSurface(LoginBoxResources[2],Window,(110,43))
		for i in LoginData: i.Draw(Window)
		if MainConnection.LoginFailed: DrawSurface(MessageImages[1],Window,(80,396))
	elif MainConnection.State == 0 or MainConnection.Mode == 1:#Connecting/loggin in...
		DrawSurface(MainMenuImages[2],Window)
	elif MainConnection.Outdated:#If login failed cause of outdated client
		DrawSurface(MainMenuImages[2],Window)
		DrawSurface(MessageImages[4],Window,(185,208))
	DrawSurface(Text.Create(Version,( 30, 30, 30)),Window,(31,15))
	DrawSurface(Text.Create(Version,(255,255,255)),Window,(30,14))
def MenuLoop(Events):
	#read input:
	for i in Events:
		if i.type == QUIT:
			#Keyboard buttons:
			QUITGame()
	
	#Step:
	MainMenu.Step(Events)
	
	#Draw:
	if MainMenu.Connecting:
		DrawSurface(MainMenuImages[2],Window)
	else:
		DrawSurface(MainMenuImages[3],Window)
		MainMenu.Draw(Window)
	DrawSurface(Text.Create(Version,( 30, 30, 30)),Window,(31,15))
	DrawSurface(Text.Create(Version,(255,255,255)),Window,(30,14))
def GameLoop(Events):
	#Step objects:
	Area.Step()
	for i in Navis.values(): i.Step()
	
	#Update View:
	View.Update()
	HUD.Step(Events)
	
	#Draw Game:
	Area.Draw(GameSurface)
	Draw = {}
	Vx, Vy = 0-int(View.DrawPos[0]), 0-int(View.DrawPos[1])
	for i in Navis.values():#Navis
		x, y = Vx+i.Position[0]+Characters[i.Character].Size[0]/2, Vy+i.Position[1]+Characters[i.Character].MaskPos[1]+Characters[i.Character].MaskSize[1]/2
		if x > -32 and x < 452 and y > -32 and y < 400:
			if y not in Draw:
				Draw[y] = []
			Draw[y].append(i)
	for i in Area.ObjectPositions():#Objects
		if i[0][0] > -64 and i[0][0] < 484 and i[0][1] > -64 and i[0][1] < 432:
			if i[0][1] not in Draw:
				Draw[i[0][1]] = []
			Draw[i[0][1]].append(i)
	Names = []; Depths = Draw.keys(); Depths.sort()
	for y in Depths:
		for i in Draw[y]:
			try:#Object
				Area.DrawObject(GameSurface, i[1], i[2], i[3], i[4])
			except:#Navi
				if i.Draw(GameSurface): Names.append(i.RenderName)
	for i in Names: i(GameSurface)
	
	#Draw GUI and game to window:
	DrawSurface(GUIimages[0],Window)
	DrawSurface(GameSurface,Window)
	#DrawSurface(Text.Create(str(Navis[0].CellPos)),Window)
	HUD.Draw(Window)
	
	#read input:
	for i in Events:
		#Keyboard buttons:
		if i.type == QUIT:
			QUITGame()

#Gamestart!
print "Start game!"
MainLoop()
reactor.connectTCP(Host, Port, MainFactory())
reactor.run()#Runs until the game is stopped

#Shut down game:
Area.Unload()
with open(RootPath+"/Settings.ini","w") as f:
	GameSettings.write(f)
pygame.quit()
