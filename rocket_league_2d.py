# rocket_league_2d.py
# Requiere: kivy, pymunk
# Para Android: buildozer con requirements = kivy, pymunk

import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Ellipse, Rotate, PushMatrix, PopMatrix
from kivy.clock import Clock
from kivy.core.window import Window
import pymunk

# --- Configuración para Android (pantalla completa y redimensionable) ---
Window.fullscreen = 'auto'
Window.softinput_mode = 'below_target'  # Evita que el teclado cubra la UI


class Car:
    """Encapsula el cuerpo rígido y los gráficos del auto."""

    def __init__(self, space, position):
        # Cuerpo dinámico
        self.body = pymunk.Body(mass=1, moment=1000)
        self.body.position = position

        # Hitbox principal (caja roja)
        self.shape = pymunk.Poly.create_box(self.body, (60, 30))
        self.shape.elasticity = 0.1
        self.shape.friction = 0.8
        space.add(self.body, self.shape)

        # Ruedas (círculos azules) como formas de colisión adicionales
        self.wheel_shapes = []
        for offset_x in (-20, 20):
            wheel = pymunk.Circle(self.body, 12, (offset_x, -15))
            wheel.elasticity = 0.1
            wheel.friction = 0.9
            space.add(wheel)
            self.wheel_shapes.append(wheel)

        # Instrucciones de dibujo (se actualizan cada frame)
        self.canvas_instructions = []
        self._create_graphics()

    def _create_graphics(self):
        """Crea los rectángulos y elipses que representan el auto."""
        # Nota: Las instrucciones de canvas se recrean en cada frame dentro del GameWidget
        pass

    def draw(self, canvas):
        """Dibuja el auto en el canvas usando las transformaciones actuales."""
        # Limpiar dibujos anteriores (se maneja desde el GameWidget)
        pass


class GameWidget(Widget):
    """Widget principal del juego: física, dibujo y entrada táctil."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.space = pymunk.Space()
        self.space.gravity = (0, -900)  # Gravedad hacia abajo

        # Suelo (pista negra)
        self.ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.ground_shape = pymunk.Segment(self.ground_body, (-2000, 50), (2000, 50), 5)
        self.ground_shape.elasticity = 0.5
        self.ground_shape.friction = 1.0
        self.space.add(self.ground_body, self.ground_shape)

        # Auto del jugador
        self.car = Car(self.space, (Window.width / 2, 200))

        # Variables de control
        self.joystick_vector = (0, 0)  # (x, y) normalizado
        self.jump_requested = False
        self.on_ground = False

        # Bucle de física
        Clock.schedule_interval(self.update, 1 / 60.0)
        # Redibujado
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_interval(self.redraw, 1 / 60.0)

    def update(self, dt):
        """Paso de la simulación y procesamiento de controles."""
        # Aplicar fuerza horizontal desde el joystick
        if abs(self.joystick_vector[0]) > 0.1:
            force_x = self.joystick_vector[0] * 5000
            self.car.body.apply_force_at_local_point((force_x, 0), (0, 0))

        # Salto
        if self.jump_requested and self.on_ground:
            impulse = (0, 12000)
            self.car.body.apply_impulse_at_local_point(impulse, (0, 0))
            self.jump_requested = False

        # Rotación automática para enderezar cuando toca el suelo
        # Se comprueba si alguna rueda o el cuerpo está en contacto con el segmento del suelo
        self.on_ground = False
        for shape in [self.car.shape] + self.car.wheel_shapes:
            if self.space.shape_query(shape):
                for contact in self.space.shape_query(shape):
                    if contact.shape == self.ground_shape:
                        self.on_ground = True
                        break
            if self.on_ground:
                break

        if self.on_ground:
            # Aplicar un resorte rotacional suave hacia el ángulo 0 (erguido)
            # Usamos un impulso angular proporcional al ángulo actual
            target_angle = 0
            current_angle = self.car.body.angle
            # Normalizar el ángulo al rango [-pi, pi]
            diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
            # Amortiguar la velocidad angular y empujar hacia el objetivo
            angular_impulse = diff * 50 - self.car.body.angular_velocity * 0.8
            self.car.body.angular_velocity += angular_impulse * dt
        else:
            # En el aire, permitir rotación libre con poco amortiguamiento
            pass

        # Avanzar simulación
        self.space.step(dt)

    def redraw(self, *args):
        """Redibuja la pista y el auto en cada frame."""
        self.canvas.clear()
        with self.canvas:
            # Fondo negro (pista)
            Color(0, 0, 0, 1)
            Rectangle(pos=self.pos, size=self.size)

            # Suelo (línea negra sobre fondo negro, pero con un borde visible)
            Color(0.2, 0.2, 0.2, 1)
            # Dibujamos el segmento del suelo como una línea gruesa
            # (Pymunk no dibuja directamente; usamos la posición conocida)
            ground_y = self.ground_body.position.y + 50  # Ajuste según el segmento
            # En realidad, el segmento está en y=50, dibujamos una línea horizontal
            # Para simplificar, dibujamos una línea en y=50
            from kivy.graphics import Line
            Line(points=[self.x, 50, self.right, 50], width=4)

            # Dibujar el auto
            self._draw_car()

    def _draw_car(self):
        """Dibuja el auto rojo con ruedas azules usando transformaciones de canvas."""
        body = self.car.body
        # Guardar estado de transformación
        PushMatrix()
        # Trasladar al centro del cuerpo y rotar
        Rotate(angle=math.degrees(body.angle), origin=(body.position.x, body.position.y))
        # Caja roja (hitbox principal)
        Color(1, 0, 0, 1)  # Rojo
        Rectangle(pos=(body.position.x - 30, body.position.y - 15), size=(60, 30))
        # Ruedas azules (círculos)
        Color(0, 0, 1, 1)  # Azul
        for offset_x in (-20, 20):
            Ellipse(pos=(body.position.x + offset_x - 12, body.position.y - 15 - 12),
                    size=(24, 24))
        PopMatrix()

    def on_touch_down(self, touch):
        """Delegar a la UI de controles si toca en la zona inferior."""
        # La UI se maneja en el widget de controles superpuesto
        return super().on_touch_down(touch)


class ControlsWidget(GridLayout):
    """UI de controles: joystick virtual y botón de salto en un GridLayout."""

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.cols = 2
        self.rows = 1
        self.size_hint = (1, 0.25)  # Ocupa el 25% inferior de la pantalla
        self.pos_hint = {'x': 0, 'y': 0}

        # --- Joystick virtual (implementación simple con canvas) ---
        self.joystick = JoystickWidget(game=self.game)
        self.add_widget(self.joystick)

        # --- Botón de salto ---
        self.jump_button = Button(text='SALTAR', font_size='20sp',
                                  background_color=(0, 0.5, 1, 1))
        self.jump_button.bind(on_press=self._on_jump)
        self.add_widget(self.jump_button)

    def _on_jump(self, instance):
        self.game.jump_requested = True


class JoystickWidget(Widget):
    """Joystick táctil básico que actualiza game.joystick_vector."""

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.base_radius = 50
        self.pad_radius = 25
        self.base_center = (0, 0)  # Se calcula en redraw
        self.pad_offset = (0, 0)

        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_interval(self.redraw, 1 / 60.0)

    def redraw(self, *args):
        self.canvas.clear()
        # Centro del joystick: mitad izquierda del widget
        self.base_center = (self.x + self.width * 0.25, self.y + self.height * 0.5)
        with self.canvas:
            # Base del joystick
            Color(0.3, 0.3, 0.3, 0.6)
            Ellipse(pos=(self.base_center[0] - self.base_radius,
                         self.base_center[1] - self.base_radius),
                    size=(self.base_radius * 2, self.base_radius * 2))
            # Pad (círculo interior)
            Color(0.6, 0.6, 0.6, 0.9)
            pad_x = self.base_center[0] + self.pad_offset[0] * self.base_radius
            pad_y = self.base_center[1] + self.pad_offset[1] * self.base_radius
            Ellipse(pos=(pad_x - self.pad_radius, pad_y - self.pad_radius),
                    size=(self.pad_radius * 2, self.pad_radius * 2))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._update_pad(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self._update_pad(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.pad_offset = (0, 0)
            self.game.joystick_vector = (0, 0)
            return True
        return super().on_touch_up(touch)

    def _update_pad(self, touch):
        dx = touch.x - self.base_center[0]
        dy = touch.y - self.base_center[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            # Normalizar al radio de la base
            factor = min(dist, self.base_radius) / dist
            self.pad_offset = (dx * factor / self.base_radius,
                               dy * factor / self.base_radius)
            # Vector para el juego (solo componente x para movimiento lateral)
            self.game.joystick_vector = (self.pad_offset[0], self.pad_offset[1])


class RocketLeague2DApp(App):
    def build(self):
        # Contenedor principal que permite superponer UI y juego
        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()

        # Widget del juego (ocupa toda la pantalla)
        self.game = GameWidget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        root.add_widget(self.game)

        # Widget de controles (superpuesto en la parte inferior)
        self.controls = ControlsWidget(game=self.game, size_hint=(1, 0.25),
                                       pos_hint={'x': 0, 'y': 0})
        root.add_widget(self.controls)

        return root


if __name__ == '__main__':
    RocketLeague2DApp().run()
