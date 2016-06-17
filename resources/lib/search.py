
from common import printDebug, GLOBAL_SETUP
import xbmc
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
class PopupWindow(xbmcgui.WindowDialog):
    term = ''
    isCancelled = False
    
    def __init__(self):
        totalwidth = 1920 #self.getWidth()
        totalheight = 1080 #self.getHeight()
        self.setCoordinateResolution(0)
        backwidth = totalwidth - 800
        backheight = totalheight - 800
        
        iconurl = addon.getAddonInfo("path") + '/resources/media/search.png'
        backdropurl = addon.getAddonInfo("path") + '/resources/media/searchback.jpg'
        self.addControl(xbmcgui.ControlImage(x=400, y=300, width=backwidth, height=backheight, filename=backdropurl))  
        self.addControl(xbmcgui.ControlImage(x=420, y=330, width=100, height=100, filename=iconurl))
        self.addControl(xbmcgui.ControlLabel(x=600, y=(totalheight/2)-150, width=backwidth-400, height=25, label='Search for media:'))
        self.edit = xbmcgui.ControlEdit (600, totalheight/2, 300, 25, 'Enter search term...')
        self.edit.setPosition(600, (totalheight/2) - 100)
        self.edit.setWidth(backwidth-400)
        self.edit.setHeight(40)
        self.addControl(self.edit)
        setupButtons(self,600,(totalheight/2),200,30,"Hori")
        self.btn_search = addButon(self,"Search", 0)
        self.btn_cancel = addButon(self,"Cancel", 50)
        
        self.edit.controlDown(self.btn_search)
        self.btn_search.controlRight(self.btn_cancel)
        self.btn_cancel.controlLeft(self.btn_search)
        self.btn_search.controlUp(self.edit)
        self.btn_cancel.controlUp(self.edit)
        self.setFocus(self.edit)
        
    def onControl(self, c):
        if self.btn_search == c:
            self.term = self.edit.getText()
            self.close()
        if self.btn_cancel == c:
            self.isCancelled = True
            self.close()
                
### The adding button Code (only really need this bit)
def setupButtons(self,x,y,w,h,a="Vert",f=None,nf=None):
    self.numbut  = 0
    self.butx = x
    self.buty = y
    self.butwidth = w
    self.butheight = h
    self.butalign = a
    self.butfocus_img = f
    self.butnofocus_img = nf
 
def addButon(self,text, offset):
    if self.butalign == "Hori":
        c =  xbmcgui.ControlButton(self.butx + (self.numbut * self.butwidth) + offset,self.buty,self.butwidth,self.butheight,text)
        self.addControl(c)
    elif self.butalign == "Vert":
        c = xbmcgui.ControlButton(self.butx ,self.buty + (self.numbut * self.butheight),self.butwidth,self.butheight,text)
        self.addControl(c)
    self.numbut += 1
    return c    