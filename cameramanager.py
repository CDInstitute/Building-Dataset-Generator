import bpy
import numpy as np

from dataset_config import RENDER_VIEWS
from shp2obj import deselect_all


class CameraManager:
	"""
	Class that manages the cameras in the scene.
	"""
	def __init__(self):
		"""
		Class initialization.
		"""
		self.scene = bpy.context.scene
		self.main_camera = bpy.data.objects['Camera']
		if RENDER_VIEWS > 1:
			bpy.ops.object.camera_add()
			self.camera = bpy.data.objects['Camera.001']
			_ = self._nest_camera()

	def _nest_camera(self):
		deselect_all()
		bpy.data.collections['Collection'].objects.link(self.camera)
		deselect_all()
		self.camera.select_set(True)
		bpy.ops.collection.objects_remove(collection='Building')
		# bpy.data.collections['Building'].objects.unlink(self.camera)
		return bpy.data.collections['Collection']

	def make(self):
		"""
		Function that changes the camera to the secondary one and sets its position.
		:return:
		"""
		if RENDER_VIEWS > 1:
			self._make()

	def make_main(self):
		"""
		Function that changes the camera to the main one.
		:return:
		"""
		self.scene.camera = self.main_camera

	def _make(self):
		"""
		Function that changes the camera to the secondary one and sets its position.
		:return:
		"""
		self.scene.camera = self.camera
		self.camera.rotation_euler[0] = np.radians(np.random.randint(40, 100) +
		                                           np.random.random())
		self.camera.rotation_euler[2] = np.radians(np.random.randint(0, 360) +
		                                           np.random.random())
		print([np.degrees(x) for x in self.camera.rotation_euler])
