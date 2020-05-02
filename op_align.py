import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_uv


class op(bpy.types.Operator):
    bl_idname = "uv.textools_align"
    bl_label = "Align"
    bl_description = "Align vertices, edges or shells"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.StringProperty(name="Direction", default="top")

    @classmethod
    def poll(cls, context):
        if not bpy.context.active_object:
            return False

        # Only in Edit mode
        if bpy.context.active_object.mode != 'EDIT':
            return False

        # Only in UV editor mode
        if bpy.context.area.type != 'IMAGE_EDITOR':
            return False

        # Requires UV map
        if not bpy.context.object.data.uv_layers:
            # self.report({'WARNING'}, "Object must have more than one UV map")
            return False

        # Not in Synced mode
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            return False

        return True

    def execute(self, context):

        align(context, self.direction)
        return {'FINISHED'}

from pprint import pprint
def align(context, direction):
    if direction not in ["bottom", "top", "left", "right"]:
        print("Unkown direction: "+str(direction))
        return

    objects = utilities_uv.get_edit_objects()
    # Store selection
    utilities_uv.selection_store(objects)

    #if len(obj.data.uv_layers) == 0:
    #    print("There is no UV channel or UV data set")
    #    return

    # Collect BBox sizes
    boundsAll = utilities_uv.getSelectionBBox(objects)

    mode = bpy.context.scene.tool_settings.uv_select_mode
    if mode == 'FACE' or mode == 'ISLAND':
        print("____ Align Islands")

        # Collect UV islands
        islands = utilities_uv.getSelectionIslands(objects)

        for island in islands:

            bpy.ops.uv.select_all(action='DESELECT')
            utilities_uv.set_selected_faces(island)
            bounds = utilities_uv.getSelectionBBox(objects)

            # print("Island "+str(len(island))+"x faces, delta: "+str(delta.y))

            if direction == "bottom":
                delta = boundsAll['min'] - bounds['min']
                delta.x = 0
            elif direction == "top":
                delta = boundsAll['max'] - bounds['max']
                delta.x = 0
            elif direction == "left":
                delta = boundsAll['min'] - bounds['min']
                delta.y = 0
            elif direction == "right":
                delta = boundsAll['max'] - bounds['max']
                delta.y = 0
            for f_uv in island:
                f, uv_layers = f_uv
                for l in f.loops:
                    luv = l[uv_layers]
                    luv.uv += delta

    elif mode == 'EDGE' or mode == 'VERTEX':
        print("____ Align Verts")

        for obj, bm, uv_layers in objects:
            for f in bm.faces:
                if f.select:
                    for l in f.loops:
                        luv = l[uv_layers]
                        if luv.select:
                            # print("Idx: "+str(luv.uv))
                            if direction == "top":
                                luv.uv[1] = boundsAll['max'].y
                            elif direction == "bottom":
                                luv.uv[1] = boundsAll['min'].y
                            elif direction == "left":
                                luv.uv[0] = boundsAll['min'].x
                            elif direction == "right":
                                luv.uv[0] = boundsAll['max'].x

        bmesh.update_edit_mesh(obj.data)

    # Restore selection
    utilities_uv.selection_restore(objects)


bpy.utils.register_class(op)
