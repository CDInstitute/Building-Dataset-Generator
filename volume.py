import bpy, bmesh
from math import radians
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from blender_utils import *
from dataset_config import *
from material import Material
from module import *
from shp2obj import Collection, deselect_all


class Factory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.min_width = MIN_WIDTH
		self.min_length = MIN_LENGTH
		self.min_height = MIN_HEIGHT
		self.max_width = MAX_WIDTH
		self.max_length = MAX_LENGTH
		self.max_height = MAX_HEIGHT

	def produce(self, scale=None):
		"""
		Function that produces a volume based on the given scale.
		:param scale: tuple (width, length, height)
		:return: generated volume, Volume
		"""
		if scale is None:
			return self._produce_random()
		v = Volume(scale)
		v.create()
		return v

	def _produce_random(self):
		"""
		Function that produces a volume based on random parameters.
		:return: generated volume, Volume
		"""
		v = Volume(scale=(np.random.randint(self.min_length, self.max_length),
		                  np.random.randint(self.min_width, self.max_width),
		                  np.random.randint(self.min_height, self.max_height)))
		return v


class CollectionFactory:
	"""
	Class that generates a collection of volumes based on their number.
	"""
	def __init__(self):
		self.volume_factory = Factory()

	def produce(self, number=None):
		"""
		Function that produces a collection of volumes
		:param number: number of volumes to compose the building of, int
		:return: building, Collection of Volumes
		"""
		return self._produce(number)

	def _produce(self, number):
		"""
		Function that produces a collection of volumes
		:param number: number of volumes to compose the building of, int
		if None will be chosen randomly from 1 to the MAX_VOLUMES in config.py
		:return: building, Collection of Volumes
		"""
		c = Collection(Volume)
		if not number:
			number = np.random.randint(1, MAX_VOLUMES+1)

		for _ in range(number):
			c.add(self.volume_factory.produce())

		return c


class Volume:
	"""
	Class that represents one volume of a building.
	"""
	def __init__(self, scale=(1.0, 1.0, 1.0), location=(0.0, 0.0, 0.0)):
		assert len(location) == 3, "Expected 3 location coordinates," \
		                           " got {}".format(len(location))
		assert len(scale) == 3, "Expected 3 scale coordinates," \
		                        " got {}".format(len(scale))

		assert max([1 if (issubclass(x.__class__, int) or
		                  issubclass(x.__class__, float)) else 0 for x in
		            scale+location]) == 1, "Expected numeric tuples scale and location"

		##############################################

		self.height = float(max(MIN_HEIGHT, scale[2]))
		self.width = float(max(MIN_WIDTH, scale[0]))
		self.length = float(max(MIN_LENGTH, scale[1]))
		self.position = location
		self.name = ''
		self.mesh = None

	def apply(self, material):
		assert isinstance(material, Material), 'Expected Material object, got ' \
		                                       '{}'.format(type(material))
		self.mesh.active_material = material.value
		material.value.node_tree.nodes['Mapping'].inputs[3].default_value[0] = self.height * 10
		material.value.node_tree.nodes['Mapping'].inputs[3].default_value[1] = self.height
		material.value.node_tree.nodes['Mapping'].inputs[3].default_value[2] = self.height * 10 # self.width
		material.value.node_tree.nodes['Mapping'].inputs[3].default_value /= 2
		self.mesh.active_material = material.value
		print(material.value.node_tree.nodes['Mapping'].inputs[3].default_value)

	def create(self):
		"""
		Function that creates a mesh based on the input parameters.
		:return:
		"""

		bpy.ops.mesh.primitive_plane_add(location=self.position)
		bpy.ops.transform.resize(value=(self.length, self.width, 1.0))
		bpy.context.selected_objects[0].name = 'volume'
		self.name = bpy.context.selected_objects[0].name
		self.mesh = bpy.data.objects[self.name]
		self._nest()
		self._extrude()
		self.mesh["inst_id"] = 1  # instance id for the building envelope
		self.mesh.pass_index = 1
		deselect_all()
		self._triangulate()

	def _extrude(self):
		"""
		Function that extrudes the plane in order to create a mesh.
		:return:
		"""
		deselect_all()
		if self.mesh:
			extrude(self.mesh, self.height)

	def _nest(self):
		names = [x.name for x in bpy.data.collections['Building'].objects]
		if not self.name in names:
			bpy.data.collections['Building'].objects.link(
					bpy.data.objects[self.name])

	def _triangulate(self):
		deselect_all()
		if self.mesh:
			select(self.mesh)
			bpy.ops.object.modifier_add(type='TRIANGULATE')
			bpy.ops.object.modifier_apply()



if __name__ == '__main__':
	f = CollectionFactory()
	collection = f.produce(number=1)


	# axis = 1
	#
	# for j, v in enumerate(collection.collection):
	#
	# 	mod = GridApplier(Window)
	# 	w = Window()
	# 	w.connect(v, 1)
	# 	if j==0:
	# 		mod.apply(w, step=(4, 2), offset=(2.0, 2.0, 2.0, 1.0))
	# 	else:
	# 		mod.apply(w, step=(4, 2))


