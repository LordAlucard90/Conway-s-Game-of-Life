import GameOfLife
from .Controllers import GrowthMediumCTRL
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import Color,  Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from os.path import dirname, abspath

#
#           Styles
#

Builder.load_file('{}/Views.kv'.format(dirname(abspath(GameOfLife.__file__))))


#
#           Base Elements
#


class CtrlButton(Button):
    """ CtrlButton represent a button who interacts with control """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super().__init__(**kwargs)


class CtrlLabel(Label):
    """ CtrlLabel represent a label who interacts with control """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super().__init__(**kwargs)


class CtrlPopup(Popup):
    """ CtrlPopup represent a popup who interacts with control """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(CtrlPopup, self).__init__(**kwargs)


class InputCtrl(TextInput):
    """ InputCtrl represent a text input who interacts with control """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super().__init__(**kwargs)


#
#           Main Layouts
#


class GameLayout(GridLayout):
    """ GameLayout represent the wrapper of all interface components """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super().__init__(**kwargs)
        self.add_widget(ControlsBar(self.ctrl))
        self.add_widget(Factory.TutorialLabel())
        self.gms = GrowthMediumSurface(self.ctrl)
        self.add_widget(self.gms)

    def refresh_keyboard(self) -> None:
        """ Refresh GrowthMediumSurface's keyboard listener

        This method helps to reinstall the binding for the keyboard listener when a popup compromise it.

        :return: None

        """
        self.gms.refresh_keyboard()


class ControlsBar(GridLayout):
    """ ControlsBar represent the wrapper of all main controls interface buttons """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super().__init__(**kwargs)
        self.add_widget(Factory.Load(self.ctrl))
        self.add_widget(Factory.Save(self.ctrl))
        self.add_widget(Factory.Reset(self.ctrl))
        self.add_widget(Factory.Clear(self.ctrl))
        self.add_widget(Factory.SpeedLabel(self.ctrl))
        self.add_widget(Factory.SpeedDown(self.ctrl))
        self.add_widget(Factory.Pause(self.ctrl))
        self.add_widget(Factory.Start(self.ctrl))
        self.add_widget(Factory.SpeedUp(self.ctrl))
        self.add_widget(Factory.ZoomLabel(self.ctrl))
        self.add_widget(Factory.ZoomOut(self.ctrl))
        self.add_widget(Factory.ZoomIn(self.ctrl))


class GrowthMediumSurface(Label):
    """ GrowthMediumSurface represent the GrowthMedium cells' grid

    This class holds all graphic information and transitions needed to the pretty and correct visualization of cells
    evolution. Starting from single cell's state's color to continue with current grid view, its size and its position.

    """
    # Current cells' state
    cells = ListProperty()
    old_cells = []

    # Position and dimension information's
    cell_rows = NumericProperty()
    cell_cols = NumericProperty()

    zoom = NumericProperty()

    pos_x = NumericProperty()
    pos_y = NumericProperty()

    # Size information for correct draw
    cell_size_w = NumericProperty()
    cell_size_h = NumericProperty()

    border_w = NumericProperty()
    border_h = NumericProperty()

    hbar_w = NumericProperty()
    hbar_h = 3
    vbar_w = 3
    vbar_h = NumericProperty()

    # Canvas objects
    cells_canvas = []
    bars_canvas = []

    # Colors
    bars_color = (0, 0, 1, .8)
    cell_color_state = [(0.2, 0.2, 0.2, 1), (0, 1, 0, .5), (1, 0, 0, .5)]

    # just to avoid bug
    _first_draw = True
    _scheduled_draw = False

    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(GrowthMediumSurface, self).__init__(**kwargs)
        Window.bind(on_resize=self._redraw)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    #
    #           Draw managers
    #

    def on_cells(self, *args: object) -> None:
        """ Cells listener

        This method catches cells updated state and manage the redraw of the GUI.

        :return: None

        """
        if len(self.cells) == len(self.old_cells) and not self._scheduled_draw:
            self._draw_update()
            self._draw_bars()
        else:
            self._redraw()
        self.old_cells = self.cells

    def texture_update(self, *args: object) -> None:
        """ Texture listener

        This method is used to draw the GUI the first time.

        :return: None

        """
        self._redraw()

    #
    #           User input listeners
    #

    def refresh_keyboard(self) -> None:
        """ Refresh keyboard listener

        This method reinstalls the binding for the keyboard listener.

        :return: None

        """
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'spacebar':
            if self.ctrl.is_running:
                self.ctrl.pause_evolution()
            elif self.ctrl.can_run:
                self.ctrl.start_evolution()
        elif keycode[1] == 'up':
            self.ctrl.increase_zoom()
        elif keycode[1] == 'down':
            self.ctrl.decrease_zoom()
        elif keycode[1] == 'left':
            self.ctrl.decrease_fps()
        elif keycode[1] == 'right':
            self.ctrl.increase_fps()
        elif keycode[1] == 'w':
            self.ctrl.move_up()
        elif keycode[1] == 'a':
            self.ctrl.move_left()
        elif keycode[1] == 's':
            self.ctrl.move_down()
        elif keycode[1] == 'd':
            self.ctrl.move_right()
        if keycode[1] in ['up', 'down', 'left', 'right', 'w', 'a', 's', 'd']:
            self._draw_bars()

    def on_touch_down(self, touch: object) -> None:
        """ Click listener

        This method catches user's clicks to update custom grid.

        :return: None

        """
        if not self.ctrl.is_running and self.height > touch.pos[1]:
            w = int(touch.pos[0])
            h = int(touch.pos[1])
            i = max(self.cell_rows - int((h - self.border_h) / (self.cell_size_h + 1)) - 1, 0)
            j = min(int((w - self.border_w) / (self.cell_size_w + 1)), self.cell_cols - 1)
            self.ctrl.update_custom_growth_medium(i, j)

    #
    #           Cells and bars designers
    #

    def _redraw(self, *args):
        if not self._scheduled_draw:
            self._scheduled_draw = True
            Clock.schedule_once(self._schedule_redraw, self.zoom / 30)

    def _schedule_redraw(self, *args):
        self.canvas.clear()
        self.cells_canvas = [None] * len(self.cells)
        for i in range(self.cell_rows):
            for j in range(self.cell_cols):
                pos = j + (self.cell_rows - i - 1) * self.cell_cols
                cell = InstructionGroup()
                cell.add(Color(*self.cell_color_state[self.cells[pos]]))
                cell.add(Rectangle(
                            pos=(
                                j * (self.cell_size_w + 1) + self.border_w,
                                i * (self.cell_size_h + 1) + self.border_h
                            ), size=(self.cell_size_w, self.cell_size_h)))
                self.cells_canvas[pos] = cell
                self.canvas.add(cell)
        if not self._first_draw:
            self._draw_bars()
        else:
            self._first_draw = False
        self._scheduled_draw = False

    def _draw_bars(self):
        if len(self.bars_canvas) > 0:
            self.canvas.remove(self.bars_canvas.pop())
            self.canvas.remove(self.bars_canvas.pop())
        hbar = InstructionGroup()
        vbar = InstructionGroup()
        hbar.add(Color(*self.bars_color))
        vbar.add(Color(*self.bars_color))
        vbar.add(Rectangle(
                    pos=(self.width - self.vbar_w - 1, self.border_h + self.vbar_pos_h),
                    size=(self.vbar_w, self.vbar_h)))
        hbar.add(Rectangle(
                    pos=(self.hbar_pos_w, 1),
                    size=(self.hbar_w, self.hbar_h)))
        self.bars_canvas.append(vbar)
        self.bars_canvas.append(hbar)
        self.canvas.add(vbar)
        self.canvas.add(hbar)

    def _draw_update(self):
        for i in range(self.cell_rows):
            for j in range(self.cell_cols):
                pos = j + (self.cell_rows - i - 1) * self.cell_cols
                if self.cells[pos] != self.old_cells[pos]:
                    new_cell = InstructionGroup()
                    new_cell.add(Color(*self.cell_color_state[self.cells[j + (self.cell_rows - i - 1) * self.cell_cols]]))
                    new_cell.add(Rectangle(
                                pos=(
                                    j * (self.cell_size_w + 1) + self.border_w,
                                    i * (self.cell_size_h + 1) + self.border_h
                                ), size=(self.cell_size_w, self.cell_size_h)))
                    self.canvas.remove(self.cells_canvas[pos])
                    self.cells_canvas[pos] = new_cell
                    self.canvas.add(new_cell)


#
#           Popups
#


class SaveCtrlPopup(CtrlPopup):
    """ SaveCtrlPopup contains the view to save current GrowthMedium """
    def __init__(self, keyboard_listener: GrowthMediumSurface, **kwargs: object):
        super(SaveCtrlPopup, self).__init__(**kwargs)
        self.keyboard_listener = keyboard_listener
        self.add_widget(SaveGridCtrl(self.ctrl))

    def dismiss(self, *largs: object, **kwargs: object):
        super().dismiss()
        self.keyboard_listener.refresh_keyboard()


class SaveGridCtrl(GridLayout):
    """ SaveGridCtrl contains all inputs to save current GrowthMedium """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(SaveGridCtrl, self).__init__(**kwargs)
        self.add_widget(InputCtrl(self.ctrl))
        self.add_widget(Factory.SavePopupBtn(self.ctrl))
        self.add_widget(Factory.CloseSavePopupBtn(self.ctrl))


class LoadCtrlPopup(CtrlPopup):
    """ LoadCtrlPopup contains the view to load a GrowthMedium """
    def __init__(self, **kwargs: object):
        super(LoadCtrlPopup, self).__init__(**kwargs)
        self.add_widget(LoadGridCtrl(self.ctrl))


class LoadGridCtrl(GridLayout):
    """ LoadGridCtrl contains all inputs to load a GrowthMedium """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(LoadGridCtrl, self).__init__(**kwargs)
        self.add_widget(ScrollFilesCtrl(self.ctrl))
        self.add_widget(Factory.LoadLabel(self.ctrl))
        self.add_widget(ActionLoadGridCtrl(self.ctrl))


class ActionLoadGridCtrl(GridLayout):
    """ ActionLoadGridCtrl contains action's buttons """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(ActionLoadGridCtrl, self).__init__(**kwargs)
        self.add_widget(Factory.LoadPopupBtn(self.ctrl))
        self.add_widget(Factory.CloseLoadPopupBtn(self.ctrl))


class ScrollFilesCtrl(ScrollView):
    """ ScrollFilesCtrl contains the scrollable list of files """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(ScrollFilesCtrl, self).__init__(**kwargs)
        file_ctrl = FileCtrl(self.ctrl)
        file_ctrl.bind(minimum_height=file_ctrl.setter('height'))
        self.add_widget(file_ctrl)


class FileCtrl(GridLayout):
    """ FileCtrl contains the Growth Medium's input files list """
    def __init__(self, grid_ctrl: GrowthMediumCTRL, **kwargs: object):
        self.ctrl = grid_ctrl
        super(FileCtrl, self).__init__(**kwargs)
        for file in self.ctrl.get_growth_medium_files():
            self.add_widget(Factory.FileCtrlBtn(self.ctrl, text=file))
