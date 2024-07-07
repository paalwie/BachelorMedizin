"""  
Mouse movements move the arrow left,right,up,down.  
Scroll wheel moves the arrow forward,back.  
Left mouse button grabs,releases.  
""" 

import viz
import vizshape
import vizact
import vizinfo
vizinfo.InfoPanel(align=viz.ALIGN_LEFT_BOTTOM)

viz.setOption('viz.display.stencil',1)

viz.setMultiSample(4)
viz.fov(60)
viz.go()

environment = viz.addChild('sky_day.osgb')
soccerball = viz.addChild('soccerball.osgb',pos=[-0.5,1.8,1.5])
basketball = viz.addChild('basketball.osgb',pos=[0,1.8,1.5])
volleyball = viz.addChild('volleyball.osgb',pos=[0.5,1.8,1.5])

#Initialize the Grabber and items that can be grabbed
#Change hightlight mode from default outline to box
usingPhysics=False
from tools import grabber
from tools import highlighter
tool = grabber.Grabber(usingPhysics=usingPhysics, usingSprings=usingPhysics, highlightMode=highlighter.MODE_BOX)
tool.setItems([soccerball,basketball,volleyball])

# update code for grabber
def updateGrabber(tool):
    state = viz.mouse.getState()
    if state & viz.MOUSEBUTTON_LEFT:
        tool.grabAndHold()
tool.setUpdateFunction(updateGrabber)

#Link the grabber to an arrow in order to
#visualize it's position
from vizconnect.util import virtual_trackers
mouseTracker = virtual_trackers.ScrollWheel(followMouse = True)
mouseTracker.distance = 1.4
arrow = vizshape.addArrow(length=0.2,color=viz.BLUE)
arrowLink = viz.link(mouseTracker,arrow)
arrowLink.postMultLinkable(viz.MainView)
viz.link(arrowLink,tool)

spin = vizact.spin(0,1,0,30,2)

#Add a spin action to the ball when its released
def onRelease(e):
    e.released.runAction(spin)
    
viz.callback(grabber.RELEASE_EVENT,onRelease)

#Disable mouse navigation and hide the mouse curser
viz.mouse(viz.OFF)
viz.mouse.setVisible(viz.OFF)