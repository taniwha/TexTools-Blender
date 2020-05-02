import bpy
import bmesh
import operator
import time
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import settings
from . import utilities_ui

def get_edit_objects():
    objects = []
    for o in bpy.context.objects_in_mode:
        bm = bmesh.from_edit_mesh(o.data)
        uv_layers = bm.loops.layers.uv.verify();
        objects.append((o, bm, uv_layers))
    return objects

def selection_store(objects):
    settings.selection_vert_indexies = {}
    settings.selection_face_indexies = {}
    settings.selection_uv_loops = {}

    # https://blender.stackexchange.com/questions/5781/how-to-list-all-selected-elements-in-python
    # print("selectionStore")
    settings.selection_uv_mode = bpy.context.scene.tool_settings.uv_select_mode
    settings.selection_uv_pivot = bpy.context.tool_settings.transform_pivot_point
    
    settings.selection_uv_pivot_pos = bpy.context.space_data.cursor_location.copy()
    settings.selection_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
    for obj, bm, uv_layers in objects:
        #VERT Selection
        settings.selection_vert_indexies[obj] = []
        for vert in bm.verts:
            if vert.select:
                settings.selection_vert_indexies[obj].append(vert.index)

        settings.selection_face_indexies[obj] = []
        for face in bm.faces:
            if face.select:
                settings.selection_face_indexies[obj].append(face.index)

        #Face selections (Loops)
        settings.selection_uv_loops[obj] = []
        for face in bm.faces:
            for loop in face.loops:
                if loop[uv_layers].select:
                    settings.selection_uv_loops[obj].append([face.index, loop.vert.index])


def selection_restore(objects):
    # print("selectionRestore")
    bpy.context.scene.tool_settings.uv_select_mode = settings.selection_uv_mode
    bpy.context.tool_settings.transform_pivot_point = settings.selection_uv_pivot

    contextViewUV = utilities_ui.GetContextViewUV()
    if contextViewUV:
        bpy.ops.uv.cursor_set(contextViewUV, location=settings.selection_uv_pivot_pos)

    #Selection Mode
    bpy.context.scene.tool_settings.mesh_select_mode = settings.selection_mode

    for obj, bm, uv_layers in objects:
        if hasattr(bm.verts, "ensure_lookup_table"): 
            bm.verts.ensure_lookup_table()
            # bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        for f in bm.faces:
            f.select = False
            for l in f.loops:
                l[uv_layers].select = False
        for v in bm.verts:
            v.select = False

        #FACE selection
        for index in settings.selection_face_indexies[obj]:
            if index < len(bm.faces):
                bm.faces[index].select = True

        #VERT Selection
        for index in settings.selection_vert_indexies[obj]:
            if index < len(bm.verts):
                bm.verts[index].select = True

        #UV Face-UV Selections (Loops)
        for uv_set in settings.selection_uv_loops[obj]:
            for loop in bm.faces[ uv_set[0] ].loops:
                if loop.vert.index == uv_set[1]:
                    loop[uv_layers].select = True
                    break
        bmesh.update_edit_mesh(obj.data, False)
    bpy.context.view_layer.update()



def get_selected_faces():
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
    faces = [];
    for face in bm.faces:
        if face.select:
            faces.append(face)

    return faces



def set_selected_faces(face_set):
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
    uv_layers = bm.loops.layers.uv.verify();
    for face_uv in face_set:
        face, uv_layers = face_uv
        for loop in face.loops:
            loop[uv_layers].select = True


def get_selected_uvs(bm, uv_layers):
    """Returns selected mesh vertices of selected UV's"""
    uvs = []
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                if loop[uv_layers].select:
                    uvs.append( loop[uv_layers] )
    return uvs



def get_selected_uv_verts(bm, uv_layers):
    """Returns selected mesh vertices of selected UV's"""
    verts = set()
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                if loop[uv_layers].select:
                    verts.add( loop.vert )
    return list(verts)



def get_selected_uv_edges(bm, uv_layers):
    """Returns selected mesh edges of selected UV's"""
    verts = get_selected_uv_verts(bm, uv_layers)
    edges = []
    for edge in bm.edges:
        if edge.verts[0] in verts and edge.verts[1] in verts:
            edges.append(edge)
    return edges



def get_selected_uv_faces(bm, uv_layers):
    """Returns selected mesh faces of selected UV's"""
    faces = []
    for face in bm.faces:
        if face.select:
            count = 0
            for loop in face.loops:
                if loop[uv_layers].select:
                    count+=1
            if count == len(face.loops):
                faces.append(face)
    return faces



def get_vert_to_uv(bm, uv_layers):
    vert_to_uv = {}
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            uv = loop[uv_layers]
            if vert not in vert_to_uv:
                vert_to_uv[vert] = [uv];
            else:
                vert_to_uv[vert].append(uv)
    return vert_to_uv



def get_uv_to_vert(bm, uv_layers):
    uv_to_vert = {}
    for face in bm.faces:
        for loop in face.loops:
            vert = loop.vert
            uv = loop[uv_layers]
            if uv not in uv_to_vert:
                uv_to_vert[ uv ] = vert;
    return uv_to_vert


def getSelectionBBoxWorker(bm, uv_layers, bounds):
    countFaces = 0;
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                if loop[uv_layers].select is True:
                    uv = loop[uv_layers].uv
                    bounds.min.x = min(bounds.min.x, uv.x)
                    bounds.min.y = min(bounds.min.y, uv.y)
                    bounds.max.x = max(bounds.max.x, uv.x)
                    bounds.max.y = max(bounds.max.y, uv.y)
            
                    bounds.center+= uv
                    countFaces+=1
    return countFaces

def getSelectionBBox(objects):
    class Bounds:
        pass
    bounds = Bounds()
    bounds.min =Vector((99999999.0,99999999.0)) 
    bounds.max = Vector((-99999999.0,-99999999.0))
    bounds.center = Vector((0.0,0.0))

    countFaces = 0;
    for obj, bm, uv_layers in objects:
        countFaces += getSelectionBBoxWorker(bm, uv_layers, bounds)
                
    bbox = {}
    bbox['min'] = bounds.min
    bbox['max'] = bounds.max
    bbox['width'] = (bounds.max - bounds.min).x
    bbox['height'] = (bounds.max - bounds.min).y
    
    if countFaces == 0:
        bbox['center'] = bounds.min
    else:
        bbox['center'] = bounds.center / countFaces

    bbox['area'] = bbox['width'] * bbox['height']
    bbox['minLength'] = min(bbox['width'], bbox['height'])
    return bbox;



def getSelectionIslands(objects):
    #Reference A: https://github.com/nutti/Magic-UV/issues/41
    #Reference B: https://github.com/c30ra/uv-align-distribute/blob/v2.2/make_island.py

    #Extend selection
    if bpy.context.scene.tool_settings.use_uv_select_sync == False:
        bpy.ops.uv.select_linked()
 
    #Collect selected UV faces
    faces_selected = [];
    for obj, bm, uv_layers in objects:
        for face in bm.faces:
            if face.select and face.loops[0][uv_layers].select:
                faces_selected.append((face, uv_layers))
        
    #Collect UV islands
    # faces_parsed = []
    faces_unparsed = faces_selected.copy()
    islands = []
    for face_uv in faces_selected:
        if face_uv in faces_unparsed:
            face, uv_layers = face_uv
            #Select single face
            bpy.ops.uv.select_all(action='DESELECT')
            face.loops[0][uv_layers].select = True;
            bpy.ops.uv.select_linked()#Extend selection
            
            #Collect faces
            islandFaces = [face_uv];
            for f_uv in faces_unparsed:
                f, uvl = f_uv
                if f != face and f.select and f.loops[0][uvl].select:
                    islandFaces.append(f_uv)
            
            for f_uv in islandFaces:
                faces_unparsed.remove(f_uv)

            #Assign Faces to island
            islands.append(islandFaces)
    
    #Restore selection 
    # for face in faces_selected:
    #     for loop in face.loops:
    #         loop[uv_layers].select = True

    
    print("Islands: {}x".format(len(islands)))
    return islands
