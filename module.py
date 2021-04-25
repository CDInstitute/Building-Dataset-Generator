import bpy, bmesh
from contextlib import redirect_stdout, redirect_stderr
from copy import copy
import io
import math
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

stdout = io.StringIO()
from dataset_config import *
from blender_utils import *
from shp2obj import Collection, deselect_all


class IdAssigner:
	"""
	Class that assigns an instance id based on the module type.
	"""
	def __init__(self):
		self.mapping = {x: y for (x, y) in zip(MODULES, range(2, len(MODULES) + 2))}

	def make(self, name: str) -> int:
		"""
		Function that returns an id based on the module type. Numbering starts from
		1 since 0 is the building envelope.
		:param name: name of the module, str
		:return: id, int
		"""
		assert name in MODULES, "Expected name to be in MODULES, got {}".format(name)
		return self.mapping[name]


class Connector:
	def __init__(self, module, volume, axis, side=0):
		self.module = module
		self.axis = axis
		self.side = side
		self.volume = volume
		self._connect()

	def _connect(self):
		gancio(self.volume, self.module, self.axis, self.side, 1)


class Module:
	def __init__(self, name='generic', scale=None, mask=(1.0, 0.0, 0.0)):
		self.name = name
		self.connector = None
		self.scale = scale
		assert issubclass(mask.__class__, list) or issubclass(mask.__class__, tuple) \
		       or issubclass(mask.__class__, np.ndarray), "Expected mask to be an " \
		                                            "array or a tuple, got {}".format(type(mask))
		assert len(mask) == 3, "Expected mask to have 3 colors, got {}".format(len(mask))
		# self.mask = mask
		self.mesh = self._create()
		self.parent = self._nest()
		self._assign_id()
		self._triangulate()

	def __copy__(self):
		m = self.__class__(self.name, scale=self.scale)
		if self.connector:
			m.connect(self.connector.volume, self.connector.axis)
		return m

	def apply(self, material=None):
		if material:
			_material = MaterialFactory().produce(material)
		else:
			_material = MaterialFactory().produce()
		self.mesh.active_material = _material.value

	def connect(self, volume, axis, side=0):
		self._connect(volume, axis, side)

	# def mask(self):
	# 	material = MaterialFactory().produce('mask', color=self.mask)
	# 	self.mesh.active_material = material.value

	def position(self, position):
		assert isinstance(position, list) or isinstance(position, tuple) or \
		       isinstance(position, np.ndarray), "Expected position as a list or" \
		                                        " a tuple, got {}".format(type(position))
		assert len(position) == 3, "Position should have 3 values, " \
		                           "got {}".format(len(position))

		for i in range(len(position)):
			self.mesh.location[i] += position[i]

	def remove(self):
		deselect_all()
		bpy.data.objects[self.mesh.name].select_set(True)
		with redirect_stdout(stdout), redirect_stderr(stdout):
			bpy.ops.object.delete()

	def _assign_id(self):
		self.mesh["inst_id"] = IdAssigner().make(self.name)
		self.mesh.pass_index = IdAssigner().make(self.name)

	def _connect(self, volume, axis, side):
		self.connector = self.ModuleConnector(self, volume, axis, side)

	def _create(self):
		# rule how connects to mesh
		raise NotImplementedError

	def _nest(self):
		names = [x.name for x in bpy.data.collections]
		if self.name not in names:
			bpy.data.collections.new(self.name)
			bpy.data.collections['Building'].children.link(
				bpy.data.collections[self.name])
		bpy.data.collections[self.name].objects.link(bpy.data.objects[self.mesh.name])
		return bpy.data.collections[self.name]

	def _triangulate(self):
		deselect_all()
		if self.mesh:
			select(self.mesh)
			bpy.ops.object.modifier_add(type='TRIANGULATE')
			bpy.ops.object.modifier_apply()

	class ModuleConnector(Connector):
		def __init__(self, module, volume, axis, side):
			Connector.__init__(self, module, volume, axis, side)


class Window(Module):
	def __init__(self, name: str='window', scale: tuple=(1.5, 0.05, 1.5)):
		Module.__init__(self, name, scale)

	def _create(self):
		bpy.ops.mesh.primitive_cube_add(size=1.0)
		bpy.ops.transform.resize(value=self.scale)
		bpy.context.selected_objects[0].name = self.name
		return bpy.context.selected_objects[0]

	class ModuleConnector(Connector):
		def __init__(self, module: Module, volume, axis: bool, side):
			Connector.__init__(self, module, volume, axis, side)

		def _connect(self):
			if self.axis == 0:
				self.module.mesh.rotation_euler[2] = math.radians(90)
			gancio(self.volume, self.module, self.axis, self.side, 1)


class ModuleFactory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.mapping = {'generic': Module,
		                'window': Window}
		self.mapping = {x: y for x, y in self.mapping.items() if x in MODULES or x == 'generic'}
		self.mask_colors = list(range(len(self.mapping)))

	def produce(self, name: str) -> object:
		"""
		Function that produces a module based on its name.
		:param name: name of the module to produce, str, should be in mapping
		:return: generated module, Module
		"""
		if name in list(self.mapping.keys()):
			# mask = self.mask_colors[list(self.mapping.keys()).index(name)]
			return self.mapping[name]()
		else:
			return self.mapping['generic']()


class ModuleApplier:
	def __init__(self, module_type):
		self.module_type = module_type
		self.name = 'single'

	def apply(self, module, position):
		self._apply(module, position)

	def _apply(self, module, position):
		assert issubclass(module.__class__,
		                  self.module_type), "This ModuleApplier is applicable" \
		                                     " only to {], got {}".format(self.module_type,
		                                                                  type(module))
		module.position(position)


class GridApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type):
		ModuleApplier.__init__(self, module_type)
		self.name = 'grid'

	def apply(self, module, grid=None, offset=(1.0, 1.0, 1.0, 1.0), step=None):
		self._apply(module, grid, offset, step)

	def _apply(self, module, grid, offset, step):
		"""

		:param module: module to apply to the volume, Module
		:param grid: parameters of the grid for the module application, tuple
		(rows, cols), int. If step is given, not taken into account
		:param offset: offset from the borders of the volume, tuple
		(left, bottom, right, top), default = (1.0, 1.0, 1.0, 1.0)
		:param step: parameter of the grid, tuple (hor_step, vert_step),
		default=None
		:return:
		"""
		assert grid or step, "Please, provide either grid or step parameter"
		if grid:
			assert isinstance(grid, list) or isinstance(grid, tuple) or\
			       isinstance(grid, np.ndarray), "expected grid to be a list or a " \
			                                     "tuple, got {}".format(type(grid))
			assert len(grid) == 2, "Expected grid to have two elements, got" \
			                       " {}".format(len(grid))
		if step:
			assert isinstance(step, list) or isinstance(step, tuple) or\
			       isinstance(step, np.ndarray), "expected step to be a list or a " \
			                                     "tuple, got {}".format(type(step))
			assert len(step) == 2, "Expected step to have two elements, got" \
			                       " {}".format(len(step))

		assert isinstance(offset, list) or isinstance(offset, tuple) or isinstance(
			offset, np.ndarray), "expected offset to be a list or a " \
		                         "tuple, got {}".format(type(offset))
		assert len(offset) == 4, "Expected offset to have two elements, got " \
		                         "{}".format(len(offset))
		assert module.connector is not None, "Module should be connected to a volume"

		axis = module.connector.axis
		_start1 = int(offset[0] + module.scale[abs(1-axis)] / 2)
		_start2 = int(offset[1] + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.connector.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.connector.volume.height -
		           (int(offset[2] + module.scale[abs(1-axis)] / 2)))

		if step:
			step_x, step_h = step
		else:
			step_x, step_h = int((_end1 - _start1) / grid[0]),\
			                 int((_end2 - _start2) / grid[1])
			if step_x == 0:
				step_x = math.ceil((_end1 - _start1) / grid[0])
			if step_h == 0:
				step_h = math.ceil((_end2 - _start2) / grid[1])

		for x in range(_start1, _end1, step_x):
			for h in range(_start2, _end2, step_h):
				m = copy(module)
				position = np.array([0, 0, 0])
				position[abs(1-axis)] = x
				position[2] = h
				m.position(position)
		module.remove()


if __name__ == '__main__':
	f = ModuleFactory()


