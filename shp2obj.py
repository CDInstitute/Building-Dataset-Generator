import argparse
import bpy
import numpy as np
import os
import sys
import textwrap

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
from annotation import Annotation
from blender_utils import get_min_max


class Building:
	"""
	Class that represents a building extruded from the contour, a single mesh.
	"""
	def __init__(self, mesh):
		self.building = mesh

	def get_bb(self):
		"""
		Function that gets the bounding box of the Building
		:return: bounding box, list of float
		[width_from, height_from, width_to, height_to]
		"""
		_bb = list(get_min_max(self.building, 0)) + \
		      list(get_min_max(self.building, 1))
		return _bb

	def save(self, filename='test', ext='obj'):
		"""
		Function that saves the building as a separate file.
		:param filename: name of the file to write without extension, str,
		default='test'
		:param ext: file extension, str, default='obj'
		:return:
		"""
		deselect_all()
		self.building.select_set(True)
		bpy.ops.export_scene.obj(filepath=filename, use_selection=True)


class Collection:
	# TESTED: collection_test.py
	def __init__(self, class_type):
		self.collection = []
		self.class_type = class_type

	def __iter__(self):
		return Iterator(self.collection, self.class_type)

	def __len__(self):
		return len(self.collection)

	def add(self, obj):
		"""
		Function that adds an object of its class (attr class_type)
		:param obj: Object to add to the collection, class_type
		:return:
		"""
		if obj.__class__ == type:
			if issubclass(obj, self.class_type):
				self.collection.append(obj)
		else:
			if isinstance(obj, self.class_type):
				self.collection.append(obj)
			elif issubclass(obj.__class__, self.class_type):
				self.collection.append(obj)
			elif isinstance(obj, list):
				for _object in obj:
					assert isinstance(_object,
					                  self.class_type), "Expected a list of {}," \
					                                    " got {}".format(
						self.class_type, type(_object))
					self.collection.append(_object)
			else:
				raise TypeError


class Iterator:
	"""
	Class that iterates over a collection.
	"""
	def __init__(self, collection, class_type):
		self.collection = collection
		self.index = 0
		self.class_type = class_type
		assert isinstance(self.collection, list), "Wrong iteration input."

	def __next__(self):
		try:
			_object = self.collection[self.index]
		except IndexError:
			raise StopIteration()
		self.index += 1
		assert isinstance(_object, self.class_type)
		return _object

	def __iter__(self):
		return self

	def has_next(self):
		return self.index < len(self.collection)


class BlenderReader:
	"""
	Class that reads 3D file .gltf and manages the scene in blender.
	"""
	def __init__(self, filename):
		self.filename = filename
		self._import()
		self.filename = self.filename.split('.')[-2]
		self.obj = bpy.data.objects
		self._clean()
		self.obj = bpy.data.objects

	def read(self):
		"""
		Function that returns all the objects in the active scene.
		:return:
		"""
		return self.obj

	def export(self, filename='test', ext='obj'):
		"""
		Function that exports the whole scene as a given extension.
		:param filename: name of the file to write without extension, str,
		default='test'
		:param ext: name of the extension of the file to write, str,
		default='obj'
		:return:
		"""
		deselect_all(True)
		if ext == 'obj':
			bpy.ops.export_scene.obj(filepath='{}.{}'.format(filename, ext))
		else:
			raise NotImplementedError
		print('File has been successfully saved as {}'.format(filename))

	def _clean(self):
		"""
		Function that cleans the scene from the excessive objects that do not
		belong to the model of interest.
		:return:
		"""
		to_clean = [x for x in self.obj if
		            x.parent and x.parent.name != self.filename.split('.')[0]]
		deselect_all()
		for mesh in to_clean:
			try:
				mesh.select_set(True)
				bpy.ops.object.delete()
			except Exception:
				pass

	def _import(self):
		"""
		Function that imports .gltf file into the scene.
		:return:
		"""
		bpy.ops.import_scene.gltf(filepath=self.filename)


def deselect_all(value=False):
	"""
	Function that deselects all the objects in the scene.
	:return: None
	"""
	for obj in bpy.data.objects:
		obj.select_set(value)


###############################################################################
# arguments

if __name__ == '__main__':

	filename = 'test.gltf'
	save = 'samples'

	if '--' in sys.argv:
		argv = sys.argv[sys.argv.index('--') + 1:]
		parser = argparse.ArgumentParser(description=textwrap.dedent('''\
			USAGE: blender --background setup.blend --python shp2obj.py -- 1.gltf

			------------------------------------------------------------------------

			This is an algorithm that divides a .gltf into separate .obj files.

			------------------------------------------------------------------------

			'''))
		parser.add_argument('file', type=str, help='path to .gltf file')
		parser.add_argument('--save', type=str,
		                    help='path to save the .obj files to', default='samples')
		args = parser.parse_known_args(argv)[0]
		try:
			args = parser.parse_args()

		except SystemExit as e:
			print(repr(e))

	filename = args.file
	save_path = args.save

	a = Annotation()

	reader = BlenderReader(filename)
	building_collection = Collection(Building)
	if save not in os.listdir():
		os.mkdir(save)
	for b in reader.obj:
		building_collection.add(Building(b))
	for i, b in enumerate(building_collection):
		a.add(name='{}/{}.png'.format(save, i), model='{}/{}.obj'.format(save, i),
		      bb=b.get_bb())
		b.save('{}/{}.obj'.format(save, i))
	a.write('test.json')
