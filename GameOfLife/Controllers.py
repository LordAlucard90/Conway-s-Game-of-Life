from .Models import GrowthMedium
from copy import copy
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty


class GrowthMediumCTRL(EventDispatcher):
    """ GrowthMediumCTRL represent the controller of the Game Of Life

    This class contains methods and properties to manage current state and view.
    Menages evolution and current speed, asks to the GrowthMedium (model) for states updates and sets user custom modifies.
    Listens to views interaction and notifies current state updates by public Properties.

    """

    # Basic UI variables
    round = NumericProperty()   # not shown
    fps = NumericProperty()
    zoom = NumericProperty()

    # General system state variables
    can_run = BooleanProperty()
    is_running = BooleanProperty()
    custom_gm = BooleanProperty()

    # Current cells' state
    gm_state_grid = ListProperty()

    # Grid dimension variables
    gm_min_cols = NumericProperty()
    gm_min_rows = NumericProperty()
    gm_cur_cols = NumericProperty()
    gm_cur_rows = NumericProperty()

    # Position of current middle view subject to all explorable grid
    pos_x = NumericProperty()
    pos_y = NumericProperty()

    # Files I/O variables
    path_exists = BooleanProperty()
    is_path_valid = BooleanProperty()
    path = StringProperty()

    # Read-Only variables
    _min_fps = 1
    _max_fps = 10

    # Read-Only model-dependent variables
    _min_zoom = _max_zoom = None

    # Others
    _gm = None
    _old_gm = None

    #
    #               Constructor
    #

    def __init__(self):
        super(GrowthMediumCTRL, self).__init__()
        self.round = 0
        self.fps = 1
        self.gm_min_rows = self.gm_cur_rows = GrowthMedium._min_rows
        self.gm_min_cols = self.gm_cur_cols = GrowthMedium._min_cols
        self._min_zoom = self.zoom = GrowthMedium._min_zoom
        self._max_zoom = GrowthMedium._max_zoom
        self.can_run = self.is_running = self.path_exists = self.custom_gm = False
        self.path = ''
        self.pos_x = self.pos_y = 0.5
        self._gm = GrowthMedium.set([[0] * self.gm_cur_cols] * self.gm_cur_rows)
        _, _, self.gm_state_grid = self._gm.get_state_grid(0)

    #
    #               Basic Evolution Controls
    #

    def start_evolution(self) -> None:
        """ Start the evolution.

        This method manages the start of the evolution from a custom state or a loaded one.

        :rtype: None

        """
        if self.custom_gm:
            self._set_custom_growth_medium()
        if self.can_run:
            self.is_running = True
            Clock.schedule_interval(self.update_state_grid, 1.0 / self.fps)
        else:
            raise SystemError('can not start')

    def pause_evolution(self) -> None:
        """ Stop the evolution.

        This method stops the current evolution.

        :rtype: None

        """
        self.is_running = False
        Clock.unschedule(self.update_state_grid)

    def clear_evolution(self) -> None:
        """ Clear the evolution.

        This method clears the current state grid deleting all the current data.

        :rtype: None

        """
        if self.is_running:
            self.pause_evolution()
        if self.custom_gm:
            self.custom_gm = False
            self._old_gm = None
        self.can_run = False
        self._gm = None
        self.round = 0
        self._gm = GrowthMedium.set([[0] * self.gm_cur_cols] * self.gm_cur_rows)
        _, _, self.gm_state_grid = self._gm.get_state_grid(0)
        if sum(self.gm_state_grid) == 0:
            self.can_run = False

    def reset_evolution(self) -> None:
        """ Reset the evolution.

        This method resets the current evolution, the state grid returns to the last init state (loaded or custom).

        :rtype: None

        """
        if self.is_running:
            self.pause_evolution()
        if self.can_run or self._gm is not None:
            if not self.can_run:
                self.can_run = True
            if self.custom_gm:
                self._gm = self._old_gm
                self._old_gm = None
                self.custom_gm = False
            self.round = 0
            _, _, self.gm_state_grid = self._gm.get_state_grid(0)
            if sum(self.gm_state_grid) == 0:
                self.can_run = False
        else:
            raise SystemError('can not reset')

    #
    #               View Evolution Controls
    #

    def increase_fps(self) -> None:
        """ Increase state update frequency.

        This method increase the state update request frequency.

        :rtype: None

        """
        if self.fps < self._max_fps:
            self.fps += 1
            self._update_speed_evolution()

    def decrease_fps(self) -> None:
        """ Increase state update frequency.

        This method decrease the state update request frequency.

        :rtype: None

        """
        if self.fps > self._min_fps:
            self.fps -= 1
            self._update_speed_evolution()

    def _update_speed_evolution(self):
        if self.is_running:
            Clock.unschedule(self.update_state_grid)
            self.update_state_grid()
            Clock.schedule_interval(self.update_state_grid, 1.0 / self.fps)

    def decrease_zoom(self):
        """ Increase the current grid dimension.

        This method increase the current grid dimension.

        :rtype: None

        """
        if self.zoom < self._max_zoom:
            self._update_grid(self._gm.increase_state_grid_dimension())

    def increase_zoom(self) -> None:
        """ Decrease the current grid dimension.

        This method decrease the current grid dimension.

        :rtype: None

        """
        if self.zoom > self._min_zoom:
            self._update_grid(self._gm.decrease_state_grid_dimension())

    def move_right(self) -> None:
        """ Move right.

        This method moves the current grid view to the right side.

        :rtype: None

        """
        self._update_grid(self._gm.shift_grid_right())

    def move_left(self) -> None:
        """ Move Left.

        This method moves the current grid view to the left side.

        :rtype: None

        """
        self._update_grid(self._gm.shift_grid_left())

    def move_up(self) -> None:
        """ Move up.

        This method moves the current grid view to the top side.

        :rtype: None

        """
        self._update_grid(self._gm.shift_grid_up())

    def move_down(self) -> None:
        """ Move down.

        This method moves the current grid view to the bottom side.

        :rtype: None

        """
        self._update_grid(self._gm.shift_grid_down())

    def _update_grid(self, data):
        self.zoom = data['zoom']
        self.gm_cur_rows = data['rows']
        self.gm_cur_cols = data['cols']
        self.pos_x = data['hpos']
        self.pos_y = data['vpos']
        self.gm_state_grid = data['grid']

    #
    #               Grid State Controls
    #

    def update_state_grid(self, *args) -> None:
        """ Update the current state.

        This method updates the current grid state on the next state.

        :param args: arguments about the moment when che update is request
        :return None
        :type args: float
        :rtype: None

        """
        if self.can_run:
            self.round += 1
            _extinction, _steady_state, self.gm_state_grid = self._gm.get_state_grid(self.round)
            if _extinction or _steady_state:
                self.pause_evolution()
                self.can_run = False
        else:
            raise SystemError('can not run')

    def update_custom_growth_medium(self, i: int, j: int) -> None:
        """ Update the current grid.

        This method updates a selected cell in the grid with a user defined state.

        :param i: row of the selected cell
        :param j: column of the selected cell
        :return None
        :type i: int
        :type j: int
        :rtype: None

        """
        if not self.custom_gm:
            self.custom_gm = True
            self._old_gm = self._gm
            self._gm = copy(self._old_gm)
            if not self.can_run:
                self.can_run = True
        self.gm_state_grid = self._gm.update_init_grid_cell(i, j)
        if sum(self.gm_state_grid) == 0:
            self.can_run = False

    def _set_custom_growth_medium(self):
        self.custom_gm = False
        self._old_gm = None
        self.round = 0
        _, _, self.gm_state_grid = self._gm.get_state_grid(0)

    #
    #               Files I/O Controls
    #

    def load_growth_medium(self) -> None:
        """ Load a saved initial state.

        This method loads a saved initial state from a file previously selected.

        :rtype: None

        """
        if self.path_exists:
            self._gm = GrowthMedium.load(self.path, self.zoom)
            self.gm_cur_rows = self._gm.cur_rows
            self.gm_cur_cols = self._gm.cur_cols
            self.zoom = self._gm.cur_zoom
            self.pos_x = self.pos_y = 0.5
            self.can_run = True
            self.round = 0
            _, _, self.gm_state_grid = self._gm.get_state_grid(0)
            self.clear_path()
        else:
            raise FileExistsError('\'{}._gm\' does not exists'.format(self.path))

    def get_growth_medium_files(self) -> list:
        """ Get all saved initial states.

        This method returns the list of all saved initial states.

        :return: list of file names
        :rtype: list

        """
        return GrowthMedium.get_growth_medium_files()

    def save_growth_medium(self) -> None:
        """ Save the current state.

        This method saves the current state in a file previously selected.

        :rtype: None

        """
        if not self.path_exists and self.is_path_valid:
            self._gm.save(self.path)
            self.clear_path()

    def check_growth_medium_name(self, name: str) -> None:
        """ Check the existence of a GrowthMedium File.

        This method saves the current state in a file previously selected, the result is stored on public Properties.

        :param name: the file
        :return None
        :type name: str
        :rtype: None

        """
        self.path = name
        if not self.path:
            self.path_exists = False
            self.is_path_valid = False
        else:
            self.is_path_valid = True
            self.path_exists = GrowthMedium.exists_growth_medium(name)

    def clear_path(self) -> None:
        """ Clear current path.

        This method clears the current saved path for file I/O.

        :rtype: None

        """
        self.path = ''

