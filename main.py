from viewerGL import ViewerGL
import glutils
from mesh import Mesh
from cpe3d import Object3D, Camera, Transformation3D, Text
import numpy as np
import OpenGL.GL as GL
import pyrr

def main():
    viewer = ViewerGL()

    viewer.set_camera(Camera())
    viewer.cam.transformation.translation.y = 2
    viewer.cam.transformation.rotation_center = viewer.cam.transformation.translation.copy()

    program3d_id = glutils.create_program_from_file('shader.vert', 'shader.frag')
    programGUI_id = glutils.create_program_from_file('gui.vert', 'gui.frag')

    m = Mesh.load_obj('SpaceShip.obj')
    m.normalize()
    m.apply_matrix(pyrr.matrix44.create_from_scale([1.3, 1.3, -1.3, 1]))
    tr = Transformation3D()
    tr.translation.y = -np.amin(m.vertices, axis=0)[1]
    tr.translation.z = -5
    tr.rotation_center.z = 0.2
    texture = glutils.load_texture('SpaceShip_couleur.jpg')
    o = Object3D(m.load_to_gpu(), m.get_nb_triangles(), program3d_id, texture, tr)
    viewer.add_object(o)

    m = Mesh.load_obj('cylindre.obj')
    m.normalize()
    m.apply_matrix(pyrr.matrix44.create_from_scale([70, 70, 50, 1]))
    texture = glutils.load_texture('Space.jpg')
    vaoSol=m.load_to_gpu()
    nbTriangle=m.get_nb_triangles()
    for i in range(0,2):
        trSol= Transformation3D()
        trSol.translation.z= -100*i
        o = Object3D(vaoSol, nbTriangle, program3d_id, texture,trSol)
        viewer.add_object(o)
    
    m = Mesh.load_obj('dsphere.obj')
    m.normalize()
    m.apply_matrix(pyrr.matrix44.create_from_scale([13, 13,13, 1]))
    texture = glutils.load_texture('Space.jpg')
    vaoSol=m.load_to_gpu()
    nbTriangle=m.get_nb_triangles()
    trSol= Transformation3D()
    trSol.translation.z= -90
    o = Object3D(vaoSol, nbTriangle, program3d_id, texture,trSol)
    viewer.add_object(o)

    m= Mesh.load_obj('Asteroid.obj')
    m.normalize()
    m.apply_matrix(pyrr.matrix44.create_from_scale([1.7, 1.7, -1.7, 1]))
    texture = glutils.load_texture('Asteroid2.png')
    nbTriangle=m.get_nb_triangles()
    vaoAste=m.load_to_gpu()
    for i in range(0,10):
        trAste=Transformation3D()
        trAste.translation.y=0.5
        trAste.translation.x=-5.5
        trAste.translation.z= -10*i
        o = Object3D(vaoAste, nbTriangle, program3d_id, texture,trAste)
        viewer.add_object(o)
    for i in range(0,10):
        trAste=Transformation3D()
        trAste.translation.y=0.5
        trAste.translation.x=5.5
        trAste.translation.z= -10*i
        o = Object3D(vaoAste, nbTriangle, program3d_id, texture,trAste)
        viewer.add_object(o)
    
    vao = Text.initalize_geometry()
    texture = glutils.load_texture('fontB.png')

    o = Text('###', np.array([-0.95,0.8], np.float32), np.array([-0.65,0.95], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    o = Text("HIGHSCORE : ", np.array([0.55, 0.8], np.float32), np.array([0.85, 0.95], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    o = Text(str(viewer.highscore), np.array([0.90, 0.79], np.float32), np.array([0.95, 0.94], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    o = Text("SCORE : ", np.array([0.65, 0.7], np.float32), np.array([0.85, 0.85], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    o = Text(str(viewer.score), np.array([0.90, 0.69], np.float32), np.array([0.95, 0.84], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    o = Text('SPACE TO START', np.array([-0.5, -0.2], np.float32), np.array([0.5, 0.2], np.float32), vao, 2, programGUI_id, texture)
    viewer.add_object(o)

    
    viewer.run()

if __name__ == '__main__':
    main()
     