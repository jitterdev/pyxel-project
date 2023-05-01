import pyxel
import pymunk
import random
import threading


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
        def debounced(*args, **kwargs):
            def call_function():
                debounced._timer = None
                return function(*args, **kwargs)
            # if we already have a call to the function currently waiting to be executed, reset the timer
            if debounced._timer is not None:
                debounced._timer.cancel()

            # after wait_time, call the function provided to the decorator with its arguments
            debounced._timer = threading.Timer(wait_time, call_function)
            debounced._timer.start()

        debounced._timer = None
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

def leftClick(**kwargs):
        self = kwargs['app']
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.point1 = True
            self.point2 = False
            global x1, y1
            x1, y1 = pyxel.mouse_x, pyxel.mouse_y
        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            self.point2 = True
            global x2, y2
            x2, y2 = pyxel.mouse_x, pyxel.mouse_y
            wall_body = pymunk.Body(body_type=pymunk.Body.STATIC)
            line = pymunk.Segment(wall_body, (x1, y1), (x2, y2), 1)
            line.elasticity = 0.8
            self.space.add(wall_body, line)
            self.lines.append(line)
            if len(self.lines) > self.MAX_LINES:
                # Remove oldest line segment from space and lines list
                oldest_line = self.lines.pop(0) 
                self.space.remove(oldest_line.body, oldest_line)
        if self.point1:
            pyxel.circ(x1, y1, 2, 8)
        if self.point2:
            pyxel.circ(x2, y2, 2, 5)
            pyxel.line(x1, y1, x2, y2, 7)


keyToFunction = {
    pyxel.KEY_UP: lambda **kwargs: localImpulse(0, -20, **kwargs),
    pyxel.KEY_DOWN: lambda **kwargs: localImpulse(0, 20, **kwargs),
    pyxel.KEY_LEFT: lambda **kwargs: localImpulse(-10, 0, **kwargs),
    pyxel.KEY_RIGHT: lambda **kwargs: localImpulse(10, 0, **kwargs),
    pyxel.KEY_1: lambda **kwargs: randomizeColor(**kwargs),
    pyxel.KEY_SPACE: debounced_toggle_run_physics, # this works right now but its really cursed, it basically delays the actual toggle by 0.5 seconds as well
    pyxel.MOUSE_BUTTON_LEFT: lambda **kwargs: leftClick(**kwargs),
}

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
        self.shape.elasticity = 0.8
        self.width = width
        self.height = height
        self.space.add(self.shape)
    def draw(self):
        x, y = self.body.position
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
        pyxel.rect(x - width/2, y - height/2, width, height, self.color)
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
        for _ in range(200):
            circle = Circle(random.randint(50,590), random.randint(50,430), random.randint(5,15), self.space)
            self.shapes.append(circle)
        self.args = {
            'color': self.color,
            'app': self,
            'shapes': self.shapes
        }
        # rect = Rectangle(random.randint(50,590), random.randint(50,430), 30, 30, self.space)
        # self.shapes.append(rect)
        pyxel.run(self.update, self.draw)

    def update(self):
        for key, function in keyToFunction.items():
            if pyxel.btn(key):
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
        hovered_body = get_hovered_body(self.space)
        if hovered_body:
            # pyxel.rect(*hovered_body.position, 10, 10, 9)
            pass
        leftClick(**self.args)

        pyxel.text(5, 30, ','.join((str(x) for x in [pyxel.mouse_x, pyxel.mouse_y])), pyxel.COLOR_YELLOW)

        for wall in self.walls:
            body = wall.body
            p1 = body.position + wall.a.rotated(body.angle)
            p2 = body.position + wall.b.rotated(body.angle)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 7)

        # Draw existing lines
        for line in self.lines:
            p1 = line.a
            p2 = line.b
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 7)


App()
