import viz
import vizconnect
import vizshape

viz.setMultiSample(4)
vizconnect.go('vizconnect_config_desktop.py')

viz.clip(0.01,1000)

# Add a background environment
dojo = viz.addChild('dojo.osgb')

#Add shapes
pyramid = vizshape.addPyramid(base=(0.2,0.2),height=0.2,pos=[-0.5,1.7,1],alpha=0.7)
torus = vizshape.addTorus(radius=0.1,tubeRadius=0.015,axis=vizshape.AXIS_X, pos=[0,1.7,1])
box = vizshape.addCube(size=0.1, pos=[0.5,1.7,1],alpha=0.8)
pyramid.texture(viz.addTexture('images/tile_slate.jpg'))
torus.texture(viz.addTexture('images/tile_wood.jpg'))

#Animate shapes
pyramid.addAction(vizact.spin(0,-1,0,15))
torus.addAction(vizact.spin(0,1,0,15))
box.addAction(vizact.spin(1,1,1,15))

shapes = [pyramid,torus,box]

# Code to get the grabber tool by name and supply the list of items which can be grabbed 
grabber = vizconnect.getRawTool('grabber')
grabber.setItems(shapes)