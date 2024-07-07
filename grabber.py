"""Tool for grabbing objects in the scene. AbstractGrabber provides a base
class which allows for any given combination of collision tester, attachment, 
placer, and highlighter"""

import viz
#import vizact
import vizshape

import tools
import tools.attacher
import tools.collision_test
import tools.highlighter
import tools.placer


GRAB_EVENT = viz.getEventID('GRABBER_GRAB_EVENT')
RELEASE_EVENT = viz.getEventID('GRABBER_RELEASE_EVENT')
UPDATE_INTERSECTION_EVENT = viz.getEventID('GRABBER_UPDATE_INTERSECTION_EVENT')


class AbstractGrabber(tools.Tool):
	"""An abstract grabber class which can have any given combination of:
	collision tester, attachment, placer, and highlighter.
	
	Supported flags: VIZ_TOOL_PLACER
	"""
	LOCK_TOGGLE = 1
	LOCK_HOLD = 2
	LOCK_HOVER = 4
	
	def __init__(self,
					node,
					collisionTester,
					attacher,
					placer,
					highlighter,
					preLoadHighlights=True,
					testIntersection=True,
					useToolTag=True,
					debug=False,
					**kwargs):
		
		self._collisionTester = collisionTester
		self._attacher = attacher
		self._placer = placer
		self._highlighter = highlighter
		
		self._useToolTag = useToolTag
		self._preLoadHighlights = preLoadHighlights
		self._testIntersection = testIntersection
		
		self._currentPlacer = placer
		self._currentAttacher = attacher
		self._currentHighlighter = highlighter
		
		super(AbstractGrabber, self).__init__(node=node, **kwargs)
		
		self._itemCollisionTesterSet = set()
		self._itemCollisionTesterList = {}
		self._currentIntersection = None
		self._currentHighlightedNode = None
		self._held = None
	
	def addItems(self, items, *args, **kwargs):
		"""Adds items to the existing list of items"""
		items = [i for i in items if i not in self._items]
		self.setItems(items+self._items, *args, **kwargs)
	
	def finalize(self):
		"""Finzlizes the grabbing"""
		super(AbstractGrabber, self).finalize()
		# if we're testing for intersections in general, and we're not currently
		# grabbing something, test for intersections now
		grabbedObj = self._attacher.getDst()
		if self._testIntersection and grabbedObj is None:
			self.getIntersection()
		
		# release if we're holding an object and not requesting to continue holding
		if self._held is not None and not self._frameLocked&self.LOCK_HOLD:
			self.release()
			self._held = None
		
		if grabbedObj is not None:
			self._currentPlacer.preview(grabbedObj)
	
	def getIntersection(self):
		"""Returns the nearest intersecting item.
		
		@return object
		"""
		# get the intersection
		if self._useToolTag:
			intersection, dist = self._collisionTester.get(tag=tools.TAG_GRAB)
		else:
			intersection, dist = self._collisionTester.get()
		for ct in self._itemCollisionTesterList.values():
			if self._useToolTag:
				cti, ctd = ct.get(tag=tools.TAG_GRAB)
			else:
				cti, ctd = ct.get()
			if dist < 0 or ctd < dist and ctd > 0:
				intersection = cti
				dist = ctd
		
		# if the intersection is different, update the current intersection
		if intersection != self._currentIntersection:
			self._updateHighlight(intersection)
			# send out an event
			viz.sendEvent(UPDATE_INTERSECTION_EVENT, viz.Event(grabber=self, new=intersection, old=self._currentIntersection))
			# save the new intersection
			self._currentIntersection = intersection
		
		return intersection
	
	def grab(self):
		"""Starts a grab"""
		# check if we're attached to anything
		if self._currentAttacher.getDst() is None:
			# perform an intersection test and get the result
			# the highlight should be updated by the get intersection call
			intersection = self.getIntersection()
			if intersection is not None:
				if hasattr(intersection, 'VIZ_TOOL_ATTACHER_FUNC'):
					self._currentAttacher = intersection.VIZ_TOOL_ATTACHER_FUNC(src=self)
				else:
					self._currentAttacher = self._attacher
				
				if hasattr(intersection, 'VIZ_TOOL_PLACER'):
					self._currentPlacer = intersection.VIZ_TOOL_PLACER
				else:
					self._currentPlacer = self._placer
				
				# initialize the placer object
				self._currentPlacer.initialize(intersection)
				# attach the intersecting item
				self._currentAttacher.attach(intersection)
				# enable preview on placer if using previews
				self._currentPlacer.setPreviewEnabled(True)
				# send an event
				viz.sendEvent(GRAB_EVENT, viz.Event(grabber=self, grabbed=intersection))
			return intersection
		return None
	
	def release(self):
		"""Starts a release"""
		released = self._currentAttacher.getDst()
		if released is not None:
			# release the object
			self._currentAttacher.detach()
			# place the object
			self._currentPlacer.place(released)
			# disable preview on placer if using previews
			self._currentPlacer.setPreviewEnabled(False)
			# send out an event
			viz.sendEvent(RELEASE_EVENT, viz.Event(grabber=self, released=released))
		return released
	
	def grabAndHold(self):
		"""Grabs and holds"""
		if not self._frameLocked&self.LOCK_HOLD:
			self._held = self.grab()
		self._lockRequested |= self.LOCK_HOLD
	
	def toggleGrab(self):
		"""Toggles between grab and release."""
		if not self._frameLocked&self.LOCK_TOGGLE:
			if self._currentAttacher.getDst() is not None:
				self.release()
			else:
				self.grab()
		self._lockRequested |= self.LOCK_TOGGLE
	
	def getAttacher(self):
		"""Returns the attacher object used by the grabber. See toos/attacher.py
		for a set of attachment classes.
		"""
		return self._currentAttacher
	
	def getCollisionTester(self):
		"""Returns the collision testing object used for intersections. See
		tools/collision_test.py for a set of collision objects. Can be any
		object derived from tools.collision_test.CollisionTester
		"""
		return self._collisionTester
	
	def getHighlight(self):
		"""Returns the highlight object used for highlighting intersections
		and grabbed objects. See tools/highlighter.py for a set of compatible
		objects. Can be any object derived from tools.highlighter.Highlight
		"""
		return self._highlighter
	
	def getPlacer(self):
		"""Returns the placer object used for placing released objects
		objects. See tools/placer.py for a set of compatible objects. Can be
		any object derived from tools.placer.Placer.
		"""
		return self._placer
	
	def setAttacher(self, attacher):
		"""Sets the attacher object used by the grabber. See toos/attacher.py
		for a set of attachment classes.
		"""
		self._attacher = attacher
	
	def setCollisionTester(self, collisionTester):
		"""Sets the collision testing object used for intersections. See
		tools/collision_test.py for a set of collision objects. Can be any
		object derived from tools.collision_test.CollisionTester
		"""
		self._collisionTester = collisionTester
		self._collisionTester.setItems(self._items)
	
	def setHighlight(self, highlight):
		"""Sets the highlight object used for highlighting intersections
		and grabbed objects. See tools/highlighter.py for a set of compatible
		objects. Can be any object derived from tools.highlighter.Highlight
		"""
		self._highlighter = highlight
		if self._highlighter and self._preLoadHighlights:
			for item in self._items:
				self._highlighter.add(item)
				self._highlighter.setVisible(item, False)
	
	def setPlacer(self, placer):
		"""Sets the placer object used for placing released objects
		objects. See tools/placer.py for a set of compatible objects. Can be
		any object derived from tools.placer.Placer.
		"""
		self._placer = placer
	
	def setItems(self, items, *args, **kwargs):
		"""Sets the list of grabbable items"""
		super(AbstractGrabber, self).setItems(items, *args, **kwargs)
		self._collisionTester.setItems(items)
		if self._highlighter and self._preLoadHighlights:
			for item in items:
				if hasattr(item, 'VIZ_TOOL_HIGHLIGHTER'):
					item.VIZ_TOOL_HIGHLIGHTER.add(item)
					item.VIZ_TOOL_HIGHLIGHTER.setVisible(item, False)
				else:
					self._highlighter.add(item)
					self._highlighter.setVisible(item, False)
		if self._useToolTag:
			for item in items:
				if hasattr(item, "toolTag"):
					item.toolTag |= tools.TAG_GRAB
				else:
					item.toolTag = tools.TAG_GRAB
		# check if we have separate collision testers
		self._itemCollisionTesterSet.clear()
		self._itemCollisionTesterList = {}
		for item in items:
			if hasattr(item, 'VIZ_TOOL_COLLISION_TESTER_FUNC'):
				if not item.VIZ_TOOL_COLLISION_TESTER_FUNC in self._itemCollisionTesterSet:
					self._itemCollisionTesterSet.add(item.VIZ_TOOL_COLLISION_TESTER_FUNC)
					ct = item.VIZ_TOOL_COLLISION_TESTER_FUNC(node=self)
					self._itemCollisionTesterList[item.VIZ_TOOL_COLLISION_TESTER_FUNC] = ct
				
				ct = self._itemCollisionTesterList[item.VIZ_TOOL_COLLISION_TESTER_FUNC]
				ct.setItems(ct.getItems()+[item])
	
	def removeItems(self, items, *args, **kwargs):
		"""Removes a set of items from the current list of grabbable items."""
		super(AbstractGrabber, self).removeItems(items, *args, **kwargs)
		self.setItems(self._items)
	
	def _updateHighlight(self, intersection):
		"""Internal method which updates the highlight object based on
		intersections
		"""
		# only update the highlight if we're not grabbing anything
		if self._currentAttacher.getDst() is None and self._currentHighlightedNode != intersection:
			
			# hide the currently highlighted object
			if self._currentHighlightedNode is not None and self._currentHighlighter:
				if self._preLoadHighlights:
					self._currentHighlighter.setVisible(self._currentHighlightedNode, False)
				else:
					self._currentHighlighter.remove(self._currentHighlightedNode)
			
			if hasattr(intersection, 'VIZ_TOOL_HIGHLIGHTER'):
				self._currentHighlighter = intersection.VIZ_TOOL_HIGHLIGHTER
			else:
				self._currentHighlighter = self._highlighter
			
			# add the new highlight
			if intersection is not None and self._currentHighlighter:
				if self._preLoadHighlights:
					self._currentHighlighter.setVisible(intersection, True)
				else:
					self._currentHighlighter.add(intersection)
			
			# update the currently highlighted node
			self._currentHighlightedNode = intersection


class HandGrabber(AbstractGrabber):
	"""A Hand grabber class which provides a simple interface for typical grabbing"""
	def __init__(self,
					usingPhysics=True,
					usingSprings=True,
					placementMode=tools.placer.MODE_MID_AIR,
					highlightMode=tools.highlighter.MODE_OUTLINE,
					**kwargs):
		
		self._usingPhysics = usingPhysics
		
		highlight = tools.highlighter.addHighlight(highlightMode)
		
		# setup the node
		if self._usingPhysics:
			node = vizshape.addSphere(0.1)
			# disabling the next two just to be safe
			node.disable(viz.DYNAMICS)
			node.disable(viz.INTERSECTION)
			# toggling visibility
			node.visible(False)
		else:
			node = viz.addGroup()
		
		# setup the attachment method
		if usingSprings:
			attachmentObj = tools.attacher.Spring(src=node)
		else:
			attachmentObj = tools.attacher.Grab(src=node)
		
		# setup the collision detection method
		if usingPhysics:
			collisionTestObj = tools.collision_test.Physics(node=node)
		else:
			collisionTestObj = tools.collision_test.Distance(node=node)
		
		# define placer
		self._previewRay = None
		self._previewObject = None
		if placementMode == tools.placer.MODE_MID_AIR:
			self._placer = tools.placer.MidAir()
		elif placementMode == tools.placer.MODE_INSPECTION:
			self._previewRay = tools.ray_caster.StippledRay()
			self._previewObject = tools.getIndicatorPlane()
			self._previewObject.zoffset(-1)
			self._placer = tools.placer.Inspection(previewRay=self._previewRay,
													previewObject=self._previewObject,
													moveTime=1.0,
													spinTime=1.0)
		elif placementMode == tools.placer.MODE_DROP_DOWN:
			self._previewRay = tools.ray_caster.SimpleRay()
			self._previewObject = tools.getIndicatorPlane()
			self._placer = tools.placer.DropDown(previewRay=self._previewRay, previewObject=self._previewObject)
		elif placementMode == tools.placer.MODE_POINT_AND_PLACE:
			self._previewRay = tools.ray_caster.SimpleRay()
			self._previewObject = tools.getIndicatorPlane()
			rayCaster = tools.ray_caster.RayCaster()
			rayCaster.setParent(node)
			rayCaster.setRay(None)
			self._placer = tools.placer.PointAndPlace(targetRayCaster=rayCaster,
												previewRay=self._previewRay,
												previewObject=self._previewObject)
		else:
			self._placer = tools.placer.MidAir()
		
		# setup the grabber
		super(HandGrabber, self).__init__(node=node,
											collisionTester=collisionTestObj,
											attacher=attachmentObj,
											placer=self._placer,
											highlighter=highlight)
	
	def remove(self):
		"""Removes the grabber object"""
		super(HandGrabber, self).remove()
		self._node.remove()
		self._collisionTester.remove()
		self._attacher.remove()
		self._placer.remove()
		if self._highlighter:
			self._highlighter.remove()
		if self._previewRay:
			self._previewRay.remove()
			self._previewRay = None
		if self._previewObject:
			self._previewObject.remove()
			self._previewObject = None

Grabber = HandGrabber


class RayGrabber(AbstractGrabber):
	"""A convenience grabber class which uses a ray for intersection and placement."""
	def __init__(self,
					usingPhysics=False,
					highlightMode=tools.highlighter.MODE_OUTLINE,
					**kwargs):
		
		highlight = tools.highlighter.addHighlight(highlightMode)
		
		node = viz.addGroup()
		self._ray = tools.ray_caster.SimpleRay()
		
		self._collisionTester = tools.collision_test.Ray(node=node, ray=self._ray)
		
		self._previewRay = tools.ray_caster.SimpleRay()
		self._previewObject = tools.getIndicatorPlane()
		rayCaster = tools.ray_caster.RayCaster()
		rayCaster.setParent(node)
		self._placer = tools.placer.PointAndPlace(targetRayCaster=rayCaster,
													previewRay=self._previewRay,
													previewObject=self._previewObject)
		
		#self._placer = tools.placer.MidAir()
		self._attacher = tools.attacher.Grab(src=node)
		
		super(RayGrabber, self).__init__(node=node,
											collisionTester=self._collisionTester,
											attacher=self._attacher,
											placer=self._placer,
											highlighter=highlight)
	
	def finalize(self):
		"""Finalizes the grabbing"""
		super(RayGrabber, self).finalize()
		if self._attacher.getDst() is not None:
			self._ray.visible(False)
		else:
			self._ray.visible(True)
	
	def remove(self):
		"""Removes the grabber object"""
		super(RayGrabber, self).remove()
		self._node.remove()
		self._collisionTester.remove()
		self._attacher.remove()
		self._placer.remove()
		self._ray.remove()
		if self._highlighter:
			self._highlighter.remove()
		if self._previewRay:
			self._previewRay.remove()
			self._previewRay = None
		if self._previewObject:
			self._previewObject.remove()
			self._previewObject = None
