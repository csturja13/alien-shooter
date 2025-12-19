from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time  # Added import

# =========================
# Camera-related variables
camera_pos = (0, 500, 500)   # used in third-person mode (computed each frame)
fovY = 60  
GRID_LENGTH = 600
rand_var = 423

# =========================
# World bounds (walls)
# =========================
XMIN, XMAX = -420, 420  
YMIN, YMAX = -645, 645  
WALL_H = 60  

# =========================
# Game state (globals)
# =========================
# Player
px, py = 0.0, 0.0
pang = 0.0                 # degrees
player_alive = True
life = 5
score = 0
missed = 0

# Bullets: list of dicts {x,y,z,vx,vy,birth}
bullets = []
BULLET_SPEED = 28.0
BULLET_SIZE = 8
BULLET_LIFETIME = 1800  # ms

# Enemies: list of dicts {x,y,z,pulse}
enemies = []
ENEMY_COUNT = 5
ENEMY_HIT_RADIUS = 22.0
PLAYER_HIT_RADIUS = 20.0

# Enemy speed (SLOWED for better gameplay)
ENEMY_SPEED = 0.3  

# Camera mode
first_person = False
orbit_angle = 45.0     # degrees around whole floor
cam_height = 200.0    # Reduced camera height
cam_radius = 600.0    # Reduced camera radius to bring scene closer

# Cheat toggles
cheat_mode = False
cheat_auto_follow = False
_fire_accum = 0  # ms accumulator for auto fire cadence
FIRE_COOLDOWN_MS = 220

# Timekeeping
_last_time = 0

# Colors (0..1)
ASH = (0.698, 0.745, 0.710)
SKIN = (1.0, 0.878, 0.741)
DARK_GREEN = (0.0, 0.392, 0.0)
BLUE = (0.0, 0.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
RED = (1.0, 0.0, 0.0)

# --------------------------------------------------------------------------------
# Minimal helpers implemented inline via expressions (no extra function definitions)
# --------------------------------------------------------------------------------

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_shapes():
    global enemies, px, py, pang, player_alive

    # ---------------------------
    # Floor (checker) + 4 walls
    # ---------------------------
    # Floor tiles
    w, l = 40, 60  
    flg = 0
    glBegin(GL_QUADS)
    for q in range(YMIN, YMAX - l + 1, l):
        for p in range(XMIN, XMAX - w + 1, w):
            if flg == 0:
                glColor3f(1, 1, 1)
                flg = 1
            else:
                glColor3f(0.7, 0.5, 0.95)
                flg = 0
            glVertex3f(p, q, 0)
            glVertex3f(p + w, q, 0)
            glVertex3f(p + w, q + l, 0)
            glVertex3f(p, q + l, 0)
    glEnd()

    # Walls (borders)
    glBegin(GL_QUADS)
    # Left wall (blue)
    glColor3f(0,0,1)
    glVertex3f(XMIN, YMIN, 0)
    glVertex3f(XMIN, YMAX, 0)
    glVertex3f(XMIN, YMAX, WALL_H)
    glVertex3f(XMIN, YMIN, WALL_H)
    # Top wall (cyan)
    glColor3f(0,1,1)
    glVertex3f(XMIN, YMAX, 0)
    glVertex3f(XMAX, YMAX, 0)
    glVertex3f(XMAX, YMAX, WALL_H)
    glVertex3f(XMIN, YMAX, WALL_H)
    # Right wall (green)
    glColor3f(0,1,0)
    glVertex3f(XMAX, YMAX, 0)
    glVertex3f(XMAX, YMIN, 0)
    glVertex3f(XMAX, YMIN, WALL_H)
    glVertex3f(XMAX, YMAX, WALL_H)
    # Bottom wall (white)
    glColor3f(1,1,1)
    glVertex3f(XMIN, YMIN, 0)
    glVertex3f(XMAX, YMIN, 0)
    glVertex3f(XMAX, YMIN, WALL_H)
    glVertex3f(XMIN, YMIN, WALL_H)
    glEnd()

    # ---------------------------
    # Player (sphere + cylinders + cuboids)
    # ---------------------------
    glPushMatrix()
    glTranslatef(px, py, 0)
    if not player_alive:
        glRotatef(90, 1, 0, 0)  # lie down on game over

    glRotatef(pang+90, 0, 0, 1)

    # Body (two cubes)
    glColor3f(*DARK_GREEN)
    glPushMatrix()
    glTranslatef(0, 0, 20)
    glutSolidCube(20)
    glTranslatef(0, 0, 20)
    glutSolidCube(20)
    glPopMatrix()

    # Head (black sphere)
    glColor3f(*BLACK)
    glPushMatrix()
    glTranslatef(0, 0, 55)
    glutSolidSphere(8, 16, 16)
    glPopMatrix()

    # Legs (blue cylinders)
    glColor3f(*BLUE)
    glPushMatrix()
    glTranslatef(7, 0, 10)
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 2, 20, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-7, 0, 10)
    glRotatef(180, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 2, 20, 10, 10)
    glPopMatrix()

    # Arms (skin cylinders)
    glColor3f(*SKIN)
    glPushMatrix()
    glTranslatef(12, 0, 40)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 3, 2, 15, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-12, 0, 40)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 3, 2, 15, 10, 10)
    glPopMatrix()

    # Gun (ash cylinder)
    glColor3f(*ASH)
    glPushMatrix()
    glTranslatef(0, -10, 40)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 1, 24, 10, 10)
    glPopMatrix()

    glPopMatrix()

    # ---------------------------
    # Bullets (cubes)
    # ---------------------------
    glColor3f(0.123, 0.345, 0.567)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b["x"], b["y"], b["z"])
        glutSolidCube(BULLET_SIZE)
        glPopMatrix()

    # ---------------------------
    # Enemies (two spheres each) with pulsing
    # ---------------------------
    for e in enemies:
        s = 1.0 + 0.2 * math.sin(e["pulse"])
        glPushMatrix()
        glTranslatef(e["x"], e["y"], e["z"])
        glScalef(s, s, s)

        glColor3f(1, 0, 0)
        glutSolidSphere(15, 16, 16)
        glTranslatef(0, 0, 15)
        glColor3f(0, 0, 0)
        glutSolidSphere(6, 16, 16)

        glPopMatrix()


def keyboardListener(key, x, y):
    global px, py, pang, cheat_mode, cheat_auto_follow, player_alive, life, score, missed, enemies, bullets, first_person

    if not player_alive:
        if key in (b'r', b'R'):
            # Restart game
            px, py = 0.0, 0.0
            pang = 0.0
            player_alive = True
            life = 5
            score = 0
            missed = 0
            bullets.clear()
            enemies.clear()
            for _ in range(ENEMY_COUNT):
                ex = random.randint(XMIN + 40, XMAX - 40)
                ey = random.randint(YMIN + 40, YMAX - 40)
                enemies.append({"x": float(ex), "y": float(ey), "z": 30.0, "pulse": random.uniform(0, math.tau)})
        return

    # move forward/back along heading; rotate left/right
    if key in (b'w', b'W'):
        ang = math.radians(pang)
        nx = px + 10.0 * math.cos(ang)
        ny = py + 10.0 * math.sin(ang)
        px = max(XMIN + 10, min(XMAX - 10, nx))
        py = max(YMIN + 10, min(YMAX - 10, ny))
    elif key in (b's', b'S'):
        ang = math.radians(pang)
        nx = px - 10.0 * math.cos(ang)
        ny = py - 10.0 * math.sin(ang)
        px = max(XMIN + 10, min(XMAX - 10, nx))
        py = max(YMIN + 10, min(YMAX - 10, ny))
    elif key in (b'a', b'A'):
        pang += 5.0
    elif key in (b'd', b'D'):
        pang -= 5.0
    elif key in (b'c', b'C'):
        cheat_mode = not cheat_mode
    elif key in (b'v', b'V'):
        cheat_auto_follow = not cheat_auto_follow
    elif key in (b'r', b'R'):
        # graceful reset anytime
        px, py = 0.0, 0.0
        pang = 0.0
        player_alive = True
        life = 5
        score = 0
        missed = 0
        bullets.clear()
        enemies.clear()
        for _ in range(ENEMY_COUNT):
            ex = random.randint(XMIN + 40, XMAX - 40)
            ey = random.randint(YMIN + 40, YMAX - 40)
            enemies.append({"x": float(ex), "y": float(ey), "z": 30.0, "pulse": random.uniform(0, math.tau)})


def specialKeyListener(key, x, y):
    global orbit_angle, cam_height
    if key == GLUT_KEY_UP:
        cam_height = max(60.0, min(500.0, cam_height + 10.0))
    if key == GLUT_KEY_DOWN:
        cam_height = max(60.0, min(500.0, cam_height - 10.0))
    if key == GLUT_KEY_LEFT:
        orbit_angle -= 4.0
    if key == GLUT_KEY_RIGHT:
        orbit_angle += 4.0


def mouseListener(button, state, x, y):
    global first_person, bullets
    if state != GLUT_DOWN:
        return

    # Left click -> fire
    if button == GLUT_LEFT_BUTTON:
        if not player_alive:
            return
        ang = math.radians(pang)
        start_x = px + 20 * math.cos(ang)
        start_y = py + 20 * math.sin(ang)
        vx = BULLET_SPEED * math.cos(ang)
        vy = BULLET_SPEED * math.sin(ang)
        bullets.append({"x": start_x, "y": start_y, "z": 15.0, "vx": vx, "vy": vy, "birth": time.time() * 1000})  
    # Right click -> toggle camera mode
    elif button == GLUT_RIGHT_BUTTON:
        first_person = not first_person


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Compute camera based on mode
    if first_person:
        ang = math.radians(pang)
        eye_x = px + 10 * math.cos(ang)
        eye_y = py + 10 * math.sin(ang)
        eye_z = 60
        center_x = eye_x + math.cos(ang)
        center_y = eye_y + math.sin(ang)
        center_z = 60
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 0, 1)
    else:
        ang = math.radians(orbit_angle)
        cx = cam_radius * math.cos(ang)
        cy = cam_radius * math.sin(ang)
        cz = cam_height
        gluLookAt(cx, cy, cz, px, py, 0, 0, 0, 1)


def idle():
    global _last_time, bullets, enemies, score, missed, life, player_alive, pang, _fire_accum

    # Timing
    now = time.time() * 1000  # Changed to time.time()
    if _last_time == 0:
        _last_time = now
    dt = now - _last_time       # milliseconds since last frame
    _last_time = now

    if not enemies:
        # initial spawn (ensure not too close to player)
        for _ in range(ENEMY_COUNT):
            ex = random.randint(XMIN + 40, XMAX - 40)
            ey = random.randint(YMIN + 40, YMAX - 40)
            enemies.append({"x": float(ex), "y": float(ey), "z": 30.0, "pulse": random.uniform(0, math.tau)})

    if player_alive:
        # -----------------
        # Enemies update
        # -----------------
        for e in enemies:
            dx = px - e["x"]
            dy = py - e["y"]
            dist = math.hypot(dx, dy) + 1e-6
            ux, uy = dx / dist, dy / dist
            # slower movement as requested
            step = ENEMY_SPEED * (dt / 16.0)  # normalize roughly to ~60fps
            e["x"] += ux * step
            e["y"] += uy * step
            e["pulse"] += 0.004 * dt

            # player collision
            if dist < (PLAYER_HIT_RADIUS + ENEMY_HIT_RADIUS * 0.6):
                life -= 1
                # respawn enemy elsewhere
                rx = random.randint(XMIN + 40, XMAX - 40)
                ry = random.randint(YMIN + 40, YMAX - 40)
                e["x"], e["y"], e["z"], e["pulse"] = float(rx), float(ry), 30.0, random.uniform(0, math.tau)

        # -----------------
        # Bullets update
        # -----------------
        new_bullets = []
        for b in bullets:
            b["x"] += b["vx"] * (dt / 16.0)
            b["y"] += b["vy"] * (dt / 16.0)
            # lifetime / bounds
            out_of_bounds = not (XMIN <= b["x"] <= XMAX and YMIN <= b["y"] <= YMAX)
            expired = (now - b["birth"]) > BULLET_LIFETIME
            if out_of_bounds or expired:
                missed += 1
                continue

            # hit test vs enemies
            hit = False
            for e in enemies:
                if math.hypot(b["x"] - e["x"], b["y"] - e["y"]) <= ENEMY_HIT_RADIUS:
                    score += 1
                    # enemy respawn
                    rx = random.randint(XMIN + 40, XMAX - 40)
                    ry = random.randint(YMIN + 40, YMAX - 40)
                    e["x"], e["y"], e["z"], e["pulse"] = float(rx), float(ry), 30.0, random.uniform(0, math.tau)
                    hit = True
                    break
            if not hit:
                new_bullets.append(b)
        bullets = new_bullets

        # -----------------
        # Cheat mode: auto aim/fire
        # -----------------
        if cheat_mode and enemies:
            # aim at nearest enemy
            nearest = min(enemies, key=lambda e: (e["x"] - px) ** 2 + (e["y"] - py) ** 2)
            dx = nearest["x"] - px
            dy = nearest["y"] - py
            target_deg = math.degrees(math.atan2(dy, dx))
            diff = (target_deg - pang + 540) % 360 - 180
            # smooth rotate
            pang += max(-3.5, min(3.5, diff))
            # auto fire cadence
            _fire_accum += dt
            if _fire_accum >= FIRE_COOLDOWN_MS:
                _fire_accum = 0
                ang = math.radians(pang)
                start_x = px + 20 * math.cos(ang)
                start_y = py + 20 * math.sin(ang)
                vx = BULLET_SPEED * math.cos(ang)
                vy = BULLET_SPEED * math.sin(ang)
                bullets.append({"x": start_x, "y": start_y, "z": 15.0, "vx": vx, "vy": vy, "birth": now})

        # game over conditions
        if life <= 0 or missed >= 10:
            player_alive = False

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    draw_shapes()

    draw_text(10, 770, f"Life: {life}   Score: {score}   Missed: {missed}")
    cam_txt = "First-Person" if first_person else "Third-Person"
    cheat_txt = "ON" if cheat_mode else "OFF"
    draw_text(10, 740, f"Camera: {cam_txt} | Cheat: {cheat_txt} | Auto-Follow: {'ON' if cheat_auto_follow else 'OFF'}")

    if not player_alive:
        draw_text(410, 420, "GAME OVER")
        draw_text(380, 390, "Press 'R' to Restart")

    glutSwapBuffers()


# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy")

    glClearColor(0.05, 0.08, 0.1, 1)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()