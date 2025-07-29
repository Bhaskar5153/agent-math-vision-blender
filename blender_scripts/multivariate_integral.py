import bpy
import math
from mathutils import Vector, Quaternion

# --- 1. Scene Setup ---
def setup_scene():
    """
    Clears the current Blender scene, sets up render parameters,
    adds a camera and a sun lamp, and configures the world background.
    """
    # Clear existing objects and reset to factory settings
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set animation parameters
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = 400  # Placeholder, will be adjusted at the end
    bpy.context.scene.render.fps = 30

    # Add a sun lamp for scene illumination
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.data.objects[-1]
    sun.data.energy = 2.0

    # Add a camera and set it as the active scene camera
    cam_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    camera.location = (10, -15, 8)  # Position the camera
    # Rotate camera to look at the scene origin
    camera.rotation_euler = (math.radians(60), 0, math.radians(35))
    camera.data.lens = 35  # Set a wider field of view

    # Set up world background color
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("World")
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.05, 0.1, 1)  # Dark blue background
    print("Scene setup complete.")

# --- Helper Functions ---
def create_text(name, text_content, location, size=1.0, color=(1,1,1,1)):
    """
    Creates a Blender text object with specified content, location, size, and color.
    """
    font_curve = bpy.data.curves.new(type="FONT", name=name + "_Curve")
    font_curve.body = text_content
    font_curve.extrude = 0.01  # Give text some thickness
    font_curve.resolution_u = 2
    font_curve.align_x = 'CENTER'
    font_curve.align_y = 'CENTER'

    text_obj = bpy.data.objects.new(name, font_curve)
    bpy.context.collection.objects.link(text_obj)
    text_obj.location = location
    text_obj.scale = (size, size, size)

    # Create and assign a material for the text
    mat = bpy.data.materials.new(name="Text_Material_" + name)
    mat.diffuse_color = color
    if hasattr(text_obj.data, 'materials'):
        text_obj.data.materials.append(mat)

    return text_obj

def create_line(name, start_loc, end_loc, radius=0.05, color=(1,1,1,1)):
    """
    Creates a cylinder object representing a line between two points.
    """
    bpy.ops.mesh.primitive_cylinder_add(
        depth=1, enter_editmode=False, align='WORLD',
        location=(0,0,0)
    )
    line_obj = bpy.context.view_layer.objects.active
    line_obj.name = name

    # Calculate direction vector and distance
    direction = Vector(end_loc) - Vector(start_loc)
    distance = direction.length

    # Scale the cylinder along its Z-axis (local length) to match the distance
    line_obj.scale = (radius, radius, distance)

    # Position the cylinder at the midpoint of the line
    line_obj.location = (Vector(start_loc) + Vector(end_loc)) / 2

    # Orient the cylinder to point along the direction vector
    quat = direction.to_track_quat('Z', 'Y') # 'Z' is cylinder's length, 'Y' is its local up
    line_obj.rotation_mode = 'QUATERNION'
    line_obj.rotation_quaternion = quat

    # Create and assign a material for the line
    mat = bpy.data.materials.new(name="Line_Material_" + name)
    mat.diffuse_color = color
    if hasattr(line_obj.data, 'materials'):
        line_obj.data.materials.append(mat)

    return line_obj

def create_arrow(name, start_loc, end_loc, radius=0.05, head_length=0.2, head_radius_factor=2, color=(1,1,1,1)):
    """
    Creates a line with an arrow head at the end.
    Returns both the line object and the arrow head object.
    """
    line = create_line(name + "_Line", start_loc, end_loc, radius, color)

    # Create a cone for the arrow head (Blender 4.x: use radius1, radius2)
    bpy.ops.mesh.primitive_cone_add(
        radius1=radius * head_radius_factor,
        radius2=0.0,
        depth=head_length,
        enter_editmode=False,
        align='WORLD',
        location=(0,0,0)
    )
    arrow_head = bpy.context.view_layer.objects.active
    arrow_head.name = name + "_Head"

    # Position and orient the arrow head at the end of the line
    direction = Vector(end_loc) - Vector(start_loc)
    quat = direction.to_track_quat('Z', 'Y')
    arrow_head.rotation_mode = 'QUATERNION'
    arrow_head.rotation_quaternion = quat
    arrow_head.location = end_loc

    # Create and assign a material for the arrow head
    mat = bpy.data.materials.new(name="Arrow_Material_" + name)
    mat.diffuse_color = color
    if hasattr(arrow_head.data, 'materials'):
        arrow_head.data.materials.append(mat)

    return line, arrow_head

def create_angle_arc(name, center, point1, point2, radius=0.5, segments=32, color=(1,1,1,1)):
    """
    Creates a curved line (arc) to represent an angle.
    The arc is drawn from center towards point1, then sweeping towards point2.
    Assumes the angle lies on the XZ plane for this specific problem (rotation around Y-axis).
    """
    # Calculate vectors from center to points
    vec1 = (Vector(point1) - Vector(center)).normalized()
    vec2 = (Vector(point2) - Vector(center)).normalized()

    # For a triangle on the XZ plane, the rotation axis for the arc is Y.
    rotation_axis = Vector((0,1,0))

    # Calculate the total angle between the two vectors
    angle_total = vec1.angle(vec2, rotation_axis)

    # Create a new curve data block
    curve_data = bpy.data.curves.new(name=name + "_Curve", type='CURVE')
    curve_data.dimensions = '3D'

    # Add a NURBS spline to the curve
    spline = curve_data.splines.new('NURBS')
    spline.points.add(segments + 1) # Add points for the arc

    # Calculate points along the arc
    for i in range(segments + 1):
        factor = i / segments
        current_angle = angle_total * factor

        # Create a quaternion for rotation around the rotation_axis
        quat = Quaternion(rotation_axis, current_angle)

        # Rotate vec1 by current_angle to get the current point direction
        rotated_vec = quat @ vec1

        point_on_arc = Vector(center) + rotated_vec * radius
        spline.points[i].co = (point_on_arc.x, point_on_arc.y, point_on_arc.z, 1)

    # Set curve resolution and add thickness (bevel)
    curve_data.resolution_u = 2
    curve_data.bevel_depth = 0.02
    curve_data.bevel_resolution = 2

    # Create an object from the curve data
    arc_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(arc_obj)

    # Create and assign a material for the arc
    mat = bpy.data.materials.new(name="Arc_Material_" + name)
    mat.diffuse_color = color
    if hasattr(arc_obj.data, 'materials'):
        arc_obj.data.materials.append(mat)

    return arc_obj

def create_axes(scale=10):
    """
    Creates 3D labeled axes (X, Y, Z) and groups them into a collection.
    """
    # X-axis (Red)
    x_axis = create_line("X_Axis", (0,0,0), (scale,0,0), radius=0.02, color=(1,0,0,1))
    x_label = create_text("X_Label", "X", (scale + 0.5, 0, 0), size=0.5, color=(1,0,0,1))

    # Y-axis (Green)
    y_axis = create_line("Y_Axis", (0,0,0), (0,scale,0), radius=0.02, color=(0,1,0,1))
    y_label = create_text("Y_Label", "Y", (0, scale + 0.5, 0), size=0.5, color=(0,1,0,1))

    # Z-axis (Blue)
    z_axis = create_line("Z_Axis", (0,0,0), (0,0,scale), radius=0.02, color=(0,0,1,1))
    z_label = create_text("Z_Label", "Z", (0, 0, scale + 0.5), size=0.5, color=(0,0,1,1))

    # Group axes and labels into a new collection for easier management
    axes_collection = bpy.data.collections.new("Axes_Collection")
    bpy.context.scene.collection.children.link(axes_collection)

    for obj in [x_axis, x_label, y_axis, y_label, z_axis, z_label]:
        bpy.context.collection.objects.unlink(obj) # Unlink from master collection
        axes_collection.objects.link(obj) # Link to new collection
        obj.hide_render = True # Hide initially
        obj.hide_viewport = True

    return axes_collection # Return the collection for animation

def animate_visibility(obj, start_frame, end_frame, visible=True):
    """
    Animates the visibility (hide_render and hide_viewport) of an object.
    """
    # Set initial state at start_frame
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    obj.keyframe_insert(data_path='hide_render', frame=start_frame)
    obj.keyframe_insert(data_path='hide_viewport', frame=start_frame)

    # Set final state at end_frame
    obj.hide_render = not (visible)
    obj.hide_viewport = not (visible)
    obj.keyframe_insert(data_path='hide_render', frame=end_frame)
    obj.keyframe_insert(data_path='hide_viewport', frame=end_frame)

def animate_line_grow(line_obj, start_frame, end_frame):
    """
    Animates a line object to grow from zero length to its full length.
    Assumes the line's length is along its local Z-axis.
    """
    original_scale_z = line_obj.scale.z # Store the original Z scale

    # Set scale.z to 0 at the start frame
    line_obj.scale.z = 0.0
    line_obj.keyframe_insert(data_path='scale', frame=start_frame)

    # Set scale.z to its original value at the end frame
    line_obj.scale.z = original_scale_z
    line_obj.keyframe_insert(data_path='scale', frame=end_frame)

def animate_text_fade_in(text_obj, start_frame, end_frame):
    """
    Animates the alpha (transparency) of a text object's material from 0 to 1.
    Ensures the material uses nodes and a Principled BSDF.
    """
    # Ensure material exists and uses nodes
    if not text_obj.data.materials:
        mat = bpy.data.materials.new(name="TempTextMat_" + text_obj.name)
        mat.use_nodes = True
        text_obj.data.materials.append(mat)

    mat = text_obj.data.materials[0]
    if not mat.use_nodes:
        mat.use_nodes = True # Ensure nodes are used for Principled BSDF

    # Get or create Principled BSDF node
    if "Principled BSDF" not in mat.node_tree.nodes:
        bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], mat.node_tree.nodes['Material Output'].inputs['Surface'])
    else:
        bsdf = mat.node_tree.nodes["Principled BSDF"]

    # Animate alpha input of Principled BSDF
    bsdf.inputs['Alpha'].default_value = 0.0
    bsdf.inputs['Alpha'].keyframe_insert(data_path='default_value', frame=start_frame)

    bsdf.inputs['Alpha'].default_value = 1.0
    bsdf.inputs['Alpha'].keyframe_insert(data_path='default_value', frame=end_frame)

    # Set blend mode to Alpha Blend for transparency to work
    mat.blend_method = 'BLEND'
    # mat.shadow_method = 'NONE' # Prevent shadows from transparent text

# --- Main Animation Logic ---
def create_trigonometry_animation():
    """
    Generates the full Blender scene and animation for the trigonometry problem.
    """
    setup_scene()

    # --- Constants and Scale ---
    # Use a scale factor to convert real-world meters to Blender units for better visualization.
    # 1 Blender unit = 1000 meters, so 3000m becomes 3 units.
    SCALE_FACTOR = 1/1000
    ALTITUDE_M = 3000
    ANGLE_DEG = 30

    altitude_blender_units = ALTITUDE_M * SCALE_FACTOR
    angle_rad = math.radians(ANGLE_DEG)

    # Calculate derived values in Blender units based on trigonometry
    hypotenuse_blender_units = altitude_blender_units / math.sin(angle_rad) # d = 3 / sin(30) = 3 / 0.5 = 6
    ground_distance_blender_units = altitude_blender_units / math.tan(angle_rad) # x = 3 / tan(30) = 3 / (1/sqrt(3)) approx 5.196

    # --- Object Positions ---
    person_loc = Vector((0, 0, 0))
    ground_point_below_plane_loc = Vector((ground_distance_blender_units, 0, 0))
    airplane_loc = Vector((ground_distance_blender_units, 0, altitude_blender_units))

    # --- 2. Ground and Person ---
    # Create a large plane for the ground
    bpy.ops.mesh.primitive_plane_add(size=20, enter_editmode=False, align='WORLD', location=(0, 0, -0.01))
    ground_obj = bpy.data.objects[-1]  # Get the last created object (the plane)
    ground_obj.name = "Ground"
    ground_mat = bpy.data.materials.new(name="Ground_Material")
    ground_mat.diffuse_color = (0.1, 0.3, 0.1, 1) # Greenish ground
    if hasattr(ground_obj.data, 'materials'):
        ground_obj.data.materials.append(ground_mat)

    # Represent the person as a simple cone
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, radius2=0.0, depth=0.5, enter_editmode=False, align='WORLD', location=person_loc)
    person_obj = bpy.data.objects[-1]  # Get the last created object (the cone)
    person_obj.name = "Person"
    person_mat = bpy.data.materials.new(name="Person_Material")
    person_mat.diffuse_color = (0.8, 0.5, 0.2, 1) # Brownish color
    if hasattr(person_obj.data, 'materials'):
        person_obj.data.materials.append(person_mat)

    # --- 3. Airplane ---
    # Create a simple airplane shape using cubes (body and wings)
    bpy.ops.mesh.primitive_cube_add(size=0.5, enter_editmode=False, align='WORLD', location=airplane_loc)
    plane_body = bpy.data.objects[-1]  # Get the last created object (the cube)
    plane_body.name = "Airplane_Body"
    plane_body.scale = (0.2, 0.2, 0.2) # Scale down the body

    bpy.ops.mesh.primitive_cube_add(size=1.5, enter_editmode=False, align='WORLD', location=airplane_loc)
    plane_wings = bpy.data.objects[-1]  # Get the last created object (the cube)
    plane_wings.name = "Airplane_Wings"
    plane_wings.scale = (1, 0.1, 0.1) # Make it flat for wings
    plane_wings.parent = plane_body # Parent wings to body for combined movement

    # Rotate plane to face the person (along the X-axis)
    plane_body.rotation_euler.z = math.radians(90)

    plane_mat = bpy.data.materials.new(name="Airplane_Material")
    plane_mat.diffuse_color = (0.7, 0.7, 0.7, 1) # Grey color
    if hasattr(plane_body.data, 'materials'):
        plane_body.data.materials.append(plane_mat)
    if hasattr(plane_wings.data, 'materials'):
        plane_wings.data.materials.append(plane_mat)

    # --- 4. Triangle Visualization Elements ---
    # Altitude Line (Opposite side)
    altitude_line, altitude_arrow_head = create_arrow("Altitude_Line", ground_point_below_plane_loc, airplane_loc, color=(0.8, 0.2, 0.2, 1)) # Red
    altitude_label = create_text("Altitude_Label", f"{ALTITUDE_M}m", airplane_loc + Vector((0.5, 0, 0)), size=0.5, color=(0.8, 0.2, 0.2, 1))

    # Ground Line (Adjacent side)
    ground_line, ground_arrow_head = create_arrow("Ground_Line", person_loc, ground_point_below_plane_loc, color=(0.2, 0.8, 0.2, 1)) # Green
    ground_label = create_text("Ground_Label", "Adjacent", ground_point_below_plane_loc / 2 + Vector((0, 0, 0.3)), size=0.5, color=(0.2, 0.8, 0.2, 1))

    # Line of Sight (Hypotenuse)
    hypotenuse_line, hypotenuse_arrow_head = create_arrow("Hypotenuse_Line", person_loc, airplane_loc, color=(0.2, 0.2, 0.8, 1)) # Blue
    hypotenuse_label = create_text("Hypotenuse_Label", "d = ?", (person_loc + airplane_loc) / 2 + Vector((0.5, 0, 0.5)), size=0.5, color=(0.2, 0.2, 0.8, 1))

    # Angle of Elevation (Arc and Label)
    # The arc is drawn from a point on the ground line (relative to person) to a point on the hypotenuse line (relative to person)
    angle_arc = create_angle_arc("Angle_Arc", person_loc, person_loc + Vector((1,0,0)), person_loc + Vector((math.cos(angle_rad),0,math.sin(angle_rad))), radius=0.8, color=(0.8, 0.8, 0.2, 1)) # Yellow
    angle_label = create_text("Angle_Label", f"{ANGLE_DEG}°", person_loc + Vector((0.8, 0, 0.4)), size=0.5, color=(0.8, 0.8, 0.2, 1))

    # Solution Text Overlays (positioned to the side of the main scene)
    solution_text_loc = Vector((0, -8, 5)) # Base position for solution text
    solution_texts = []
    solution_texts.append(create_text("Sol_1", "1. Visualize the triangle:", solution_text_loc + Vector((0,0,2)), size=0.7))
    solution_texts.append(create_text("Sol_2", "   Opposite (Altitude) = 3,000m", solution_text_loc + Vector((0,0,1.5)), size=0.6))
    solution_texts.append(create_text("Sol_3", "   Angle (θ) = 30°", solution_text_loc + Vector((0,0,1)), size=0.6))
    solution_texts.append(create_text("Sol_4", "   Hypotenuse (d) = unknown", solution_text_loc + Vector((0,0,0.5)), size=0.6))
    solution_texts.append(create_text("Sol_5", "2. Choose trigonometric ratio:", solution_text_loc + Vector((0,0,-0.5)), size=0.7))
    solution_texts.append(create_text("Sol_6", "   sin(θ) = Opposite / Hypotenuse", solution_text_loc + Vector((0,0,-1)), size=0.6))
    solution_texts.append(create_text("Sol_7", "3. Substitute values:", solution_text_loc + Vector((0,0,-2)), size=0.7))
    solution_texts.append(create_text("Sol_8", "   sin(30°) = 3000 / d", solution_text_loc + Vector((0,0,-2.5)), size=0.6))
    solution_texts.append(create_text("Sol_9", "4. Recall sin(30°):", solution_text_loc + Vector((0,0,-3.5)), size=0.7))
    solution_texts.append(create_text("Sol_10", "   sin(30°) = 0.5", solution_text_loc + Vector((0,0,-4)), size=0.6))
    solution_texts.append(create_text("Sol_11", "5. Solve for 'd':", solution_text_loc + Vector((0,0,-5)), size=0.7))
    solution_texts.append(create_text("Sol_12", "   0.5 = 3000 / d", solution_text_loc + Vector((0,0,-5.5)), size=0.6))
    solution_texts.append(create_text("Sol_13", "   d = 3000 / 0.5", solution_text_loc + Vector((0,0,-6)), size=0.6))
    solution_texts.append(create_text("Sol_14", "   d = 6000 meters", solution_text_loc + Vector((0,0,-6.5)), size=0.6, color=(0.2, 0.8, 0.2, 1)))

    # --- 5. Animation Sequence ---
    frame = bpy.context.scene.frame_start + 10 # Start animation after a brief pause

    # Initial state: Hide all dynamic elements at the very beginning
    elements_to_hide = [
        altitude_line, altitude_arrow_head, altitude_label,
        ground_line, ground_arrow_head, ground_label,
        hypotenuse_line, hypotenuse_arrow_head, hypotenuse_label,
        angle_arc, angle_label,
        person_obj, plane_body, plane_wings
    ]
    for obj in elements_to_hide:
        animate_visibility(obj, frame, frame, visible=False) # Set to hidden at frame 'frame'
    for text_obj in solution_texts:
        animate_visibility(text_obj, frame, frame, visible=False)

    # Show axes: Fade in the axes and their labels
    axes_collection = create_axes(scale=7)
    for obj in axes_collection.objects:
        animate_visibility(obj, frame, frame + 30, visible=True)
    frame += 60 # Pause to view axes

    # Step 1: Introduce the person and the airplane
    animate_visibility(person_obj, frame, frame + 10, visible=True)
    animate_visibility(plane_body, frame, frame + 10, visible=True)
    animate_visibility(plane_wings, frame, frame + 10, visible=True)
    frame += 30

    # Animate the altitude line growing and its label appearing
    animate_line_grow(altitude_line, frame, frame + 20)
    animate_visibility(altitude_arrow_head, frame + 20, frame + 20, visible=True) # Make arrow head visible when line is done
    animate_text_fade_in(altitude_label, frame + 20, frame + 30)
    frame += 40

    # Animate the ground line growing and its label appearing
    animate_line_grow(ground_line, frame, frame + 20)
    animate_visibility(ground_arrow_head, frame + 20, frame + 20, visible=True)
    animate_text_fade_in(ground_label, frame + 20, frame + 30)
    frame += 40

    # Animate the hypotenuse line growing and its label appearing
    animate_line_grow(hypotenuse_line, frame, frame + 20)
    animate_visibility(hypotenuse_arrow_head, frame + 20, frame + 20, visible=True)
    animate_text_fade_in(hypotenuse_label, frame + 20, frame + 30)
    frame += 40

    # Animate the angle arc growing and its label appearing
    # For curve objects, animate bevel_depth to make them grow
    original_bevel_depth = angle_arc.data.bevel_depth
    angle_arc.data.bevel_depth = 0.0
    angle_arc.data.keyframe_insert(data_path='bevel_depth', frame=frame)
    angle_arc.data.bevel_depth = original_bevel_depth
    angle_arc.data.keyframe_insert(data_path='bevel_depth', frame=frame + 20)
    animate_text_fade_in(angle_label, frame + 20, frame + 30)
    frame += 40

    # Display "Visualize the triangle" text and knowns
    animate_text_fade_in(solution_texts[0], frame, frame + 10)
    animate_text_fade_in(solution_texts[1], frame + 10, frame + 20)
    animate_text_fade_in(solution_texts[2], frame + 20, frame + 30)
    animate_text_fade_in(solution_texts[3], frame + 30, frame + 40)
    frame += 60 # Pause for text

    # Step 2: Display "Choose trigonometric ratio" and formula
    animate_text_fade_in(solution_texts[4], frame, frame + 10)
    animate_text_fade_in(solution_texts[5], frame + 10, frame + 20)
    frame += 40

    # Step 3: Display "Substitute values" and formula with values
    animate_text_fade_in(solution_texts[6], frame, frame + 10)
    animate_text_fade_in(solution_texts[7], frame + 10, frame + 20)
    frame += 40

    # Step 4: Display "Recall sin(30°)" and its value
    animate_text_fade_in(solution_texts[8], frame, frame + 10)
    animate_text_fade_in(solution_texts[9], frame + 10, frame + 20)
    frame += 40

    # Step 5: Display "Solve for 'd'" and the solution steps
    animate_text_fade_in(solution_texts[10], frame, frame + 10)
    animate_text_fade_in(solution_texts[11], frame + 10, frame + 20)
    animate_text_fade_in(solution_texts[12], frame + 20, frame + 30)
    animate_text_fade_in(solution_texts[13], frame + 30, frame + 40)

    # Update the hypotenuse label with the calculated value
    hypotenuse_label.data.body = f"d = {int(hypotenuse_blender_units * (1/SCALE_FACTOR))}m"
    animate_text_fade_in(hypotenuse_label, frame + 30, frame + 40) # Ensure it's visible with new text

    frame += 60 # Final pause to view the solution

    # Set the final frame of the animation
    bpy.context.scene.frame_end = frame + 30

    print("Animation script finished.")

# Run the animation creation function when the script is executed
if __name__ == "__main__":
    create_trigonometry_animation()