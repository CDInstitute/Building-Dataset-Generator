import bpy, bmesh
from mathutils import Vector
import numpy as np


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
	return min([x[axis:axis+1][0] for x in world_bb_vertices]), \
	       max([x[axis:axis+1][0] for x in world_bb_vertices])

def gancio(v1, v2, axis, border1=0, border2=0):
	"""
	Function that attaches one volume to another one based on condition.
	:param v1: volume to attach the other volume to, Volume
	:param v2: volume to attach to the other volume, Volume
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

def select(_volume):
	_volume.select_set(True)
	bpy.context.view_layer.objects.active = _volume

