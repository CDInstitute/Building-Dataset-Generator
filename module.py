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
from material import MaterialFactory
from overlap_control import OverlapVolumeController, OverlapOtherVolumeController
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
	def __init__(self, module, axis, side=0):
		self.module = module
		self.axis = axis
		self.side = side
		self._connect()

	def _connect(self):
		gancio(self.module.volume, self.module, axis=self.axis, border1=self.side,
		       border2=1)


class Module:
	def __init__(self, name='generic', scale=None, mesh=None, volume=None):
		self.name = name
		self.connector = None
		self.scale = scale
		self.volume = volume
		if mesh:
			self.mesh = mesh
		else:
			self.mesh = self._create()
		try:
			self.parent = self._nest()
		except Exception:
			pass
		self._assign_id()
		self.y_offset = 0


	def __copy__(self):
		deselect_all()
		select(self.mesh)
		bpy.ops.object.duplicate_move()
		_name = self.mesh.name.split('.')[0]

		ind = [x.name for x in bpy.data.objects if _name + '.' in x.name or _name == x.name]
		mesh = bpy.data.objects[ind[-1]]
		m = self.__class__(self.name, scale=self.scale, mesh=mesh,
		                   volume=self.volume)
		# self._triangulate()

		if self.connector:
			m.connect(self.connector.axis, self.connector.side)
		return m

	def apply(self):
		if len(MODULES[self.name]['materials']) > 0:
			_material = np.random.choice(MODULES[self.name]['materials'])
			_material = MaterialFactory().produce(_material)
		else:
			_material = MaterialFactory().produce()
		print(self.name, '|', _material.value.name)
		self.mesh.active_material = _material.value

	def connect(self, axis, side=0):
		self._connect(axis, side)

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

	def _connect(self, axis, side):
		self.connector = self.ModuleConnector(self, axis, side)

	def _create(self):
		# rule how connects to mesh
		raise NotImplementedError

	def _nest(self):
		deselect_all()
		postfix = '_0'
		if '.' in self.volume.name:
			postfix = '.{}'.format(self.volume.name.split('.')[-1])
		if '.' in self.name:
			self.name = self.name.split('.')
		_name = self.name + postfix
		if _name not in [x.name for x in bpy.data.collections[self.volume.name].children]:
			bpy.data.collections.new(_name)
			_name = [x.name for x in bpy.data.collections if _name in x.name][-1]
			bpy.data.collections[self.volume.name].children.link(
				bpy.data.collections[_name])

		bpy.data.collections[_name].objects.link(bpy.data.objects[self.mesh.name])
		return bpy.data.collections[_name]

	def _old_nest(self):
		deselect_all()
		names = [x.name for x in bpy.data.collections]
		if self.name not in names:
			bpy.data.collections.new(self.name)
			bpy.data.collections['Building'].children.link(
				bpy.data.collections[self.name])
		bpy.data.collections[self.name].objects.link(bpy.data.objects[self.mesh.name])
		return bpy.data.collections[self.name]

	def _rename_material(self):
		ind = bpy.data.objects[self.name].active_material_index
		bpy.data.materials[ind].name = 'module_{}'.format(self.name)

	def _remove_material(self, empty=False):
		"""
		Function that removes a material from the scene.
		:return:
		"""
		if self.mesh.active_material:
			bpy.data.materials.remove(self.mesh.active_material, do_unlink=True)

	def _triangulate(self):
		deselect_all()
		if self.mesh:
			select(self.mesh)
			bpy.ops.object.modifier_add(type='TRIANGULATE')
			bpy.ops.object.modifier_apply()

	class ModuleConnector(Connector):
		def __init__(self, module, axis, side):
			Connector.__init__(self, module, axis, side)


class Window(Module):
	def __init__(self, name: str='window', scale: tuple=(1.5, 0.05, 1.5), mesh=None,
	             volume=None):
		Module.__init__(self, name, scale, mesh, volume=volume)
		self._triangulate()
		self.y_offset = 1.0

	def _create(self):
		bpy.ops.mesh.primitive_cube_add(size=1.0)
		bpy.ops.transform.resize(value=self.scale)
		bpy.context.selected_objects[0].name = self.name
		return bpy.context.selected_objects[0]

	class ModuleConnector(Connector):
		def __init__(self, module: Module, axis: bool, side):
			Connector.__init__(self, module, axis, side)

		def _connect(self):
			if self.axis == 0:
				self.module.mesh.rotation_euler[2] = math.radians(90)
			gancio(self.module.volume, self.module, axis=self.axis, border1=self.side,
			       border2=1)

			self.module.mesh.location[2] = 0


class Balcony(Module):
	def __init__(self, name: str='balcony', scale: tuple=(1.0, 1.0, 1.0), mesh=None,
	             volume=None):
		self.names = os.listdir('{}/{}'.format(MODULE_PATH, name))
		self.names = [x for x in self.names if x.endswith('.obj')]
		Module.__init__(self, name, scale, mesh, volume=volume)

	def __copy__(self):
		deselect_all()
		select(self.mesh)
		bpy.ops.object.duplicate_move()
		_name = self.mesh.name.split('.')[0]

		ind = [x.name for x in bpy.data.objects if _name + '.' in x.name or _name == x.name]
		mesh = bpy.data.objects[ind[-1]]
		m = self.__class__(self.name, scale=self.scale, mesh=mesh, volume=self.volume)
		# self._triangulate()

		# if self.connector:
		# 	m.connect(self.connector.volume, self.connector.axis,
		# 	          self.connector.side)
		return m

	def _create(self, name=None):
		if not name:
			name = np.random.choice(self.names)
		# if exists make a copy else import
		_num_images = len(bpy.data.images)
		_obj = [x for x in bpy.data.objects if name.split('.')[0] + '.' in x.name]
		if len(_obj) > 0:
			deselect_all()
			select(_obj[0])
			bpy.ops.object.duplicate_move()
			ind = [x.name for x in bpy.data.objects if name.split('.')[0] + '.' in x.name]
			return bpy.context.scene.objects[ind[-1]]
		else:
			bpy.ops.import_scene.obj(filepath='{}/{}/{}'.format(MODULE_PATH,
			                                                    self.name, name))
			bpy.context.selected_objects[0].name = name.split('.')[0]
			self.mesh = bpy.context.selected_objects[0]
			if not MODULES[self.name]['materials'] or \
					_num_images == len(bpy.data.images):
				self._remove_material()
			self._triangulate()

		return self.mesh #bpy.context.selected_objects[0]

	class ModuleConnector(Connector):
		def __init__(self, module: Module, axis: bool, side):
			Connector.__init__(self, module, axis, side)

		def _connect(self):
			gancio2(self.module.volume, self.module, self.axis, self.side, 1)
			self.module.mesh.location[2] = 0


class Roof(Module):
	def __init__(self, name: str='roof',
	             scale: tuple=(1.0, 1.0, 1.0), mesh=None,
	             volume=None):
		Module.__init__(self, name, scale, mesh, volume=volume)
		self._triangulate()
		self.y_offset = 1.0

	def position(self, position):
		pass

	def _create(self):
		if self.scale == (1.0, 1.0, 1.0):
			self.scale = list((1, 1, np.random.uniform(0.3, 0.8)))
			self.scale[0] = np.diff(get_min_max(self.volume.mesh, 0))[0] * (
						1 + np.random.uniform(0, 0.2))
			self.scale[1] = np.diff(get_min_max(self.volume.mesh, 1))[0] * (
						1 + np.random.uniform(0, 0.2))
		bpy.ops.mesh.primitive_cube_add(size=1.0)
		bpy.ops.transform.resize(value=self.scale)
		bpy.context.selected_objects[0].name = self.name
		return bpy.context.selected_objects[0]

	class ModuleConnector(Connector):
		def __init__(self, module: Module, axis: bool, side):
			Connector.__init__(self, module, axis, side=side)

		def _connect(self):
			select(self.module.mesh)
			top_connect(self.module.volume, self.module)


class ModuleFactory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.mapping = {'generic': Module,
		                'window': Window,
		                'balcony': Balcony,
		                'roof': Roof
		                }
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
			return self.mapping[name]
		else:
			return self.mapping['generic']


class ApplierFactory:
	"""
	Factory that produces volumes.
	"""
	def __init__(self):
		self.mapping = {'random': RandomGridApplier,
		                'column': ColumnApplier,
		                'row': RowApplier,
		                'grid': GridApplier,
		                'single': ModuleApplier}

	def produce(self, name: str) -> object:
		"""
		Function that produces a module based on its name.
		:param name: name of the module to produce, str, should be in mapping
		:return: generated module, Module
		"""
		key = MODULES[name]['rule']
		if key in list(self.mapping.keys()):
			# mask = self.mask_colors[list(self.mapping.keys()).index(name)]
			return self.mapping[key]
		else:
			return self.mapping['single']


class ModuleApplier:
	def __init__(self, module_type, name='single'):
		self.module_type = module_type
		self.name = name
		self.controller = OverlapVolumeController()
		self.volume_controller = OverlapOtherVolumeController()

	def apply(self, module, **args):
		self._apply(module, **args)

	def _apply(self, module, **args):
		assert issubclass(module.__class__,
		                  self.module_type), "This ModuleApplier is applicable" \
		                                     " only to {], got {}".format(self.module_type,
		                                                                  type(module))
		if 'position' in list(args.keys()):
			module.position(position)
			self.controller.make(m)
			try:
				self.volume_controller.make(m)
			except Exception:
				pass


class GridApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type, name='grid'):
		ModuleApplier.__init__(self, module_type, name)

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
		_start2 = int(offset[1] + module.y_offset + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.volume.height -
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

		for x in range(_start1, _end1, int(step_x)):
			for h in range(_start2, _end2, int(step_h)):
				m = copy(module)
				position = np.array([0, 0, 0])
				position[abs(1-axis)] = x
				position[2] = h
				m.position(position)
				self.controller.make(m)
				try:
					self.volume_controller.make(m)
				except Exception:
					pass

		module.remove()


class ColumnApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type, name='column'):
		ModuleApplier.__init__(self, module_type, name)

	def apply(self, module, grid=None, offset=(1.0, 1.0, 1.0, 1.0), step=None):
		self._apply(module, grid, offset, step)

	def _apply(self, module, grid, offset, step):
		"""

		:param module: module to apply to the volume, Module
		:param col: column to fill, int
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
		_start2 = int(offset[1] + module.y_offset + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.volume.height -
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

		col_number = np.random.randint(1, max(2, int((_end1 - _start1) / step_x)))
		columns = list(set(np.random.randint(0, int((_end1 - _start1) / step_x),
		                        size=col_number)))

		for col in columns:
			x = int(_start1) + int(step_x) * col
			for h in range(_start2, _end2, int(step_h)):
				m = copy(module)
				position = np.array([0, 0, 0])
				position[abs(1 - axis)] = x
				position[2] = h
				m.position(position)
				self.controller.make(m)
				try:
					self.volume_controller.make(m)
				except Exception:
					pass
		module.remove()


class RowApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type, name='row'):
		ModuleApplier.__init__(self, module_type, name)

	def apply(self, module, grid=None, offset=(1.0, 1.0, 1.0, 1.0), step=None):
		self._apply(module, grid, offset, step)

	def _apply(self, module, grid, offset, step):
		"""

		:param module: module to apply to the volume, Module
		:param col: column to fill, int
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
		_start2 = int(offset[1] + module.y_offset + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.volume.height -
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

		row_number = np.random.randint(1, max(2, int((_end1 - _start1) / step_x)))
		rows = list(set(np.random.randint(0, int((_end2 - _start2)/step_h),
		                                  size=row_number)))
		for row in rows:
			h = int(_start2) + int(step_h) * row
			for x in range(_start1, _end1, int(step_x)):
				m = copy(module)
				position = np.array([0, 0, 0])
				position[abs(1-axis)] = x
				position[2] = h
				m.position(position)
				self.controller.make(m)
				try:
					self.volume_controller.make(m)
				except Exception:
					pass
		module.remove()


class RandomGridApplier(ModuleApplier):
	"""
	Vertical Grid Applier.
	"""
	def __init__(self, module_type):
		ModuleApplier.__init__(self, module_type, name='random')

	def apply(self, module, grid=None, offset=(1.0, 1.0, 1.0, 1.0), step=None):
		self._apply(module, grid, offset, step)

	def _apply(self, module, grid, offset, step):
		"""

		:param module: module to apply to the volume, Module
		:param col: column to fill, int
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
		_start2 = int(offset[1] + module.y_offset + module.scale[2] / 2)
		_end1 = int(np.diff(get_min_max(module.volume.mesh, abs(1-axis))) -
		               (int(offset[2] + module.scale[abs(1-axis)] / 2)))
		_end2 = int(module.volume.height -
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


		# x = int(_start1) + int(step_x) * (col-1)
		for x in range(_start1, _end1, int(step_x)):
			for h in range(_start2, _end2, int(step_h)):
				if np.random.random() > 0.5:
					m = copy(module)
					position = np.array([0, 0, 0])
					position[abs(1-axis)] = x
					position[2] = h
					m.position(position)
					self.controller.make(m)
					try:
						self.volume_controller.make(m)
					except Exception:
						pass
		module.remove()

if __name__ == '__main__':
	f = ModuleFactory()


