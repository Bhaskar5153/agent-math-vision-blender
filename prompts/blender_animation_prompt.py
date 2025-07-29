def get_blender_animation_prompt(solution: str) -> str:
    return (
        "You are a **Blender Python animation expert** using only **Blender 4.4.3+ APIs**.\n"
        "Create a fully functional and educational animation of the student's math solution below.\n\n"
        f"Solution:\n{solution}\n\n"
        " Requirements:\n"
        "+ Use correct, updated `bpy` methods compatible with Blender 4.4.3+.\n"
        "+ Never rely on `bpy.context.active_object`. Always store object references explicitly (e.g., `obj = bpy.context.object`, or use `bpy.data.objects.new`).\n"
        "+ After creating any object, ensure `obj.hide_render = False` to make it visible in final renders.\n"
        "+ All objects (meshes, curves, text, camera, lights) must be visible both in viewport and render.\n"
        "+ Create labeled X, Y, Z axes using `Empty` or `Curve` objects.\n"
        "+ Select appropriate Blender primitives based on context — use Sphere, Plane, Armature, Rigid Body, Force Field, etc., where relevant to the math or physics.\n"
        "+ Animate object transformations using `.keyframe_insert()` (location, rotation, scale).\n"
        "+ Add camera and lights that ensure clear visibility and focus on animated elements.\n"
        "+ Comment each section: object creation, animation, labeling, camera setup, lighting.\n"
        "+ End with a timestamp comment (e.g. `# Generated: YYYY-MM-DD HH:MM`).\n\n"
        "🔒 Output constraints:\n"
        "**Return runnable Python code only — no markdown, no explanation. The code must be clean, well-commented, and executable in Blender 4.4.3+.**"
    )
