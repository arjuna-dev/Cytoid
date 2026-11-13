"""Original Kiirtaniyas art. Run stages through Blender MCP, not system Python.

Scene is isolated from any open user scene. Exported models use meter units.
"""
import bpy
import math
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'engines/unity/Assets/Kiirtaniyas/Art/Models'
SCENE_NAME = 'Kiirtaniyas_MVP'


def material(name, color, metallic=0.0, emission=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = 0.65
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m


def palette():
    return {n: material('KU_' + n, c, *extra) for n, c, *extra in [
        ('Sandstone', (0.46, 0.30, 0.19)), ('StoneLight', (0.66, 0.48, 0.30)),
        ('StoneRose', (0.52, 0.32, 0.25)), ('Plaster', (0.78, 0.64, 0.42)),
        ('Wood', (0.19, 0.075, 0.035)), ('Cloth', (0.93, 0.78, 0.51)),
        ('Saffron', (0.91, 0.29, 0.045)), ('Teal', (0.045, 0.34, 0.31)),
        ('Skin', (0.67, 0.35, 0.16)), ('SkinLight', (0.91, 0.57, 0.29)),
        ('Hair', (0.055, 0.024, 0.016)), ('Blush', (0.91, 0.30, 0.22)),
        ('Mouth', (0.18, 0.035, 0.025)), ('Gold', (0.8, 0.43, 0.09), 0.55),
        ('Leaf', (0.10, 0.29, 0.095)), ('LeafLight', (0.27, 0.43, 0.12)),
        ('Flower', (0.91, 0.13, 0.21)), ('FlowerGold', (1, 0.52, 0.055)),
        ('Flame', (1, 0.59, 0.13), 0, 3.0), ('Night', (0.025, 0.035, 0.08))]}


def empty(name, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def finish(o, name, mat, parent):
    o.name = name
    if mat:
        o.data.materials.append(mat)
    o.parent = parent
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def sphere(name, pos, scale, mat, parent, seg=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=pos)
    o = bpy.context.object
    o.scale = scale
    return finish(o, name, mat, parent)


def box(name, pos, scale, mat, parent, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Soft edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(o, name, mat, parent)


def cylinder(name, pos, radius, depth, mat, parent, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos)
    return finish(bpy.context.object, name, mat, parent)


def rod(name, a, b, radius, mat, parent):
    a, b = Vector(a), Vector(b)
    o = cylinder(name, (a + b) / 2, radius, (b - a).length, mat, parent, 12)
    o.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return o


def capsule(name,a,b,radius,mat,parent):
    a,b=Vector(a),Vector(b)
    obj=sphere(name,(a+b)/2,(radius,radius,(b-a).length/2+radius),mat,parent,20,12)
    obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return obj


def line(name, points, radius, mat, parent, cyclic=False):
    c = bpy.data.curves.new(name, 'CURVE')
    c.dimensions = '3D'
    c.bevel_depth = radius
    c.bevel_resolution = 2
    s = c.splines.new('POLY')
    s.points.add(len(points)-1)
    for p, v in zip(s.points, points):
        p.co = (*v, 1)
    s.use_cyclic_u = cyclic
    o = bpy.data.objects.new(name, c)
    bpy.context.scene.collection.objects.link(o)
    return finish(o, name, mat, parent)


def setup():
    if bpy.data.scenes.get(SCENE_NAME):
        raise RuntimeError('MVP scene already exists; reuse stage functions or explicitly remove it before rebuilding.')
    scene = bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new('KU_Evening')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.085, 0.10, 0.15, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = 0.45
    scene.view_settings.view_transform = 'AgX'
    palette()


def courtyard():
    m = palette()
    root = empty('Courtyard')
    cylinder('Courtyard_Foundation', (0, 0, -0.22), 4.9, 0.38, m['Sandstone'], root, 64)
    cylinder('Courtyard_Paving', (0, 0, -0.045), 4.75, 0.08, m['StoneLight'], root, 64)
    rng = random.Random(40)
    # Concentric individually bevelled pavers retain readable hand-built stonework.
    for ring in range(1, 9):
        r0 = ring * 0.5
        count = max(12, round(2 * math.pi * r0 / 0.48))
        for i in range(count):
            a = 2 * math.pi * (i + (ring % 2)*0.5) / count
            o = box('Paver', (r0*math.cos(a), r0*math.sin(a), 0.008),
                    (0.46, 2*math.pi*r0/count-0.025, 0.045),
                    m[rng.choice(['StoneLight', 'StoneLight', 'Sandstone', 'StoneRose'])], root, 0.025)
            o.rotation_euler.z = a
    for x in [-0.63, 0.63]:
        for y in [-0.63, 0.63]:
            box('Table_Leg', (x,y,0.36), (0.16,0.16,0.7), m['Wood'], root)
    box('Table_Top', (0,0,0.74), (1.75,1.75,0.16), m['Wood'], root)
    box('Table_Cloth', (0,0,0.835), (1.8,1.8,0.07), m['Cloth'], root)
    for y in [-0.89,0.89]:
        box('Table_Cloth_Drape', (0,y,0.72), (1.81,0.035,0.27), m['Cloth'], root, 0.012)
        box('Table_Cloth_Border', (0,y*1.02,0.615), (1.81,0.025,0.055), m['Saffron'], root, 0.009)
    cylinder('Lamp_Base', (0,0,0.91),0.24,0.07,m['Gold'],root)
    sphere('Lamp_Bowl',(0,0,0.96),(0.19,0.19,0.095),m['Gold'],root)
    sphere('Lamp_Flame',(0,0,1.10),(0.035,0.035,0.13),m['Flame'],root)
    for i in range(12):
        a=i*math.tau/12
        flower((0.5*math.cos(a),0.5*math.sin(a),0.90),root,m,i)
    # Open backdrop frames the gathering without closing off future crowd rings.
    for x in [-3.6,3.6]:
        box('Gate_Pillar',(x,2.5,1.35),(0.42,0.42,2.7),m['Plaster'],root)
        box('Gate_Cap',(x,2.5,2.72),(0.56,0.56,0.15),m['Sandstone'],root)
        box('Low_Garden_Wall',(x,1.5,0.37),(0.27,1.8,0.74),m['Plaster'],root)
    points=[(-3.6+i*7.2/24,2.5,2.85-0.5*math.sin(math.pi*i/24)) for i in range(25)]
    line('Festoon_Cord',points,0.017,m['Wood'],root)
    for i in range(13):
        x=-3.4+i*6.8/12
        z=2.85-0.5*math.sin(math.pi*(x+3.6)/7.2)
        sphere('Warm_Bulb',(x,2.5,z-0.09),(0.05,0.05,0.075),m['Flame'],root,12,8)
    for idx,(x,y) in enumerate([(-3.6,1.5),(3.6,1.5),(-3.2,2.8),(3.2,2.8),(-3.9,-0.9),(3.9,-0.8)]):
        cylinder('Terracotta_Pot',(x,y,0.25),0.27,0.5,m['StoneRose'],root)
        cylinder('Pot_Rim',(x,y,0.5),0.3,0.09,m['Sandstone'],root)
        for j in range(7):
            a=j*math.tau/7
            pos=(x+0.19*math.cos(a),y+0.19*math.sin(a),0.7+0.1*(j%3))
            leaf=sphere('Garden_Leaf',pos,(0.1,0.31,0.095),m['Leaf' if j%2 else 'LeafLight'],root,12,8)
            leaf.rotation_euler=(0.45,0,a-math.pi/2)
        flower((x,y,0.99),root,m,idx)
    # A broad garden apron fills the portrait composition while the table stays close.
    cylinder('Garden_Apron',(0,0,-0.29),7.3,0.24,m['Sandstone'],root,64)
    for idx in range(18):
        a=idx*math.tau/18
        x,y=6.2*math.cos(a),6.2*math.sin(a)
        sphere('Garden_Bed',(x,y,-0.11),(0.78,0.62,0.22),m['Wood'],root,12,8)
        for j in range(3):
            px=x+0.34*math.cos(j*math.tau/3)
            py=y+0.30*math.sin(j*math.tau/3)
            sphere('Round_Shrub',(px,py,0.20),(0.42,0.39,0.37),m['LeafLight' if j%2 else 'Leaf'],root,12,8)
        flower((x,y,0.57),root,m,idx)
        if idx%3==0:
            cylinder('Garden_Lantern_Base',(x,y,0.68),0.11,0.14,m['Gold'],root,12)
            sphere('Garden_Lantern',(x,y,0.82),(0.12,0.12,0.17),m['Flame'],root,12,8)
    for side in [-1,1]:
        x,y=side*4.8,4.0
        rod('Tree_Trunk',(x,y,0),(x,y,2.5),0.16,m['Wood'],root)
        for j in range(4):
            a=j*math.tau/4
            sphere('Tree_Canopy',(x+0.47*math.cos(a),y+0.47*math.sin(a),2.6+(j%2)*0.35),
                   (0.85,0.76,0.75),m['LeafLight' if j%2 else 'Leaf'],root,12,8)
    for side in [-1,1]:
        x,y=side*4.8,-2.7
        box('Garden_Bench',(x,y,0.50),(1.3,0.43,0.13),m['Wood'],root)
        for dx in [-0.44,0.44]:
            box('Bench_Leg',(x+dx,y,0.23),(0.15,0.32,0.46),m['Wood'],root)
    return root


def flower(pos, parent, m, index):
    x,y,z=pos
    for j in range(5):
        a=j*math.tau/5
        sphere('Petal',(x+0.075*math.cos(a),y+0.075*math.sin(a),z),
               (0.065,0.065,0.025),m['Flower' if index%2 else 'FlowerGold'],parent,10,6)
    sphere('Flower_Centre',(x,y,z+0.017),(0.04,0.04,0.025),m['Gold'],parent,10,6)


def singer(name, joined=False):
    """Reference-led egg silhouette, with texture-only blush and no cheek meshes."""
    m=palette()
    root=empty(name)
    root['pose']='joined_palms' if joined else 'raised_hands'
    root['forward_blender']='-Y'
    root['ground_z']=0.0
    skin=material('KU_SkinJoined' if joined else 'KU_SkinRaised',
                  (0.60,0.345,0.18) if joined else (0.79,0.49,0.25))
    p=skin.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value=0.53
    p.inputs['Subsurface Weight'].default_value=0.07
    cloth=m['Teal' if joined else 'Saffron']
    body=empty(name+'_Body',root)
    tunic=sphere('Egg_Tunic',(0,0,0.62),(0.575,0.515,0.565),cloth,body,32,20)
    # A broad belly and tapered crown read as a single bundled, legless figure.
    for v in tunic.data.vertices:
        factor=1.0-0.16*v.co.z
        v.co.x*=factor
        v.co.y*=factor
    for z in [0.28,0.31]:
        q=(z-0.62)/0.565
        r=0.575*math.sqrt(1-q*q)*(1-0.16*q)+0.006
        depth=0.515*math.sqrt(1-q*q)*(1-0.16*q)+0.006
        line('Woven_Hem',[(r*math.cos(a),depth*math.sin(a),z) for a in
             [i*math.tau/64 for i in range(64)]],0.009,m['Cloth'],body,True)
    sphere('Soft_Collar',(0,-0.035,1.035),(0.40,0.38,0.07),m['Cloth'],body,24,10)
    for z in [0.53,0.67,0.81]:
        y=-0.515*math.sqrt(max(0,1-((z-0.62)/0.565)**2))*(1-0.16*(z-0.62)/0.565)
        sphere('Tunic_Button',(0,y-0.008,z),(0.019,0.009,0.019),m['Gold'],body,10,6)
    for side in [-1,1]:
        leg=empty(name+('_Leg_L' if side<0 else '_Leg_R'),root)
        x=side*0.19
        sphere('Peeking_Foot',(x,-0.115,0.07),(0.125,0.19,0.07),m['Wood'],leg,16,10)
        pivot(leg,(x,0,0.15))
    head=empty(name+'_Head',body)
    face=sphere('Round_Face',(0,-0.035,1.30),(0.535,0.50,0.505),skin,head,40,24)
    face.data.materials.clear()
    face.data.materials.append(face_material(name,skin))
    uv=face.data.uv_layers.active
    for poly in face.data.polygons:
        coords=[]
        for li in poly.loop_indices:
            v=face.data.vertices[face.data.loops[li].vertex_index].co
            coords.append((li,math.atan2(v.x,-v.y)/math.tau+0.5,math.asin(max(-1,min(1,v.z)))/math.pi+0.5))
        seam=max(c[1] for c in coords)-min(c[1] for c in coords)>0.5
        for li,u,v in coords:
            uv.data[li].uv=(u+1 if seam and u<0.5 else u,v)
    hair_cap(head,m['Hair'])
    sphere('Hair_Bun',(0.02,0.105,1.82),(0.13,0.13,0.115),m['Hair'],head,20,12)
    for i in range(5):
        a=i*math.tau/5
        sphere('Bun_Curl',(0.02+0.078*math.cos(a),0.105+0.078*math.sin(a),1.85),
               (0.065,0.060,0.065),m['Hair'],head,12,8)
    for x in [-0.516,0.516]:
        sphere('Ear',(x,-0.017,1.26),(0.071,0.078,0.094),skin,head,16,10)
    sphere('Button_Nose',(0,-0.536,1.305),(0.047,0.032,0.041),skin,head,16,10)
    # Facial curves conform to the round head instead of hovering on cheek bulges.
    for x in [-0.178,0.178]:
        points=[face_point(x-0.063+i*0.0126,1.414-0.033*math.sin(math.pi*i/10)) for i in range(11)]
        line('Happy_Closed_Eye',points,0.010,m['Hair'],head)
        points=[face_point(x-0.059+i*0.0118,1.506+0.018*math.sin(math.pi*i/10)) for i in range(11)]
        line('Expressive_Brow',points,0.009,m['Hair'],head)
    face_patch('Singing_Smile',0,1.198,0.078,0.076,m['Mouth'],head)
    face_patch('Smile_Tongue',0,1.16,0.041,0.019,m['Blush'],head,0.004)
    for side in [-1,1]:
        shoulder=(side*0.46,-0.015,0.97)
        elbow=(side*(0.42 if joined else 0.64),-0.31 if joined else -0.015,0.91 if joined else 1.23)
        palm=(side*(0.055 if joined else 0.67),-0.60 if joined else -0.04,1.075 if joined else 1.54)
        arm=empty(name+('_Arm_L' if side<0 else '_Arm_R'),body)
        capsule('Soft_Sleeve',shoulder,elbow,0.145,cloth,arm)
        capsule('Soft_Forearm',elbow,palm,0.083,skin,arm)
        sphere('Mitten_Palm',palm,(0.049 if joined else 0.086,0.075,0.123),skin,arm,20,12)
        if not joined:
            sphere('Thumb',(palm[0]-side*0.075,palm[1]-0.006,palm[2]-0.015),(0.037,0.044,0.052),skin,arm,12,8)
        pivot(arm,shoulder)
    pivot(head,(0,0,1.03))
    pivot(body,(0,0,0.38))
    dance(root,joined)
    return root


def face_point(x,z,offset=0.003):
    y=-0.035-0.50*math.sqrt(max(0.001,1-(x/0.535)**2-((z-1.30)/0.505)**2))
    return (x,y-offset,z)


def face_patch(name,x,z,rx,rz,mat,parent,offset=0.002):
    points=[face_point(x,z,offset)]
    for i in range(32):
        a=i*math.tau/32
        points.append(face_point(x+rx*math.cos(a),z+rz*math.sin(a),offset))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(points,[],[(0,1+i,1+(i+1)%32) for i in range(32)])
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    return finish(obj,name,mat,parent)


def face_material(name,skin):
    """Bake smooth Gaussian blush into a small portable albedo, with no decals."""
    import numpy as np
    raised=name=='SingerRaised'
    tag='Raised' if raised else 'Joined'
    mat=bpy.data.materials.get('KU_Face'+tag)
    if mat is None:
        mat=skin.copy()
        mat.name='KU_Face'+tag
    width,height=512,256
    u,v=np.meshgrid((np.arange(width)+0.5)/width,(np.arange(height)+0.5)/height)
    theta=(u-0.5)*math.tau
    phi=(v-0.5)*math.pi
    x=np.sin(theta)*np.cos(phi)
    y=-np.cos(theta)*np.cos(phi)
    z=np.sin(phi)
    amount=np.zeros_like(x)
    for cx in [-0.52,0.52]:
        amount+=np.exp(-0.5*((x-cx)/0.16)**2-0.5*((z+0.07)/0.115)**2)
    amount*=np.clip((-y-0.15)/0.55,0,1)*0.47
    base=np.array(skin.diffuse_color[:3])
    blush=np.array((0.76,0.20,0.135) if raised else (0.60,0.17,0.105))
    rgb=base[None,None,:]*(1-amount[:,:,None])+blush[None,None,:]*amount[:,:,None]
    rgb=np.where(rgb<=0.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-0.055)
    rgba=np.concatenate((rgb,np.ones((height,width,1))),axis=2).astype(np.float32)
    image=bpy.data.images.get('KU_Face'+tag+'_Albedo') or bpy.data.images.new('KU_Face'+tag+'_Albedo',width,height,alpha=True)
    image.pixels.foreach_set(rgba.ravel())
    texture_dir=OUT.parent/'Textures'
    texture_dir.mkdir(parents=True,exist_ok=True)
    image.filepath_raw=str(texture_dir/('KU_Face'+tag+'_Albedo.png'))
    image.file_format='PNG'
    image.save()
    image.pack()
    tex=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'),None) or mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=image
    mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    return mat


def hair_cap(parent,mat):
    """A fitted cap with a receding curved hairline leaves the round forehead open."""
    vertices=[]
    segments,rings=40,10
    for j in range(rings+1):
        for i in range(segments):
            a=i*math.tau/segments
            front=max(0,-math.sin(a))
            extent=1.61-0.93*front
            phi=0.015+(extent-0.015)*j/rings
            vertices.append((0.54*math.sin(phi)*math.cos(a),-0.035+0.505*math.sin(phi)*math.sin(a),1.30+0.509*math.cos(phi)))
    faces=[]
    for j in range(rings):
        for i in range(segments):
            n=(i+1)%segments
            faces.append((j*segments+i,j*segments+n,(j+1)*segments+n,(j+1)*segments+i))
    mesh=bpy.data.meshes.new('Fitted_Hair')
    mesh.from_pydata(vertices,[],faces)
    obj=bpy.data.objects.new('Fitted_Hair',mesh)
    bpy.context.scene.collection.objects.link(obj)
    finish(obj,'Fitted_Hair',mat,parent)


def pivot(obj, position):
    """Move an empty pivot while preserving its children's rest positions."""
    delta=Vector(position)-obj.location
    obj.location=position
    for child in obj.children:
        child.location-=delta


def dance(root, joined):
    """Two-beat, in-place lalita marmika interpretation; Unity owns travel."""
    scene=bpy.context.scene
    scene.render.fps=30
    scene.frame_start=1
    scene.frame_end=37
    root['animation']='LalitaMarmika: alternating soft steps, lateral lean, raised arms'
    for obj in root.children_recursive:
        if obj.type!='EMPTY':
            continue
        base=obj.location.copy()
        for frame in range(1,38,3):
            phase=math.tau*(frame-1)/36
            sway=math.sin(phase)
            obj.rotation_euler=(0,0,0)
            obj.location=base
            if obj.name.endswith('_Body'):
                obj.rotation_euler.y=math.radians(9)*sway
                obj.rotation_euler.z=math.radians(3)*sway
                obj.location.x+=0.045*sway
                obj.location.z+=0.025*(1-math.cos(phase*2))
            elif obj.name.endswith('_Head'):
                obj.rotation_euler.y=math.radians(-4)*math.sin(phase-0.25)
                obj.rotation_euler.x=math.radians(3)*math.sin(phase*2)
            elif '_Arm_' in obj.name and not joined:
                obj.rotation_euler.y=math.radians(5)*math.sin(phase-0.35)
            elif '_Leg_' in obj.name:
                side=-1 if obj.name.endswith('_L') else 1
                lift=max(0,side*sway)
                obj.location.z+=0.075*lift
                obj.location.y-=0.07*side*sway
                obj.rotation_euler.x=math.radians(10)*side*sway
            obj.keyframe_insert(data_path='location',frame=frame)
            obj.keyframe_insert(data_path='rotation_euler',frame=frame)
        if obj.animation_data and obj.animation_data.action:
            obj.animation_data.action.name=root.name+'_'+obj.name+'_LalitaMarmika'
            for curve in obj.animation_data.action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation='BEZIER'
                curve.modifiers.new('CYCLES')
    scene.frame_set(1)


def presentation():
    scene=bpy.context.scene
    raised=bpy.data.objects['SingerRaised']
    joined=bpy.data.objects['SingerJoined']
    raised.location=(-1.65,-1.22,0.04)
    raised.rotation_euler.z=-0.45
    joined.location=(1.65,0.30,0.04)
    joined.rotation_euler.z=0.60
    path=empty('ClockwiseOrbit_Guide')
    path['radius_m']=2.1
    path['direction']='Clockwise when viewed from above; decreasing Blender Z angle'
    path.empty_display_type='CIRCLE'
    path.empty_display_size=2.1
    path.hide_render=True
    bpy.ops.object.camera_add(location=(7,-10,9))
    camera=bpy.context.object
    camera.name='Intimate_Isometric'
    camera.rotation_euler=(Vector((0,0,0.5))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO'
    camera.data.ortho_scale=15
    scene.camera=camera
    for name,loc,power,color,size in [('Golden_Key',(-3,-4,7),1000,(1,0.70,0.40),5),('Heavenly_Rim',(2,4,6),1300,(0.59,0.70,1),4),('Soft_Fill',(4,-2,3),300,(1,0.82,0.64),4)]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        o=bpy.context.object
        o.name=name
        o.data.energy=power
        o.data.color=color
        o.data.shape='DISK'
        o.data.size=size
        o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type='POINT',location=(0,0,1.25))
    bpy.context.object.name='Table_Warmth'
    bpy.context.object.data.energy=15
    bpy.context.object.data.color=(1,0.38,0.08)
    scene.frame_end=37
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
    scene.render.filepath=str(ROOT/'art/blender/mvp_preview.png')


def character_preview(side=False):
    """Render a close, neutral inspection view of both silhouettes and materials."""
    scene=bpy.context.scene
    camera=scene.camera
    old_camera=(camera.location.copy(),camera.rotation_euler.copy(),camera.data.ortho_scale)
    old_resolution=(scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath)
    states=[]
    for name in ['SingerRaised','SingerJoined']:
        obj=bpy.data.objects[name]
        states.append((obj,obj.location.copy(),obj.rotation_euler.copy()))
    bpy.data.objects['SingerRaised'].location=(-0.86,0,0.04)
    bpy.data.objects['SingerRaised'].rotation_euler.z=-0.12
    bpy.data.objects['SingerJoined'].location=(0.90,0,0.04)
    bpy.data.objects['SingerJoined'].rotation_euler.z=1.45 if side else 0.38
    hidden=[]
    for obj in [bpy.data.objects['Courtyard'],*bpy.data.objects['Courtyard'].children_recursive]:
        hidden.append((obj,obj.hide_render))
        obj.hide_render=True
    floor=box('Inspection_Floor',(0,0,-0.01),(200,200,0.1),material('KU_Inspection',(0.135,0.16,0.16)),None,0)
    camera.location=(2.4,-7,3.2)
    camera.rotation_euler=(Vector((0,0,0.96))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=4.2
    scene.render.resolution_x=1600
    scene.render.resolution_y=1100
    scene.cycles.samples=64
    scene.cycles.use_denoising=True
    scene.render.filepath=str(ROOT/'art/blender'/('character_side_pass.png' if side else 'character_reference_pass.png'))
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(floor,do_unlink=True)
    for obj,hidden_before in hidden:
        obj.hide_render=hidden_before
    for obj,loc,rot in states:
        obj.location=loc
        obj.rotation_euler=rot
    camera.location,camera.rotation_euler,camera.data.ortho_scale=old_camera
    scene.render.resolution_x,scene.render.resolution_y,scene.render.filepath=old_resolution


def export(names=('Courtyard','SingerRaised','SingerJoined')):
    OUT.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    for name in names:
        root=bpy.data.objects[name]
        loc,rot=root.location.copy(),root.rotation_euler.copy()
        root.location=(0,0,0)
        root.rotation_euler=(0,0,0)
        bpy.ops.object.select_all(action='DESELECT')
        objects=[root,*root.children_recursive]
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active=root
        # Convert curves in a temporary duplicate hierarchy for FBX compatibility.
        bpy.ops.object.duplicate()
        duplicates=list(bpy.context.selected_objects)
        for o in duplicates:
            if o.type=='CURVE':
                bpy.context.view_layer.objects.active=o
                o.select_set(True)
        bpy.ops.object.convert(target='MESH')
        # Batch surfaces by material within each transform group. The courtyard
        # exports as a few meshes, while head and arm groups remain poseable.
        exported=list(bpy.context.selected_objects)
        groups={}
        for o in exported:
            if o.type=='MESH':
                key=(o.parent.name if o.parent else '',o.active_material.name if o.active_material else '')
                groups.setdefault(key,[]).append(o)
        for group in groups.values():
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:
                o.select_set(True)
            bpy.context.view_layer.objects.active=group[0]
            if len(group)>1:
                bpy.ops.object.join()
            group[0].name='Surface_'+(group[0].active_material.name if group[0].active_material else 'Default')
            bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        # The duplicated root is the only empty without a parent.
        duplicate_root=next(o for o in duplicates if o.type=='EMPTY' and o.parent is None)
        duplicate_root.select_set(True)
        for o in duplicate_root.children_recursive:
            o.select_set(True)
        bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,
            object_types={'EMPTY','MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z',axis_up='Y',bake_anim=name!='Courtyard',
            bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
            bake_anim_simplify_factor=0,add_leaf_bones=False,use_mesh_modifiers=True,
            path_mode='COPY',embed_textures=True)
        bpy.ops.object.delete()
        root.location=loc
        root.rotation_euler=rot
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/blender/kiirtaniyas_mvp.blend'))
    print('Saved source and three FBX models to',OUT)
