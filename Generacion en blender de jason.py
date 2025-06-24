import bpy
import json
from bpy.props import StringProperty, PointerProperty, EnumProperty
from bpy.types import Operator, Panel, PropertyGroup

# Helper: list mesh objects
def get_mesh_objects(self, context):
    return [(obj.name, obj.name, "") for obj in context.scene.objects if obj.type == 'MESH']

# Settings to store path and base object
class EcosistemaSettings(PropertyGroup):
    json_path: StringProperty(
        name="JSON Path",
        description="Ruta al archivo ecosistema.json",
        default="",
        subtype='NONE'
    )
    base_object: EnumProperty(
        name="Modelo Base",
        description="Objeto a instanciar en cada punto",
        items=get_mesh_objects
    )

# Operator to open file browser
class OT_SelectJSON(Operator):
    bl_idname = "ecosistema.select_json"
    bl_label = "Seleccionar JSON"

    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        context.scene.ecosistema_settings.json_path = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Operator to import instances
class OT_ImportEcosistema(Operator):
    bl_idname = "ecosistema.import_json"
    bl_label = "Importar Ecosistema"

    def execute(self, context):
        props = context.scene.ecosistema_settings
        ruta = bpy.path.abspath(props.json_path)
        # Load JSON
        try:
            with open(ruta, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Error al cargar JSON: {e}")
            return {'CANCELLED'}
        # Get base object
        base = context.scene.objects.get(props.base_object)
        if not base:
            self.report({'ERROR'}, "Modelo base no encontrado")
            return {'CANCELLED'}
        # Remove previous
        for obj in list(context.collection.objects):
            if obj.get('is_ecosistema_instance'):
                bpy.data.objects.remove(obj, do_unlink=True)
        # Instantiate
        for punto in data:
            loc = (punto['x'], punto['y'], punto['z'])
            inst = base.copy()
            inst.data = base.data.copy()
            inst.location = loc
            inst['is_ecosistema_instance'] = True
            # Assign material
            label = punto.get('label', 0)
            mat_name = f"Cluster_{label}"
            if mat_name in bpy.data.materials:
                inst.data.materials.clear()
                inst.data.materials.append(bpy.data.materials[mat_name])
            context.collection.objects.link(inst)
        self.report({'INFO'}, "Ecosistema importado correctamente")
        return {'FINISHED'}

# UI Panel
class PT_EcosistemaPanel(Panel):
    bl_label = "Generador Ecosistema"
    bl_idname = "VIEW3D_PT_ecosistema"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ecosistema'

    def draw(self, context):
        layout = self.layout
        props = context.scene.ecosistema_settings
        # Show current path
        if props.json_path:
            layout.label(text=props.json_path)
        else:
            layout.label(text="No se ha seleccionado JSON")
        # Button to select
        layout.operator(OT_SelectJSON.bl_idname, icon='FILE_FOLDER')
        # Base object dropdown
        layout.prop(props, "base_object")
        # Import button
        layout.operator(OT_ImportEcosistema.bl_idname, icon='IMPORT')

# Registration
tool_classes = (
    EcosistemaSettings,
    OT_SelectJSON,
    OT_ImportEcosistema,
    PT_EcosistemaPanel,
)

def register():
    for cls in tool_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ecosistema_settings = PointerProperty(type=EcosistemaSettings)


def unregister():
    for cls in reversed(tool_classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ecosistema_settings

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass
    register()
