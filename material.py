import bpy
import numpy as np
import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)
file_dir = file_dir.replace('\\', '/').replace('\r', '/r').replace('\n', '/n').\
	replace('\t', '/t')

# TODO: check mtl import option


class Material:
	"""
	Class that represents a material object in Blender.
	"""
	def __init__(self, name):
		self.name = name.lower().capitalize()  # name of the material and its texture folder
		self.filename = 'material'
		self._path = file_dir + '/Textures/{}.blend'.format(self.filename)
		self._add = '\\Material\\'
		self.value = self._load()  # loads material into the scene
		self._update_nodes()  # loads the textures to the material

	def _load(self):
		try:
			return bpy.data.materials[self.name]  #.copy()
		except KeyError:
			return self._load_new()

	def _load_maps(self, map_type):
		"""
		Function that uploads texture map into the Material tree nodes. Textures
		 are taken from folder Texture/Material where Material corresponds to the
		 name of the material.
		:param map_type: type of the map to upload, str, one of 'Diffuse', 'Normal',
		'Roughness', 'Displacement'
		:return: texture map, bpy image object
		"""
		assert map_type in ['Diffuse', 'Normal', 'Roughness', 'Displacement'], \
			"Unknown map type, expected one of: 'Diffuse', 'Normal'," \
			"'Roughness', 'Displacement'"
		try:
			bpy.ops.image.open(filepath=file_dir + '/Textures/{}/{}.png'.
			                   format(self.name, map_type.capitalize()))
			_images = [x.filepath for x in bpy.data.images]
			return bpy.data.images[_images.index('//Textures'
			                                     '\\{}\\{}.png'.format(self.name,
			                                                               map_type))]
		except Exception as e:
			print('Failed to load {} texture of {}'.format(map_type, self.name))
			print(repr(e))

	def _load_new(self):
		try:
			# print(file_dir)
			bpy.ops.wm.append(filepath=self._path + self._add + self.filename,
				filename='{}'.format(self.filename),
				directory=self._path + self._add)
			materials = [x for x in bpy.data.materials if x.name.startswith('material')]
			materials[-1].name = self.name
			return bpy.data.materials[self.name]
		except Exception as e:
			print(repr(e))
			print('Could not import {} from {}'.format(self.name, self._path))
			raise KeyboardInterrupt()

	def _update_nodes(self):
		"""
		Function that updates the nodes of the material tree with the material
		textures.
		:return:
		"""
		if 'Diffuse_texture' in [x.name for x in self.value.node_tree.nodes]:
			self.value.node_tree.nodes['Diffuse_texture'].image = self._load_maps('Diffuse')
			self.value.node_tree.nodes['Normal_texture'].image = self._load_maps('Normal')
			self.value.node_tree.nodes['Displacement_texture'].image = self._load_maps('Displacement')
		else:
			self.value = self._load_new()
			self._update_nodes()


class MaskMaterial(Material):
	def __init__(self, name='mask', filename='mask', color=(1.0, 1.0, 1.0)):
		self.filename = filename
		self.color = color
		Material.__init__(self, name, filename=self.filename)

	def _update_nodes(self):
		self.value.node_tree.nodes['RGB'].outputs[0].default_value[0] = self.color[0]
		self.value.node_tree.nodes['RGB'].outputs[0].default_value[1] = self.color[1]
		self.value.node_tree.nodes['RGB'].outputs[0].default_value[2] = self.color[2]


class GlassMaterial(Material):
	def __init__(self, name='glass'):
		Material.__init__(self, name)

	def _load(self):
		try:
			return bpy.data.materials[self.name]
		except Exception:
			bpy.ops.material.new()
			_material = [x for x in bpy.data.materials if 'Material' in x.name][-1]
			_material.name = self.name
			return _material

	def _update_nodes(self):
		if 'Glass BSDF' not in [x.name for x in self.value.node_tree.nodes]:
			self.value.node_tree.nodes.new('ShaderNodeBsdfGlass')
			node1 = self.value.node_tree.nodes['Glass BSDF']
			node2 = self.value.node_tree.nodes['Material Output']
			_ = self.value.node_tree.links.new(node1.outputs[0], node2.inputs[0])


class MetallMaterial(Material):
	def __init__(self, name='metall'):
		Material.__init__(self, name)

	def _load(self):
		try:
			return bpy.data.materials[self.name]
		except Exception:
			bpy.ops.material.new()
			_material = [x for x in bpy.data.materials if 'Material' in x.name][-1]
			_material.name = self.name
			return _material

	def _update_nodes(self):
		if 'Principled BSDF' not in [x.name for x in self.value.node_tree.nodes]:
			self.value.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
			node1 = self.value.node_tree.nodes['Principled BSDF']
			_gray = np.random.uniform(0.2, 0.4)
			node1.inputs[0].default_value = [_gray, _gray, _gray, 1.0]
			node1.inputs[4] = 1.0

			node2 = self.value.node_tree.nodes['Material Output']
			_ = self.value.node_tree.links.new(node1.outputs[0], node2.inputs[0])


class MaterialFactory:
	"""
	Class that produces materials based on the given name.
	"""
	def __init__(self):
		self.materials = os.listdir('{}/Textures'.format(file_dir))
		self.materials = [x for x in self.materials if os.path.isdir('{}/Textures/{}'.format(file_dir, x))]

	def produce(self, name=None, color=None):
		if name:
			if name == 'mask':
				if not color:
					color = [1.0, 0.0, 0.0]
				return MaskMaterial(name, color)
			elif name == 'glass':
				return GlassMaterial(name.lower().capitalize())
			elif name == 'metall':
				return MetallMaterial(name.lower().capitalize())
			else:
				name = name.lower().capitalize()
				assert name in self.materials, "Unknown material {}, not in Textures folder".format(name)
				return Material(name)
		else:
			return Material(np.random.choice(self.materials))


if __name__ == '__main__':

	from generator import *

	material = MaterialFactory().produce('CONCrete')
	f = CollectionFactory()
	collection = f.produce(number=1)
	building = ComposedBuilding(collection.collection)
	building.make()
	building.volumes[0].apply(material)
