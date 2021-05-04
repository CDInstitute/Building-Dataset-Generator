import bpy, bmesh
from copy import copy
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
import os
import sys

file_dir = os.path.dirname(__file__)
sys.path.append(file_dir)

from iou import IoU3D, Intersection


def deselect_all():
	"""
	Function that deselects all the objects in the scene.
	:return: None
	"""
	for obj in bpy.data.objects:
		obj.select_set(False)


def extrude(mesh, height, direction=-1):
	"""
	Function that extrudes a given plane to a given height in a given direciton.
	:param mesh: plane to extrude, Blender plane object mesh
	:param height: height to extrude the plane to, float or int
	:param direction: direction to make the extrusion into, -1 -> top
															  1 -> bottom,
															  default = -1
	:return:
	"""
	assert issubclass(height.__class__, int) or \
		   issubclass(height.__class__, float), "Expected height as a float or " \
												"an int, got {}".format(type(height))
	assert direction in [-1, 1], "Expected direction to be -1 or 1, got {}".format(direction)

	mesh.select_set(True)
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(type='FACE')  # Change to face selection
	bpy.ops.mesh.select_all(action='SELECT')  # Select all faces

	bm = bmesh.new()
	bm = bmesh.from_edit_mesh(bpy.context.object.data)

	# Extude Bmesh
	for f in bm.faces:
		face = f.normal
	r = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
	verts = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
	TranslateDirection = face * direction * height  # Extrude Strength/Length
	bmesh.ops.translate(bm, vec=TranslateDirection, verts=verts)

	# Update & Destroy Bmesh
	bmesh.update_edit_mesh(
		bpy.context.object.data)  # Write the bmesh back to the mesh
	bm.free()  # free and prevent further access

	# Flip normals
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.flip_normals()

	# At end recalculate UV
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.uv.smart_project()

	# Switch back to Object at end
	bpy.ops.object.mode_set(mode='OBJECT')

	# Origin to center
	bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')


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

def gancio(v1, v2, axis, border1=0, border2=0):
	"""
	Function that attaches one volume to another one based on condition.
	:param v1: volume to attach the other volume to, Volume or Module
	:param v2: volume to attach to the other volume, Volume or Module
	:param axis: axis along which the volume will be attached, bool, 0 - x axis,
																	   1 - y axis
	:param border1: max or min side of the axis, 0 - min, 1 - max
	:param border2: max or min side of the opposite axis, 0 - min, 1 - max
	:return:
	"""
	mapping = {0: -1, 1: 1}
	coords1 = [get_min_max(v1.mesh, 0), get_min_max(v1.mesh, 1)]
	coords2 = [get_min_max(v2.mesh, 0), get_min_max(v2.mesh, 1)]

	v2.mesh.location[axis] = coords1[axis][border1] + \
							 (0.5 * np.diff(coords2[axis]) * mapping[border1])

	v2.mesh.location[abs(1 - axis)] = coords1[abs(1 - axis)][border2] + \
									  mapping[abs(1 - border2)] * np.diff(coords1[abs(1 - axis)]) + \
									  (0.5 * np.diff(coords2[abs(1-axis)]) * mapping[border2])

def gancio2(v1, v2, axis, border1=0, border2=0):
	"""
	Function that attaches one volume to another one based on condition.
	:param v1: volume to attach the other volume to, Volume or Module
	:param v2: volume to attach to the other volume, Volume or Module
	:param axis: axis along which the volume will be attached, bool, 0 - x axis,
																	   1 - y axis
	:param border1: max or min side of the axis, 0 - min, 1 - max
	:param border2: max or min side of the opposite axis, 0 - min, 1 - max
	:return:
	"""

	v2.mesh.rotation_euler[2] = 0
	v2.mesh.location[2] = 0
	place(v1, v2, axis, border1, border2)
	_intersections = []

	iou = Intersection(v1, v2)

	for i in range(8):

		# while intersection_check(v1.mesh, v2.mesh):
		deselect_all()
		v2.mesh.rotation_euler[2] += np.radians(90)
		place(v1, v2, axis, border1, border2)


		if border2 == 1:
			v2.mesh.location[abs(1-axis)] += 0.5
		else:
			v2.mesh.location[abs(1-axis)] -= 0.5


		# inter = intersection_check(v1.mesh, v2.mesh)
		inter = iou.calculate()
		if i < 4:
			_intersections.append(inter)
		if i >= 4:
			if inter == min(_intersections):
				v2.mesh.rotation_euler[2] -= np.radians(360)
				break

	place(v1, v2, axis, border1, border2)


def gancio3(v1, v2, axis, border1=0, border2=0):
	"""
	Function that attaches one volume to another one based on condition.
	:param v1: volume to attach the other volume to, Volume or Module
	:param v2: volume to attach to the other volume, Volume or Module
	:param axis: axis along which the volume will be attached, bool, 0 - x axis,
																	   1 - y axis
	:param border1: max or min side of the axis, 0 - min, 1 - max
	:param border2: max or min side of the opposite axis, 0 - min, 1 - max
	:return:
	"""

	v2.mesh.rotation_euler[2] = 0
	place(v1, v2, axis, border1, border2)
	_intersections = []

	iou = Intersection(v1, v2)

	for i in range(8):

		# while intersection_check(v1.mesh, v2.mesh):
		deselect_all()
		v2.mesh.rotation_euler[2] += np.radians(90)
		place(v1, v2, axis, border1, border2)

		if border2 == 1:
			v2.mesh.location[abs(1 - axis)] += 0.5
		else:
			v2.mesh.location[abs(1 - axis)] -= 0.5

		# inter = intersection_check(v1.mesh, v2.mesh)
		inter = iou.calculate(i)
		if i < 4:
			_intersections.append(inter)
		if i >= 4:
			if inter == min(_intersections):
				v2.mesh.rotation_euler[2] -= np.radians(360)
				break

	place(v1, v2, axis, border1, border2)
	if border2 == 1:
		v2.mesh.location[abs(1-axis)] += 0.5
	else:
		v2.mesh.location[abs(1-axis)] -= 0.5


def place(v1, v2, axis, border1, border2):
	mapping = {0: -1, 1: 1}
	coords1 = [get_min_max(v1.mesh, 0), get_min_max(v1.mesh, 1)]  # volume min max
	v2.mesh.location[axis] = coords1[axis][border1]  # border1 - front or back
	v2.mesh.location[abs(1 - axis)] = coords1[abs(1 - axis)][border2] + mapping[
		abs(1 - border2)] * np.diff(coords1[abs(1 - axis)])  # border2 start or end


def intersection_check(v1, v2):

	bm1 = bmesh.new()
	bm2 = bmesh.new()

	#fill bmesh data from objects
	bm1.from_mesh(v1.data)
	bm2.from_mesh(v2.data)

	#fixed it here:
	bm1.transform(v1.matrix_world)
	bm2.transform(v2.matrix_world)

	#make BVH tree from BMesh of objects
	v1_BVHtree = BVHTree.FromBMesh(bm1)
	v2_BVHtree = BVHTree.FromBMesh(bm2)

	#get intersecting pairs
	inter = v1_BVHtree.overlap(v2_BVHtree)
	return inter

def select(_volume):
	_volume.select_set(True)
	bpy.context.view_layer.objects.active = _volume

def top_connect(volume, module):
	"""
	Function that connects a module to the top of the volume (roof)
	:param volume: volume to connect the module to
	:param module: module to connect to the volume
	:return:
	"""
	volume_top = get_min_max(volume.mesh, 2)[1]
	coords = get_min_max(module.mesh, 2)

	module.mesh.location[2] = volume_top + ((coords[1] - coords[0]) / 2)
	for axis in range(2):
		module.mesh.location[axis] = volume.mesh.location[axis]





