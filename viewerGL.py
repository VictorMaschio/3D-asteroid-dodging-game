#!/usr/bin/env python3
import OpenGL.GL as GL
import glfw
import pyrr
import numpy as np
from mesh import Mesh
from cpe3d import Object3D, Camera, Transformation3D, Text
import glutils
import time
import random
from cpe3d import Object3D

class ViewerGL:
    def __init__(self):
        # initialisation de la librairie GLFW
        glfw.init()
        # paramétrage du context OpenGL
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        # création et paramétrage de la fenêtre
        glfw.window_hint(glfw.RESIZABLE, False)
        self.window = glfw.create_window(1600, 900, 'OpenGL', None, None)
        # paramétrage de la fonction de gestion des évènements
        glfw.set_key_callback(self.window, self.key_callback)
        # activation du context OpenGL pour la fenêtre
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        # activation de la gestion de la profondeur
        GL.glEnable(GL.GL_DEPTH_TEST)
        # choix de la couleur de fond
        GL.glClearColor(0.5, 0.6, 0.9, 1.0)
        print(f"OpenGL: {GL.glGetString(GL.GL_VERSION).decode('ascii')}")

        self.objs = []
        self.touch = {}
        
        self.dz = 0.5
        self.dx = 0

        self.sem = 1

        self.objs_mechant = []
        
        self.nb_objs_niveau = [0,0]
        self.niveau = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],[1,1,0,0],[0,1,1,0],[0,0,1,1],[1,0,0,1],[1,0,1,0],[0,1,0,1],[1,1,1,0],[0,1,1,1],[1,0,1,1],[1,1,0,1]]
        
        self.rayon_asteroide = 1
        self.rayon_vaisseau = 1

        self.viemax = 3
        self.vie = 3
        self.score = 0
        self.highscore = self.load_highscore('highscore.txt')
        self.strike = 0

        self.program3d_id = glutils.create_program_from_file('shader.vert', 'shader.frag')
        self.m= Mesh.load_obj('Asteroid.obj')
        self.m.normalize()
        self.m.apply_matrix(pyrr.matrix44.create_from_scale([1.7, 1.7, -1.7, 1]))
        self.texture = glutils.load_texture('Asteroid1.png')
        self.nbTriangle=self.m.get_nb_triangles()
        self.vaoAste=self.m.load_to_gpu()


        self.programGUI_id = glutils.create_program_from_file('gui.vert', 'gui.frag')
        self.vao = Text.initalize_geometry()
        self.textureText = glutils.load_texture('fontB.png')
        self.start = False
        


    def run(self):
        # boucle d'affichage
        while not glfw.window_should_close(self.window):
            # nettoyage de la fenêtre : fond et profondeur
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            # Si la partie est en route
            if self.start==True:
                if self.sem == 1:
                    # initialisation des niveaux
                    self.init_level()
                    self.sem = 0
                    # ajout de l'afficheur de strike
                    self.objs.append(Text(str(self.strike), np.array([-0.05, 0.8], np.float32), np.array([0.05, 0.95], np.float32), self.vao, 2, self.programGUI_id, self.textureText))
                    # suppression du texte "space to start"
                    self.objs.pop(29)
                # Verifie les collisions et augmente la vitesse
                self.collision()
                self.increase_speed()
            # actualise l'état des touches
            self.update_key()

            # Boucle qui parcourt les objets
            for obj in self.objs:
                GL.glUseProgram(obj.program)
                if isinstance(obj, Object3D):
                    self.update_camera(obj.program)
                obj.draw()
                # Si c'est un astéroide le dépalce de 100 lorsqu'il sort de la caméra
                if obj in self.objs[4 : 24]:
                    if obj.transformation.translation.z >  self.objs[0].transformation.translation.z +4:
                        obj.transformation.translation.z+=-100
                # Si c'est un tunnel le dépalce de 200 lorsqu'il sort de la caméra
                elif obj==self.objs[1] or obj==self.objs[2]:
                    if obj.transformation.translation.z >  self.objs[0].transformation.translation.z +50:
                        obj.transformation.translation.z+=-200

            # Boucle qui parcourt les astéroides à eviter
            for obj in self.objs_mechant:
                GL.glUseProgram(obj.program)
                if isinstance(obj, Object3D):
                    self.update_camera(obj.program)
                # Si l'astéroide sort de la camera, le supprime
                if obj.transformation.translation.z >  self.objs[0].transformation.translation.z +4:
                    # augmente le score et la strike
                    self.strike += 1
                    self.score+= 50*self.nb_objs_niveau[0]*self.strike
                    if self.score >self.highscore:
                        self.highscore = self.score
                    # si la strike est un multipe de 10 augmente la vie et l'actualise
                    if self.strike %10 == 0:
                        self.viemax +=1
                        if  self.vie < self.viemax:
                            self.vie +=1
                    elif self.strike%15 == 0 :
                        self.vie =self.viemax
                    self.draw_life()
                    self.draw_strike()
                    self.draw_score()
                    # supprime le level
                    self.delete_level()
                obj.draw()
                
            # changement de buffer d'affichage pour éviter un effet de scintillement
            glfw.swap_buffers(self.window)
            # gestion des évènements
            glfw.poll_events()
        
    def collision(self):
        for obj in self.objs_mechant:
            x = self.objs[0].transformation.translation.x -obj.transformation.translation.x
            z = self.objs[0].transformation.translation.z -obj.transformation.translation.z
            dist = np.sqrt(x*x + z*z)
            # verifie la collision
            if dist <= self.rayon_asteroide + self.rayon_vaisseau :
                # diminue la vie et réinitialise la strike
                self.vie -= 1
                self.strike = 0
                # Recrée un niveau si un niveau d'astéroide actuel
                self.delete_level()
                # Actualise la vie
                self.draw_life()
                self.draw_strike()
                # Met le jeu en pause
                if self.vie == 0 :
                    self.dx = 0
                    self.dz = 0
                    self.objs.pop(29)
                    self.objs.append(Text("PRESS SPACE TO RESTART", np.array([-0.5, -0.2], np.float32), np.array([0.5, 0.2], np.float32), self.vao, 2, self.programGUI_id, self.textureText))
                    self.save_highscore('highscore.txt')
                    self.start=False



    def increase_speed(self):
        if int(time.time()-self.time1s) >= 1 and self.vie > 0:
            self.time1s = time.time()
            self.dz += 0.01

    def draw_score(self):
        self.objs[26] = Text(str(self.highscore), np.array([0.85, 0.79], np.float32), np.array([0.95, 0.94], np.float32), self.vao, 2, self.programGUI_id, self.textureText)
        self.objs[28] = Text(str(self.score), np.array([0.85, 0.69], np.float32), np.array([0.95, 0.84], np.float32), self.vao, 2, self.programGUI_id, self.textureText)
    
    def draw_strike(self):
        self.objs[29] = Text(str(self.strike), np.array([-0.05, 0.8], np.float32), np.array([0.05, 0.95], np.float32), self.vao, 2, self.programGUI_id, self.textureText)

    def draw_life(self):
        coeur = ''
        for i in range(0,self.viemax):
            if i >= self.vie :
                coeur+='@'
            else:
                coeur+='#'
        self.objs[24] = Text(coeur, np.array([-0.95,0.8], np.float32), np.array([-0.95 +0.1*self.viemax,0.95], np.float32), self.vao, 2, self.programGUI_id, self.textureText)

    def init_level(self):
        # boucle qui parcourt le tableau des niveaux
        for i in range (0,len(self.nb_objs_niveau)):
            # génération aléatoire d'un niveau simple
            niveau = self.niveau[random.randint(0,3)]
            nb = 0
            for j in range(0,len(niveau)):
                if niveau[j] == 1:
                    # si l'on a un astéroide
                    nb += 1
                    trAste=Transformation3D()
                    # on le place au bon endroit 
                    trAste.translation.y = 0.5
                    trAste.translation.x = 3.4 - 2.2*j
                    trAste.translation.z = -200 -100*i + self.objs[0].transformation.translation.z
                    o = Object3D(self.vaoAste, self.nbTriangle, self.program3d_id, self.texture,trAste)
                    #  on l'affiche en l'ajoutant dans la liste
                    self.objs_mechant.append(o)
            self.nb_objs_niveau[i] = nb

    def delete_level(self):
        # boucle qui parcourt le tableau des niveaux pour supprimer les premiers objets de la liste
        # ce qui correspond au niveau le plus proche
        for i in range (0,self.nb_objs_niveau[0]):
            self.objs_mechant.pop(0)
        self.nb_objs_niveau[0] = self.nb_objs_niveau[1]
        self.create_level()

    def create_level(self):
        # génération aléatoire d'un niveau difficile
        if int(time.time()-self.timeinit) >= 30:
            niveau = self.niveau[random.randint(10,13)]
        # génération aléatoire d'un niveau moyen
        elif int(time.time()-self.timeinit) >= 15:
            niveau = self.niveau[random.randint(4,9)]
        # génération aléatoire d'un niveau simple
        else:
            niveau = self.niveau[random.randint(0,3)]
        nb = 0
        for i in range(0,len(niveau)):
            # si l'on a un astéroide dans le niveau
            if niveau[i] == 1:
                nb += 1 
                trAste=Transformation3D()
                # on le place au bon endroit
                trAste.translation.y = 0.5
                trAste.translation.x = 3.4 - 2.2*i
                trAste.translation.z = -200 + self.objs[0].transformation.translation.z 
                o = Object3D(self.vaoAste, self.nbTriangle, self.program3d_id, self.texture,trAste)
                 #  on l'affiche en l'ajoutant dans la liste
                self.objs_mechant.append(o)      
        self.nb_objs_niveau[1] = nb

    def load_highscore(self,nom):
        monFichier=open(nom, encoding='utf-8')
        Fichier=monFichier.readlines()
        monFichier.close()
        return int(Fichier[0])

    def save_highscore(self,nom):
        monFichier=open(nom,"w", encoding='utf-8')
        monFichier.write(str(self.score))
        monFichier.close()
    
    def key_callback(self, win, key, scancode, action, mods):
        # sortie du programme si appui sur la touche 'échappement'
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(win, glfw.TRUE)
        self.touch[key] = action
    
    def add_object(self, obj):
        self.objs.append(obj)

    def set_camera(self, cam):
        self.cam = cam

    def update_camera(self, prog):
        GL.glUseProgram(prog)
        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(prog, "translation_view")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : translation_view")
        # Modifie la variable pour le programme courant
        translation = -self.cam.transformation.translation
        GL.glUniform4f(loc, translation.x, translation.y, translation.z, 0)

        # Récupère l'identifiant de la variable pour le programme courant
        loc = GL.glGetUniformLocation(prog, "rotation_center_view")
        # Vérifie que la variable existe
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_center_view")
        # Modifie la variable pour le programme courant
        rotation_center = self.cam.transformation.rotation_center
        GL.glUniform4f(loc, rotation_center.x, rotation_center.y, rotation_center.z, 0)

        rot = pyrr.matrix44.create_from_eulers(-self.cam.transformation.rotation_euler)
        loc = GL.glGetUniformLocation(prog, "rotation_view")
        if (loc == -1) :
            print("Pas de variable uniforme : rotation_view")
        GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, rot)
    
        loc = GL.glGetUniformLocation(prog, "projection")
        if (loc == -1) :
            print("Pas de variable uniforme : projection")
        GL.glUniformMatrix4fv(loc, 1, GL.GL_FALSE, self.cam.projection)

    def update_key(self):
        # déplacement automatique du vaisseau, de la caméra et de la demi-sphère
        self.objs[0].transformation.translation.z -= self.dz
        self.objs[3].transformation.translation.z -= self.dz
        self.cam.transformation.translation.z -= self.dz
        # gestion des touches Q et D pour les déplacements
        if glfw.KEY_A in self.touch and self.touch[glfw.KEY_A] > 0:
            if self.objs[0].transformation.translation.x - self.dx > -3.5:
                self.objs[0].transformation.translation.x -= self.dx
                self.cam.transformation.translation.x -= self.dx
        if glfw.KEY_D in self.touch and self.touch[glfw.KEY_D] > 0:
            if self.objs[0].transformation.translation.x + self.dx< 3.5:
                self.objs[0].transformation.translation.x += self.dx
                self.cam.transformation.translation.x += self.dx
        # réinitialisation des valeurs pour restart la partie
        if glfw.KEY_SPACE in self.touch and self.touch[glfw.KEY_SPACE] > 0:
            if self.start==False:
                self.timeinit = time.time()
                self.time1s = time.time()
                self.objs[0].transformation.translation.x = 0
                self.cam.transformation.translation.x = 0
                self.dz=0.5
                self.dx=0.2
                self.vie=3
                self.viemax=3
                self.draw_life()
                self.score=0
                self.draw_score()
                self.objs_mechant = []
                self.nb_objs_niveau = [0,0]
                self.sem=True
                self.start= True