import pyxel
import pymunk
import random
import time
import math


steps = 60 # setting this higher than 60 breaks the line drawing a lot in unpredictable ways
speed = 1.0
dt = speed / steps

# TODO:


def debounce(wait_time):
    """
    Decorator that will debounce a function so that it is called after wait_time seconds
    If it is called multiple times, will wait for the last call to be debounced and run only this one.
    """

    def decorator(function):
        last_call = 0
        def debounced(*args, **kwargs):
            nonlocal last_call
            current_time = time.time()
            elapsed_time = current_time - last_call
            if elapsed_time < wait_time:
                # not enough time has passed since the last call to the function
                return
            last_call = current_time
            return function(*args, **kwargs)

        return debounced

    return decorator

def print_mass_moment(b):
    print("mass={:.0f} moment={:.0f}".format(b.mass, b.moment))

def get_hovered_body(space):
    x, y = pyxel.mouse_x, pyxel.mouse_y
    point = space.point_query((x, y), 0, pymunk.ShapeFilter())
    if point:
        shape = point[0].shape
        return shape.body

def toggle_run_physics(**kwargs):
    setattr(kwargs['app'], 'run_physics', not kwargs['app'].run_physics)

debounced_toggle_run_physics = debounce(0.5)(toggle_run_physics)

def localImpulse(x, y, **kwargs):
    for shape in kwargs['shapes']:
        shape.body.apply_impulse_at_local_point((shape.body.mass*x, shape.body.mass*y))
def randomizeColor(**kwargs):
    for shape in kwargs['shapes']:
        shape.color = random.randint(0,15)


def line(**kwargs):
    self = kwargs['app']
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
        self.point1 = True
        self.point2 = False
        global x1, y1
        x1, y1 = pyxel.mouse_x, pyxel.mouse_y
    if self.point1 and not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
        self.point2 = True
        global x2, y2
        x2, y2 = pyxel.mouse_x, pyxel.mouse_y
    if self.point1 and self.point2:
        wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        line = pymunk.Segment(wall_body, (x1, y1), (x2, y2), 1)
        line.elasticity = 0.8
        self.space.add(wall_body, line)
        self.lines.append(line)
        if len(self.lines) > self.MAX_LINES:
            # Remove oldest line segment from space and lines list
            oldest_line = self.lines.pop(0) 
            self.space.remove(oldest_line.body, oldest_line)
        self.point1 = False
        self.point2 = False

def circle(**kwargs):
    self = kwargs['app']
    if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
        self.point1 = True
        self.point2 = False
        global x1, y1
        x1, y1 = pyxel.mouse_x, pyxel.mouse_y
    if self.point1 and not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
        self.point2 = True
        global x2, y2
        x2, y2 = pyxel.mouse_x, pyxel.mouse_y
    if self.point1 and self.point2:
        radius = math.dist((x1, y1), (x2, y2))
        circle = Circle(pyxel.mouse_x, pyxel.mouse_y, radius, self.space)
        self.shapes.append(circle)
        self.point1 = False
        self.point2 = False


modeToFunction = {
    'create': {
        'line': lambda **kwargs: line(**kwargs),
        'circle': lambda **kwargs: circle(**kwargs),
    },
    'edit': {},
    'delete': {},
}

def leftClick(**kwargs):
    mode = kwargs['app'].mode
    submode = kwargs['app'].subMode
    for dict_mode, submodes in modeToFunction.items():
        if dict_mode == mode:
            for dict_submode, function in submodes.items():
                if dict_submode == submode:
                    function(**kwargs)

submodes = {
    'create': {
        pyxel.KEY_Z: 'line',
        pyxel.KEY_X: 'circle',
        pyxel.KEY_C: 'rectangle',
        pyxel.KEY_V: 'triangle',
        pyxel.KEY_B: 'constraint',
        pyxel.KEY_0: None
    },
    'edit': {},
    'delete': {}
}


modes = {
    pyxel.KEY_1: 'create',
    pyxel.KEY_2: 'edit',
    pyxel.KEY_3: 'delete',
}

def changeSubMode(**kwargs):
    self = kwargs['app']
    for mode, submode in submodes.items():
        if self.mode == mode:
            for key, submode in submode.items():
                if key == kwargs['key']:
                    self.subMode = submode

def changeMode(**kwargs):
    self = kwargs['app']
    for key, mode in modes.items():
        if key == kwargs['key']:
            self.mode = mode
            self.subMode = None

def chain(*iterables):
    for it in iterables:
        for each in it:
            yield each



keyToFunction = {
    pyxel.KEY_UP: lambda **kwargs: localImpulse(0, -20, **kwargs),
    pyxel.KEY_DOWN: lambda **kwargs: localImpulse(0, 20, **kwargs),
    pyxel.KEY_LEFT: lambda **kwargs: localImpulse(-10, 0, **kwargs),
    pyxel.KEY_RIGHT: lambda **kwargs: localImpulse(10, 0, **kwargs),
    # pyxel.KEY_1: lambda **kwargs: randomizeColor(**kwargs),
    pyxel.KEY_SPACE: debounced_toggle_run_physics,
    tuple(modes.keys()): lambda **kwargs: changeMode(**kwargs),
    tuple(key for submode in submodes.values() for key in submode.keys()): lambda **kwargs: changeSubMode(**kwargs),
    pyxel.MOUSE_BUTTON_LEFT: lambda **kwargs: leftClick(**kwargs),
}

class Constraint:
    def __init__(self, body_a, body_b, space):
        self.constraint = None
        self.body_a = body_a
        self.body_b = body_b
        self.space = space
    def create_constraint(self):
        raise NotImplementedError("create_constraint method must be implemented in subclass")
    
    def add_to_space(self):
        self.space.add(self.constraint)
    
    def remove_from_space(self):
        self.space.remove(self.constraint)

    def draw(self):
        pass

class DampedRotarySpring(Constraint): # DampedRotarySpring works like the DammpedSpring but in a angular fashion.
    def __init__(self, body_a, body_b, rest_angle, stiffness, dampness, space):
        super().__init__(body_a, body_b, space)
        self.rest_angle = rest_angle
        self.stiffness = stiffness
        self.dampness = dampness
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.DampedRotarySpring(self.body_a, self.body_b, self.rest_angle, self.stiffness, self.dampness)
class DampedSpring(Constraint): # The spring allows you to define the rest length, stiffness and damping.
    def __init__(self, body_a, body_b, anchor_a, anchor_b, rest_length, stiffness, dampness, space):
        super().__init__(body_a, body_b, space)
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.rest_angle = rest_length
        self.stiffness = stiffness
        self.dampness = dampness
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.DampedSpring(self.body_a, self.body_b, self.anchor_a, self.anchor_b, self.rest_angle, self.stiffness, self.dampness)

class GearJoint(Constraint): # GearJoint keeps the angular velocity ratio of a pair of bodies constant.
    def __init__(self, body_a, body_b, phase, ratio, space):
        super().__init__(body_a, body_b, space)
        self.phase = phase
        self.ratio = ratio # ratio is always measured in absolute terms. It is currently not possible to set the ratio in relation to a third body’s angular velocity. phase is the initial angular offset of the two bodies.
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.GearJoint(self.body_a, self.body_b, self.phase, self.ratio)

class GrooveJoint(Constraint): # GrooveJoint is similar to a PivotJoint, but with a linear slide. One of the anchor points is a line segment that the pivot can slide in instead of being fixed.
    def __init__(self, body_a, body_b, groove_a, groove_b, anchor_b, space):
        super().__init__(body_a, body_b, space)
        self.groove_a = groove_a
        self.groove_b = groove_b
        self.anchor_b = anchor_b
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.GrooveJoint(self.body_a, self.body_b, self.groove_a, self.groove_b, self.anchor_b)

class PinJoint(Constraint): # PinJoint links shapes with a solid bar or pin. Keeps the anchor points at a set distance from one another.
    def __init__(self, body_a, body_b, anchor_a, anchor_b, space):
        super().__init__(body_a, body_b, space)
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.PinJoint(self.body_a, self.body_b, self.anchor_a, self.anchor_b)

class PivotJoint(Constraint): # PivotJoint allow two objects to pivot about a single point. It's like a swivel.
    def __init__(self, body_a, body_b, pivot, space):
        super().__init__(body_a, body_b, space)
        self.pivot = pivot
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.PivotJoint(self.body_a, self.body_b, self.pivot)

class RatchetJoint(Constraint): # RatchetJoint is a rotary ratchet, it works like a socket wrench.
    def __init__(self, body_a, body_b, phase, ratchet, space):
        super().__init__(body_a, body_b, space)
        self.phase = phase # phase is the initial offset to use when deciding where the ratchet angles are.
        self.ratchet = ratchet # ratchet is the distance between "clicks"
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.RatchetJoint(self.body_a, self.body_b, self.phase, self.ratchet)

class RotaryLimitJoint(Constraint): # RotaryLimitJoint constrains the relative rotations of two bodies.
    def __init__(self, body_a, body_b, min, max, space):
        super().__init__(body_a, body_b, space)
        self.min = min # min and max are the angular limits in radians. It is implemented so that it’s possible to for the range to be greater than a full revolution.
        self.max = max
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.RotaryLimitJoint(self.body_a, self.body_b, self.min, self.max)

class SimpleMotor(Constraint): # SimpleMotor keeps the relative angular velocity constant.
    def __init__(self, body_a, body_b, rate, space):
        super().__init__(body_a, body_b, space)
        self.rate = rate # rate is the desired relative angular velocity. You will usually want to set an force (torque) maximum for motors as otherwise they will be able to apply a nearly infinite torque to keep the bodies moving.
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.SimpleMotor(self.body_a, self.body_b, self.rate)

class SlideJoint(Constraint): # SlideJoint is like a PinJoint, but with a minimum and maximum distance. A chain could be modeled using this joint. It keeps the anchor points from getting to far apart, but will allow them to get closer together.
    def __init__(self, body_a, body_b, anchor_a, anchor_b, space):
        super().__init__(body_a, body_b, space)
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.create_constraint()
    def create_constraint(self):
        self.constraint = pymunk.SlideJoint(self.body_a, self.body_b, self.anchor_a, self.anchor_b)

class Shape:
    def __init__(self, x, y, space):
        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = x, y
        self.space = space
        self.color = 8
        self.space.add(self.body)
    def draw(self):
        pass

class Circle(Shape):
    def __init__(self, x, y, radius, space):
        super().__init__(x, y, space)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.density = .2
        self.shape.elasticity = 0.8
        self.radius = radius
        self.space.add(self.shape)
    def draw(self):
        x, y = self.body.position
        radius = self.shape.radius
        width = pyxel.width
        height = pyxel.height
        
        # Adjust position if outside the bounds of the window
        if x - radius < 0:
            x = radius
        elif x + radius > width:
            x = width - radius
        
        if y - radius < 0:
            y = radius
        elif y + radius > height:
            y = height - radius
        
        self.body.position = x, y
        pyxel.circ(x, y, radius, self.color)

class Rectangle(Shape):
    def __init__(self, x, y, width, height, space):
        super().__init__(x, y, space)
        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.density = .05
        self.shape.mass = 1.0
        self.shape.elasticity = 0.8
        self.width = width
        self.height = height
        self.space.add(self.shape)
        self.body.moment = pymunk.moment_for_box(self.shape.mass, (width, height))
        self.angle = 0
    def draw(self):
        x, y = self.body.position
        angle = math.degrees(self.body.angle)
        width = self.width
        height = self.height
        
        # Adjust position if outside the bounds of the window
        if x - width/2 < 0:
            x = width/2
        elif x + width/2 > pyxel.width:
            x = pyxel.width - width/2
        
        if y - height/2 < 0:
            y = height/2
        elif y + height/2 > pyxel.height:
            y = pyxel.height - height/2
        
        self.body.position = x, y

        # Compute vertices of rotated rectangle
        x1, y1 = -width/2, -height/2
        x2, y2 = width/2, -height/2
        x3, y3 = width/2, height/2
        x4, y4 = -width/2, height/2
        
        cx, cy = x, y
        ca, sa = math.cos(self.body.angle), math.sin(self.body.angle)
        
        # Rotate vertices around the center of the rectangle
        x1r, y1r = cx + ca * x1 - sa * y1, cy + sa * x1 + ca * y1
        x2r, y2r = cx + ca * x2 - sa * y2, cy + sa * x2 + ca * y2
        x3r, y3r = cx + ca * x3 - sa * y3, cy + sa * x3 + ca * y3
        x4r, y4r = cx + ca * x4 - sa * y4, cy + sa * x4 + ca * y4
        
        # Draw the rotated rectangle
        vertices = [(x1r, y1r), (x2r, y2r), (x3r, y3r), (x4r, y4r)]
        for i in range(4):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i+1)%4]
            pyxel.line(x1, y1, x2, y2, self.color)


class App:
    def __init__(self):
        pyxel.init(640, 480, fps=steps)
        pyxel.mouse(True)
        self.run_physics = True
        self.space = pymunk.Space()
        self.space.gravity = 0, 1000
        self.point1 = False
        self.point2 = False
        self.color = 11
        self.lines = []
        self.MAX_LINES = 3
        self.mode = None
        self.subMode = None
        # create walls
        wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.walls = [
            pymunk.Segment(wall_body, (0, 0), (pyxel.width-1, 0), 1),
            pymunk.Segment(wall_body, (pyxel.width-1, 0), (pyxel.width-1, pyxel.height-1), 1),
            pymunk.Segment(wall_body, (pyxel.width, pyxel.height-1), (0, pyxel.height-1), 1),
            pymunk.Segment(wall_body, (0, pyxel.height), (0, 0), 1)
        ]
        for wall in self.walls:
            wall.elasticity = 0.8
            wall.friction = 0.8
        self.space.add(wall_body, *self.walls)
        self.shapes = []
        for _ in range(100):
            circle = Circle(random.randint(50,590), random.randint(50,430), random.randint(5,15), self.space)
            self.shapes.append(circle)
        self.args = {
            'color': self.color,
            'app': self,
            'shapes': self.shapes,
            'key': None
        }
        # for _ in range(50):
        #     rect = Rectangle(random.randint(50,590), random.randint(50,430), random.randint(20,40), random.randint(20,40), self.space)
        #     self.shapes.append(rect)
        pyxel.run(self.update, self.draw)

    def update(self):
        for key, function in keyToFunction.items():
            if type(key) == tuple:
                for key in key:
                    if pyxel.btn(key) or pyxel.btnr(key):
                        self.args['key'] = key
                        function(**self.args)
            else:
                if pyxel.btn(key) or pyxel.btnr(key):
                    function(**self.args)
        # print(self.run_physics)
        if self.run_physics:
            for _ in range(steps): # move simulation forward 0.1 seconds:
                self.space.step(dt / steps)

    def draw(self):
        pyxel.cls(1)
        for shape in self.shapes:
            shape.draw()
            # print_mass_moment(shape.body)
        # hovered_body = get_hovered_body(self.space)
        # if hovered_body:
        #     # pyxel.rect(*hovered_body.position, 10, 10, 9)
        #     pass

        pyxel.text(5, 30, ','.join((str(x) for x in [pyxel.mouse_x, pyxel.mouse_y])), pyxel.COLOR_YELLOW)
        pyxel.text(600, 440, 'None' if self.mode is None else self.mode, 7)
        pyxel.text(600, 450, 'None' if self.subMode is None else self.subMode, 7)
        
        for wall in self.walls:
            body = wall.body
            p1 = body.position + wall.a.rotated(body.angle)
            p2 = body.position + wall.b.rotated(body.angle)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 7)
            
        if self.point1:
            pyxel.circ(x1, y1, 2, 8)
        if self.point2:
            pyxel.circ(x2, y2, 2, 5)

        # Draw existing lines
        for line in self.lines:
            p1 = line.a
            p2 = line.b
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 7)


App()