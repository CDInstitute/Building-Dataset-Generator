import bpy, bmesh  #, bpycv
# import cv2
from math import radians
import numpy as np
import os
import random
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from dataset_config import ENGINE, MASK_SAVE, IMG_SAVE, MODULES, IMAGE_SIZE, \
	DEPTH_SAVE, RENDER_EXR, NORMALS_SAVE
from shp2obj import deselect_all


class Renderer:
	"""
	Class that manages the scene rendering. Incomplete.
	"""
	def __init__(self, mode=0):
		self.engine = ENGINE
		self.mode = mode
		if self.mode == 0:
			bpy.types.ImageFormatSettings.color_mode = 'RGBA'
		self._scene_name = bpy.data.scenes[-1].name
		self.scene = bpy.data.scenes[self._scene_name]
		self.scene.view_layers["View Layer"].use_pass_object_index = True
		self.scene.view_layers["View Layer"].use_pass_normal = True
		# self.scene.render.use_overwrite = False
		self.scene.render.image_settings.color_mode = 'RGBA'
		self.scene.render.resolution_x = IMAGE_SIZE[0]
		self.scene.render.resolution_y = IMAGE_SIZE[1]
		self.mask_tree = MaskNodeTree(self.mode)
		self.mask_tree.make()
		self.depth_tree = DepthTree()
		self.depth_tree.make()
		self.norm_tree = NormTree()
		self.norm_tree.make()

	def render(self, filename='new_mask_test'):
		"""
		Function that performs all the rendering steps: normal render, segmentation
		mask.
		:param filename: name of the file, str
		:return:
		"""

		deselect_all(True)
		bpy.ops.view3d.camera_to_view_selected()
		deselect_all()
		self.mask_tree.connect()
		self._render(filename)

		self._render_mask(filename)
		self.depth_tree.connect()
		bpy.ops.render.render()
		self._render_depth(filename)
		if RENDER_EXR:
			self.depth_tree.connect_root()
			bpy.ops.render.render()
			self._render_exr(filename)
		self.norm_tree.connect()
		bpy.ops.render.render()
		self._render_normals(filename)

	def _render_bpycv(self, filename='test'):
		"""
		Function that renders maps with the use of bpycv package.
		:param filename: name of the file to be saved, str, default 'test'
		:return:
		"""
		result = bpycv.render_data()
		cv2.imwrite("{}.png".format(filename), result["image"])
		cv2.imwrite("{}_mask.png".format(filename), result["inst"])
		cv2.imwrite("{}_depth.png".format(filename),
		            result["depth"] / result["depth"].max() * 255)

	def _render(self, filename):
		"""
		Function that renders the scene.
		:return:
		"""
		image_settings = bpy.context.scene.render.image_settings
		image_settings.file_format = "PNG"
		image_settings.color_depth = '8'
		bpy.data.scenes[self._scene_name].render.engine = self.engine
		bpy.ops.render.render()
		if not IMG_SAVE in os.listdir():
			os.mkdir(IMG_SAVE)
		bpy.data.images["Render Result"].save_render(
			'{}/{}.png'.format(IMG_SAVE, filename))

	def _render_depth(self, filename):
		"""
		Function that renders the scene as a multichannel mask.
		:return:
		"""
		if len(bpy.data.images) == 0:
			bpy.ops.render.render()
		if not DEPTH_SAVE in os.listdir():
			os.mkdir(DEPTH_SAVE)
		bpy.data.images["Viewer Node"].save_render(
			'{}/{}_depth.png'.format(DEPTH_SAVE, filename))

	def _render_exr(self, filename):
		image_settings = bpy.context.scene.render.image_settings
		image_settings.file_format = "OPEN_EXR"
		image_settings.color_depth = '32'
		bpy.data.images["Viewer Node"].save_render(
			'{}/{}_depth.exr'.format(DEPTH_SAVE, filename))

	def _render_mask(self, filename):
		"""
		Function that renders the scene as a multichannel mask.
		:return:
		"""
		if len(bpy.data.images) == 0:
			bpy.ops.render.render()
		if not MASK_SAVE in os.listdir():
			os.mkdir(MASK_SAVE)
		bpy.data.images["Viewer Node"].save_render(
			'{}/{}_mask.png'.format(MASK_SAVE, filename))

	def _render_normals(self, filename):
		"""
		Function that renders the scene as a multichannel mask.
		:return:
		"""
		if len(bpy.data.images) == 0:
			bpy.ops.render.render()
		if not NORMALS_SAVE in os.listdir():
			os.mkdir(NORMALS_SAVE)
		bpy.data.images["Viewer Node"].save_render(
			'{}/{}_normals.png'.format(NORMALS_SAVE, filename))

	def _render_keypoints(self):
		"""
		Function that renders the scene as a one-channel mask of predefined
		keypoints.
		:return:
		"""
		raise NotImplementedError


class Tree:
	"""
	Generic compositor tree.
	"""
	def __init__(self):
		"""
		Class initialization
		"""
		self.scene = bpy.data.scenes[0]
		self.scene.use_nodes = True
		self.links = self.scene.node_tree.links
		self.root_node = self.scene.node_tree.nodes["Render Layers"]
		if "Viewer" in [x.name for x in self.scene.node_tree.nodes]:
			self.output_node = self.scene.node_tree.nodes['Viewer']
		else:
			self.output_node = self.scene.node_tree.nodes.new(type="CompositorNodeViewer")
			self.margin = 1200
			self._place_node(self.output_node, self.root_node, 1)
		self.output_node.use_alpha = True
		self.name = 'Result_Node_Name'
		self.margin = 60

	def connect(self):
		"""
		Function that connects the tree output node to the viewer node.
		:return:
		"""
		result_node = self.scene.node_tree.nodes[self.name]
		field = result_node.outputs.keys()[0]
		_ = self.links.new(result_node.outputs[field],
		                   self.output_node.inputs["Image"])
		for node in self.scene.node_tree.nodes:
			node.select = False
		self.output_node.select = True
		self.scene.node_tree.nodes.active = self.output_node
		self.output_node.update()


	def make(self):
		"""
		Function that builds the entire node tree for instance segmentation and
		returns the resulting node.
		:return: resulting node, node
		"""
		self.scene.render.engine = ENGINE
		return self._make()

	def _make(self):

		return True

	def _place_node(self, node, prev_node, axis):
		"""
		Function that places a node near the previous one aligned along one axis.
		:param node: node to place, node
		:param prev_node: node to refer to, node
		:param axis: axis to align the node to, bool, 0 - vertical, 1 - horizontal
		:return:
		"""
		if axis == 1:
			offset = prev_node.width
		else:
			offset = prev_node.height
		node.location[abs(1 - axis)] = prev_node.location[abs(1 - axis)] + offset + self.margin
		node.location[axis] = prev_node.location[axis]


class DepthTree(Tree):
	def __init__(self):
		"""
		Class initialization
		"""
		Tree.__init__(self)
		self.name = "Normalize"

	def connect_root(self):
		"""
		Function of a depth tree to get the z data with normalization.
		:return:
		"""
		_ = self.links.new(self.root_node.outputs["Depth"],
		                   self.output_node.inputs["Image"])
		for node in self.scene.node_tree.nodes:
			node.select = False
		self.output_node.select = True
		self.scene.node_tree.nodes.active = self.output_node
		self.output_node.update()

	def _make(self):
		result_node = self.scene.node_tree.nodes.new(
			type="CompositorNodeNormalize")
		_ = self.links.new(self.root_node.outputs["Depth"],
		                   result_node.inputs["Value"])
		result_node.update()


class MaskNodeTree(Tree):
	def __init__(self, mode=0):
		"""
		Class initialization
		:param mode       segmentation mode: 0 - color, 1 - grayscale, default 0
		"""
		Tree.__init__(self)
		self.mode = mode
		self.name = "Mix"

	def _make(self):
		"""
		Function that creates a node tree with the necessary outputs to make
		segmentation masks.
		:return:
		"""

		result_node = None
		for index in range(1, len(MODULES) + 2):
			result_node = self._material_branch(index, result_node)

	def _make_add_node(self, node1, node2):
		"""
		Function that combines two nodes together summing their values.
		:param node1: first image node, node
		:param node2: second image node, node
		:return: resulting node, node
		"""
		add_node = self.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")
		add_node.blend_type = 'Add'.upper()
		link = self.links.new(node1.outputs["Image"], add_node.inputs[1])
		link = self.links.new(node2.outputs["Image"], add_node.inputs[2])
		return add_node

	def _make_color_node(self, value):
		"""
		Function that makes a mode with a color value (grayscale).
		:param value:
		:return: color node
		TODO: make a separate class
		TODO: add an option to make color masks (3 values -> rgba node)
		"""
		node = self.scene.node_tree.nodes.new(type="CompositorNodeValue")
		node.outputs[0].default_value = value
		alpha_node = self.scene.node_tree.nodes.new(type="CompositorNodeSetAlpha")
		_ = self.links.new(node.outputs["Value"], alpha_node.inputs["Image"])
		return alpha_node

	def _make_color_node_rgb(self, value):
		"""
		Function that makes a mode with a color value (rgb).
		:param value:
		:return: color node
		TODO: make a separate class
		TODO: add an option to make color masks (3 values -> rgba node)
		"""
		hsv_node = self.scene.node_tree.nodes.new(type="CompositorNodeCombHSVA")
		hsv_node.inputs[0].default_value = value
		hsv_node.inputs[1].default_value = 1.0
		hsv_node.inputs[2].default_value = 1.0
		return hsv_node

	def _make_mask_id_node(self, index):
		"""
		Function that takes input from the root node and renders one object id.
		:param index: index of the objects to render as a mask, int >= 0
		:return: mask_id_node, node
		"""
		node = self.scene.node_tree.nodes.new(type="CompositorNodeIDMask")
		node.use_antialiasing = True
		node.index = index
		node.update()
		_ = self.links.new(self.root_node.outputs["IndexOB"], node.inputs["ID value"])
		return node

	def _make_multiply_node(self, node1, node2):
		"""
		Function that combines two nodes together multiplying their values.
		:param node1: first image node, node
		:param node2: second image node, node
		:return: resulting node, node
		"""
		multiply_node = self.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")
		multiply_node.blend_type = 'Multiply'.upper()
		_ = self.links.new(node1.outputs["Alpha"], multiply_node.inputs[1])
		_ = self.links.new(node2.outputs["Image"], multiply_node.inputs[2])
		return multiply_node

	def _material_branch(self, index, result_node=None):
		"""
		Function that adds a mask material branch to the composite tree.
		:param index: index of the mask, int > 0
		:param result_node: previous resulting node to connect to the new branch, node
		:return: new resulting node, node
		"""
		mask_id_node = self._make_mask_id_node(index)
		if not result_node is None:
			self._place_node(mask_id_node, result_node, 1)
		else:
			self._place_node(mask_id_node, self.root_node, 1)
		if self.mode == 0:
			color_node = self._make_color_node_rgb(index / (len(MODULES) + 2))
		elif self.mode == 1:
			color_node = self._make_color_node(index/(len(MODULES) + 2))
		else:
			print("Color mode {} was not recognized".format(self.mode))
			raise NotImplementedError
		self._place_node(color_node, mask_id_node, 0)
		multiply_node = self._make_multiply_node(mask_id_node, color_node)
		self._place_node(multiply_node, mask_id_node, 1)
		if result_node:
			add_node = self._make_add_node(result_node, multiply_node)
			self._place_node(add_node, multiply_node, 1)
			self.name = add_node.name
			return add_node
		self.name = multiply_node.name
		return multiply_node


class NormTree(Tree):
	def __init__(self):
		Tree.__init__(self)
		self.name = "Normal"

	def connect(self):
		_ = self.links.new(self.root_node.outputs["Normal"],
		                   self.output_node.inputs["Image"])
		for node in self.scene.node_tree.nodes:
			node.select = False
		self.output_node.select = True
		self.scene.node_tree.nodes.active = self.output_node
		self.output_node.update()


if __name__ == '__main__':

	from generator import *
	from material import MaterialFactory
	from volume import CollectionFactory

	f = CollectionFactory()
	collection = f.produce(number=1)
	building = ComposedBuilding(collection.collection)
	building.make()
	for v in building.volumes:
		v.apply(MaterialFactory().produce())
	r = Renderer(mode=0)
	r.render()


