import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv


class op(bpy.types.Operator):
    bl_idname = "uv.textools_island_align_edge"
    bl_label = "Align Island by Edge"
    bl_description = "Align the island by selected edge"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Only in UV editor mode
        if bpy.context.area.type != 'IMAGE_EDITOR':
            return False

        if not bpy.context.active_object:
            return False

        if bpy.context.active_object.type != 'MESH':
            return False

        # Only in Edit mode
        if bpy.context.active_object.mode != 'EDIT':
            return False

        if bpy.context.scene.tool_settings.use_uv_select_sync:
            return False

        # Requires UV map
        if not bpy.context.object.data.uv_layers:
            return False

        # Requires UV Edge select mode
        if bpy.context.scene.tool_settings.uv_select_mode != 'EDGE':
            return False

        return True

    def execute(self, context):
        main(context)

        return {'FINISHED'}


def main(context):
    print("Executing operator_island_align_edge")

    objects = utilities_uv.get_edit_objects()

    # Store selection
    utilities_uv.selection_store(objects)

    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    uv_layers = bm.loops.layers.uv.verify()

    faces_selected = []
    for obj, bm, uv_layers in objects:
        for face in bm.faces:
            if face.select:
                for loop in face.loops:
                    if loop[uv_layers].select:
                        faces_selected.append((face, uv_layers))
                        break

    print("faces_selected: "+str(len(faces_selected)))

    # Collect 2 uv verts for each island
    face_uvs = {}
    for f_uv in faces_selected:
        face, uv_layers = f_uv
        uvs = []
        for loop in face.loops:
            if loop[uv_layers].select:
                uvs.append(loop[uv_layers])
                if len(uvs) >= 2:
                    break
        if len(uvs) >= 2:
            face_uvs[f_uv] = uvs

    faces_islands = {}
    faces_unparsed = faces_selected.copy()
    for face_uv in face_uvs:
        if face_uv in faces_unparsed:
            face, uvl = face_uv
            bpy.ops.uv.select_all(action='DESELECT')
            face_uvs[face_uv][0].select = True
            bpy.ops.uv.select_linked()  # Extend selection

            # Collect faces
            faces_island = [face_uv]
            for f_uv in faces_unparsed:
                f, uv_layers = f_uv
                if f != face and f.select and f.loops[0][uv_layers].select:
                    print("append "+str(f.index))
                    faces_island.append(f_uv)
            for f in faces_island:
                faces_unparsed.remove(f)

            # Assign Faces to island
            faces_islands[face_uv] = faces_island

    print("Sets: {}x".format(len(faces_islands)))

    # Align each island to its edges
    for face in faces_islands:
        align_island(face_uvs[face][0].uv, face_uvs[face][1].uv,
                     faces_islands[face])

    # Restore selection
    utilities_uv.selection_restore(objects)


def align_island(uv_vert0, uv_vert1, faces):
    print("Align {}x faces".format(len(faces)))

    # Select faces
    bpy.ops.uv.select_all(action='DESELECT')
    for face, uv_layers in faces:
        for loop in face.loops:
            loop[uv_layers].select = True

    diff = uv_vert1 - uv_vert0
    angle = math.atan2(diff.y, diff.x) % (math.pi/2)

    bpy.ops.uv.select_linked()

    bpy.context.tool_settings.transform_pivot_point = 'CURSOR'
    bpy.ops.uv.cursor_set(location=uv_vert0 + diff/2)

    if angle >= (math.pi/4):
        angle = angle - (math.pi/2)

    bpy.ops.transform.rotate(value=angle, orient_axis='Z', constraint_axis=(
        False, False, False), orient_type='GLOBAL', mirror=False, use_proportional_edit=False)


bpy.utils.register_class(op)
