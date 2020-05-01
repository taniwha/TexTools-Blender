import bpy
import bmesh
import operator
import math

from . import utilities_texel


class op(bpy.types.Operator):
    bl_idname = "uv.textools_texel_density_get"
    bl_label = "Get Texel size"
    bl_description = "Get Pixel per unit ratio or Texel density"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        #Only in UV editor mode
        if bpy.context.area.type != 'IMAGE_EDITOR':
            return False

        if not bpy.context.active_object:
            return False
        
        if len(bpy.context.selected_objects) == 0:
            return False

        if bpy.context.active_object.type != 'MESH':
            return False

        if not bpy.context.object.data.uv_layers:
            return False

        # if bpy.context.object.mode == 'EDIT':
        #     # In edit mode requires face select mode
        #     if bpy.context.scene.tool_settings.mesh_select_mode[2] == False:
        #         return False

        return True

    def execute(self, context):
        get_texel_density(
            self, 
            context
        )
        return {'FINISHED'}



def get_texel_density(self, context):
    print("Get texel density")

    object_faces = utilities_texel.get_selected_object_faces()

    # Warning: No valid input objects
    if len(object_faces) == 0:
        self.report({'ERROR_INVALID_INPUT'}, "No UV maps or meshes selected" )
        return

    print("obj faces groups {}".format(len(object_faces)))

    # Collect Images / textures
    object_images = {}
    for obj in object_faces:
        image = utilities_texel.get_object_texture_image(obj)
        if image:
            object_images[obj] = image

    fallback_image = None
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            fallback_image = area.spaces[0].image
            break


    sum_area_vt = 0
    sum_area_uv = 0

    # Get area for each triangle in view and UV
    for obj in object_faces:
        # Find image of object
        if obj in object_images:
            image = object_images[obj]
        else: 
            image = fallback_image

        if image:
            if bpy.context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(obj.data)
            uv_layers = bm.loops.layers.uv.verify()
            bm.faces.ensure_lookup_table()

            for index in object_faces[obj]:
                face = bm.faces[index]

                # Triangle Verts
                triangle_uv = [loop[uv_layers].uv for loop in face.loops ]
                triangle_vt = [vert.co for vert in face.verts]

                #Triangle Areas
                face_area_vt = utilities_texel.get_area_triangle(
                    triangle_vt[0], 
                    triangle_vt[1], 
                    triangle_vt[2] 
                )
                face_area_uv = utilities_texel.get_area_triangle_uv(
                    triangle_uv[0], 
                    triangle_uv[1], 
                    triangle_uv[2],
                    image.size[0],
                    image.size[1]
                )
                sum_area_vt+= math.sqrt( face_area_vt )
                sum_area_uv+= math.sqrt( face_area_uv ) * min(image.size[0], image.size[1])

    # print("Sum verts area {}".format(sum_area_vt))
    # print("Sum texture area {}".format(sum_area_uv))

    if sum_area_uv == 0 or sum_area_vt == 0:
        bpy.context.scene.texToolsSettings.texel_density = 0
    else:
        bpy.context.scene.texToolsSettings.texel_density = sum_area_uv / sum_area_vt

bpy.utils.register_class(op)
    
