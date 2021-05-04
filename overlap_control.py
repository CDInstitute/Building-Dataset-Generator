import bpy
import mathutils
import io
import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
stdout = io.StringIO()
from blender_utils import *
from iou import Intersection

class OverlapController:
	def __init__(self):
		self.name = 'v0'

	def make(self, m1, m2):
		"""
		Function that checks whether two objects overlap
		:param m1: object to check the overlap of, mesh
		:param m2: object to check the overlap of, mesh
		:return: result, bool
		"""
		return self._make(m1, m2)

	def _make(self, m1, m2):
		"""
		Function that checks whether two objects overlap
		:param m1: object to check the overlap of, mesh
		:param m2: object to check the overlap of, mesh
		:return: result, bool
		"""
		# length = (m1.matrix_world.to_translation() - m2.matrix_world.to_translation()).length
		length = (m1.location - m2.location).length
		if length < 1.5:
			# _result = intersection_check(m1, m2)
			# if len(_result) > 0:
			return True
		_result = intersection_check(m1, m2)
		if len(_result) > 0:
			return True

class OverlapVolumeController:
	def __init__(self):
		self.controller = OverlapController()

	def make(self, module):
		return self._make(module)

	def _make(self, module):
		_children = []
		for sub in [x.name for x in bpy.data.collections[module.volume.name].children]:
			if module.name not in sub and sub not in module.name:
				_children += bpy.data.collections[sub].objects

		for _child in _children:  # mesh
			result = self.controller.make(module.mesh, _child)
			if result:
				deselect_all()
				_child.select_set(True)
				# with redirect_stdout(stdout), redirect_stderr(stdout):
				bpy.ops.object.delete()

class OverlapOtherVolumeController:
	def __init__(self):
		self.controller = OverlapController()

	def make(self, module):
		return self._make(module)

	def _make(self, module):
		_volumes = [x for x in bpy.data.objects if 'volume' in x.name]

		for v in _volumes:  # mesh
			if v.name != module.volume.mesh.name:
				result = self.controller.make(module.mesh, v)
				if result:
					module.remove()
