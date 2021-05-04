import bpy, bmesh
from copy import copy
from math import radians
import math
from mathutils import Vector
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

def get_min_max(volume, axis):
	"""
	Function that returns limits of a mesh on the indicated axis. Only applied
	to objects that are not rotated or rotated to 90 degrees
	:param volume: volume to get the dims of, mesh
	:param axis: int, 0 - width; 1 - length; 2 - height
	:return: min, max, float
	"""
	bpy.context.view_layer.update()
	bb_vertices = [Vector(v) for v in volume.bound_box]
	mat = volume.matrix_world
	world_bb_vertices = [mat @ v for v in bb_vertices]
	return min([x[axis: axis + 1][0] for x in world_bb_vertices]), \
		   max([x[axis: axis + 1][0] for x in world_bb_vertices])


class IoU:
	"""
	Class that calculates a generic intersection over union of two objects.
	"""

	def __init__(self, v1, v2):
		"""
		Class initialization.
		:param v1: first volume, blender object
		:param v2: second volume, blender object
		"""
		self.name = 'iou'
		self.v1 = v1
		self.v2 = v2
		self.operations = {0: 'intersect', 1: 'union'}

	def calculate(self) -> float:
		"""
		Function that calculates the IoU metric
		:return: result of iou, float
		"""
		return self._calculate()

	def _apply_modifier(self, volume1, volume2, operation: bool=0) -> float:
		"""
		Function that applies a boolean modifier of a specified type.
		:param volume: volume to apply the modifier to, object
		:param operation: operation to apply, 0 - intersection, 1 - union
		:return: volume of the resulting object, float
		"""
		_volume = copy(volume1)
		deselect_all()
		select(_volume.mesh)
		bpy.ops.object.modifier_add(type='BOOLEAN')
		_volume.mesh.modifiers['Boolean'].operation = self.operations[
			operation].upper()
		_volume.mesh.modifiers['Boolean'].object = volume2.mesh
		bpy.ops.object.modifier_apply(modifier='Boolean')
		result = self._get(_volume.mesh)
		select(_volume.mesh)
		bpy.ops.object.delete()
		return result

	def _calculate(self) -> float:
		"""
		Function that calculates the IoU metric
		:return: result of iou, float
		"""
		return self._iou(self.v1, self.v2)

	def _copy(self, volume):
		"""
		Function that makes a copy of an object.
		:param volume: object to make a copy of
		:return: duplicate of the object
		"""
		deselect_all()
		select(volume)
		bpy.ops.object.duplicate_move()
		return bpy.context.scene.objects[-1]

	def _get(self, volume) -> float:
		"""
		Function that calculates the volume of a given object.
		:param volume: object to calculate the volume of
		:return: volume, float
		"""
		bm = bmesh.new()
		bm.from_mesh(volume.data)
		return bm.calc_volume()

	def _iou(self, v1, v2):
		_intersection = self._intersection(v1, v2)
		_union = self._apply_modifier(v1, v2, 1)
		return _intersection / _union

	def _intersection(self, v1, v2):
		return self._apply_modifier(v1, v2, 0)


class IoU3D(IoU):
	"""
	Class that calculates the intersection over union of two 3D objects.
	"""
	def __init__(self, v1, v2):
		"""
		Class initialization.
		:param v1: first volume, blender object
		:param v2: second volume, blender object
		"""
		IoU.__init__(self, v1, v2)
		self.name = 'iou3d'


class Intersection(IoU):
	"""
		Class that calculates the intersection over union of two 3D objects.
		"""

	def __init__(self, v1, v2):
		"""
		Class initialization.
		:param v1: first volume, blender object
		:param v2: second volume, blender object
		"""
		IoU.__init__(self, v1, v2)
		self.name = 'iou3d'

	def _calculate(self) -> float:
		"""
		Function that calculates the IoU metric
		:return: result of iou, float
		"""
		return self._intersection(self.v1, self.v2)


class IoU2D(IoU):
	"""
	Class that calculates the intersection over union of two 3D objects.
	"""
	def __init__(self, v1, v2):
		"""
		Class initialization.
		:param v1: first curve, blender curve
		:param v2: second curve, blender curve
		"""
		IoU.__init__(self, v1, v2)
		self.name = 'iou2d'

	def _calculate(self):
		_volume1 = self._curve_to_mesh(self.v1)
		_volume2 = self._curve_to_mesh(self.v2)
		iou = self._iou(_volume1, _volume2)
		_volume1.select_set(True)
		_volume2.select_set(True)
		bpy.ops.object.delete()

		return iou

	def _curve_to_mesh(self, curve):
		_curve = self._copy(curve)
		select(_curve)
		bpy.ops.object.convert(target='MESH')  # curve to mesh
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		# select mesh
		bpy.ops.mesh.fill_grid(span=12)
		bpy.ops.object.mode_set(mode='OBJECT')
		return _curve

	def _get(self, volume) -> float:
		"""
		Function that calculates the area of a given object.
		:param volume: object to calculate the area of
		:return: area, float
		"""
		select(volume)
		bm = bmesh.new()
		bm.from_mesh(volume.data)
		return sum([x.calc_area() for x in bm.faces])


def select(_volume):
	_volume.select_set(True)
	bpy.context.view_layer.objects.active = _volume


def deselect_all():
	"""
	Function that deselects all the objects in the scene.
	:return: None
	"""
	for obj in bpy.data.objects:
		obj.select_set(False)



if __name__ == '__main__':

	################

	TEST = '3D'

	################

	if TEST == '3D':
		bpy.ops.mesh.primitive_cube_add()
		bpy.ops.mesh.primitive_cube_add()
		v1 = bpy.data.objects['Cube']
		v2 = bpy.data.objects['Cube.001']
		v2.location[0] += 1
		v2.location[1] += 1
		v2.location[2] += 1
		print(IoU3D(v1, v2).calculate())
	elif TEST == '2D':
		bpy.ops.curve.primitive_bezier_circle_add()
		bpy.ops.curve.primitive_bezier_circle_add()
		v1 = bpy.data.objects['BezierCircle']
		v2 = bpy.data.objects['BezierCircle.001']
		v2.location[0] += 1
		v2.location[1] += 1
		print(IoU2D(v1, v2).calculate())

