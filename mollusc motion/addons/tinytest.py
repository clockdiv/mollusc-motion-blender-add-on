
bl_info = {
    "name": "tinytest",
    "author": "Julian",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "category": "Hardware",
    "location": "",
    "description": "an organic and open source motion capture and motion control system",
    "warning" : "",
    "doc_url": "",
    "tracker_url": ""
}


import bpy



#                   Panels



class HARDWARE_PT_molluscmotion_setup(bpy.types.Panel):
    """Tiny Tests"""
    bl_idname = 'OBJECT_PT_TINY_TEST'
    bl_label = 'TinyTest'
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'tiny test'
        
    def draw(self, context):
        col = self.layout.column()
        col.label(text='Object:')
        col.prop(context.scene, 'tinytest_object', text='')

        # print(context.scene.mollusc_object.name)

#                   Blender Registration




def register():

    bpy.utils.register_class(HARDWARE_PT_molluscmotion_setup)
    bpy.types.Scene.tinytest_object = bpy.props.PointerProperty(name = 'Tiny Test Object', type = bpy.types.Object)

def unregister():
    bpy.utils.unregister_class(HARDWARE_PT_molluscmotion_setup)
    del bpy.types.Scene.tinytest_object

