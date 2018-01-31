import GameOfLife
from numpy import array
from os import listdir
from os.path import exists, dirname, abspath
from re import match
from scipy.signal import convolve2d


class GrowthMedium:
    """ GrowthMedium represents the model of the Game Of Life.

    This class carry abstractions and methods to model the cell's grid in the Game.

    """

    # Variables used to manage size and position of visible grid
    _min_rows = cur_rows = 10
    _min_cols = cur_cols = 16

    _min_zoom = cur_zoom = 1
    _max_zoom = 10

    rows_shift = 0
    cols_shift = 0

    # Variables used to hide and manage errors caused by finite grid (should be infinite)
    _hidden_rows = int(_min_rows / 2)
    _hidden_cols = int(_min_cols / 2)

    sml_flat_earth_fallen = array([])
    big_flat_earth_fallen = array([])

    # Variables used to manage states of the system
    init_grid = array([])

    cur_state_grid = []

    lifetime = array([])

    _ancient_threshold = 4

    _neighbors_filter = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]

    #
    #               Static Factories, Copy And Files Managers
    #

    @staticmethod
    def set(initial_state: array([[]]), zoom: int = 1) -> object:
        """ Static Constructor, gets the initial grid and a minimum zoom required. Returns a GrowthMedium instance.

        The initial_state is a 2D numpy array in {0, 1}, who represent the initial state of each cell: dead or alive.
        Zoom defines the minimum zoom required by the GrowthMediumCtrl, if it is not enough to include all the
        initial cell the grid will be expanded as required at most _max_zoom.

        :param initial_state: initial_state 2D numpy array that represents the initial state for the evolution
        :param zoom: the minimum zoom required by the controller
        :return the associated GrowthMedium instance
        :type initial_state: numpy.array([[]])
        :type zoom: int
        :rtype: GrowthMedium

        """
        gm = GrowthMedium()

        rows = len(initial_state)
        cols = len(initial_state[0])

        if rows == 0 or cols == 0:
            raise ImportError('Growth Medium rows or cols is 0')

        if GrowthMedium._min_zoom < zoom <= GrowthMedium._max_zoom:
            _zoom = zoom
        else:
            _zoom = 1

        r_zoom = rows / gm._min_rows if rows % gm._min_rows == 0 else int(rows / gm._min_rows) + 1
        c_zoom = cols / gm._min_cols if cols % gm._min_cols == 0 else int(cols / gm._min_cols) + 1

        gm.cur_zoom = int(max(r_zoom, c_zoom, _zoom))
        if gm.cur_zoom > GrowthMedium._max_zoom:
            raise ImportError('Growth Medium is too large')

        gm.cur_rows = gm._min_rows * gm.cur_zoom
        gm.cur_cols = gm._min_cols * gm.cur_zoom

        gm.rows_shift = int((gm._max_zoom - gm.cur_zoom + 1) * (gm._min_rows / 2))
        gm.cols_shift = int((gm._max_zoom - gm.cur_zoom + 1) * (gm._min_cols / 2))

        load_rows_shift = gm.rows_shift + int(((gm.cur_rows - rows) / 2))
        load_cols_shift = gm.cols_shift + int(((gm.cur_cols - cols) / 2))

        _tot_cols = gm._min_cols * (gm._max_zoom + 1)
        _tot_rows = gm._min_rows * (gm._max_zoom + 1)

        gm.init_grid = array([[0] * _tot_cols] * _tot_rows)

        gm.init_grid[load_rows_shift:rows + load_rows_shift,
                     load_cols_shift:cols + load_cols_shift] = array(initial_state)

        gm.sml_flat_earth_fallen = array([[False] * _tot_cols] * _tot_rows)
        gm.sml_flat_earth_fallen[1:-1, 1:-1] = array([[True] * (_tot_cols - 2)] * (_tot_rows - 2))

        gm.big_flat_earth_fallen = array([[False] * _tot_cols] * _tot_rows)
        gm.big_flat_earth_fallen[3:-3, 3:-3] = array([[True] * (_tot_cols - 6)] * (_tot_rows - 6))

        return gm

    @staticmethod
    def load(file: str, zoom: int=1) -> object:
        """ Static Constructor, gets a file name and a minimum zoom required. Returns a GrowthMedium instance.

        GrowthMedium files (.gm) are loaded from a directory in the GameOfLife package.
        Zoom defines the minimum zoom required by the GrowthMediumCtrl, if it is not enough to include all the
        initial cell the grid will be expanded as required at most _max_zoom.

        :param file: the name of the saved initial state
        :param zoom: the minimum zoom required by the controller
        :return the associated GrowthMedium instance
        :type file: str
        :type zoom: int
        :rtype: GrowthMedium

        """
        path = '{}/growth_mediums/{}.gm'.format(dirname(abspath(GameOfLife.__file__)), file)
        if exists(path):
            grid = []
            with open(path, 'r') as f:
                for line in f:
                    row = match('[01]*', line)[0]
                    if len(row) > 0:
                        grid.append(list(row))
            num_cols = max([len(row) for row in grid])
            if [True for row in grid if num_cols != len(row)]:
                raise SyntaxError('Wrong file structure in {}.gm'.format(file))
            return GrowthMedium.set(grid, zoom)
        else:
            raise FileExistsError('{}.gm does not exists'.format(file))

    @staticmethod
    def exists_growth_medium(file: str) -> bool:
        path = '{}/growth_mediums/{}.gm'.format(dirname(abspath(GameOfLife.__file__)), file)
        return exists(path)

    @staticmethod
    def get_growth_medium_files() -> list(str()):
        """ Get the list of GrowthMedium files stored.

        This static method inspects the store directory in the GameOfLife package and returns the list of all
        GrowthMedium files (.gm) stored.

        :return the list of GrowthMedium files names
        :rtype: list(str())

        """
        path = '{}/growth_mediums'.format(dirname(abspath(GameOfLife.__file__)))
        return sorted([x[0:-3] for x in listdir(path) if x.endswith('.gm')])

    def save(self, file: str) -> None:
        """ Save the current Growth Medium in a file.

        This method saves the current initial state of the GrowthMedium in the store directory of the GameOfLife package
        with the file name chosen and the extension '.gm'.
        Furthermore check the presence of life and compress the space to the minimum rectangle with alive cells.

        :param file: the name of the file where the GrowthMedium will be saved
        :return this method has no return
        :type file: str
        :rtype: None

        """
        path = '{}/growth_mediums/{}.gm'.format(dirname(abspath(GameOfLife.__file__)), file)
        if not exists(path):
            if len(self.cur_state_grid) == 0:
                state_grid = self.init_grid
            else:
                state_grid = (self.cur_state_grid > 0) * 1
            if sum(state_grid.ravel()) > 0:
                _mr = _MR = _mc = _MC = 0
                for i in range(self.cur_rows):
                    for j in range(self.cur_cols):
                        if state_grid[self.rows_shift+i, self.cols_shift+j] > 0:
                            if _mr == 0 and _mc == 0:
                                _mr = _MR = i
                                _mc = _MC = j
                            else:
                                _mr = min(i, _mr)
                                _MR = max(i, _MR)
                                _mc = min(j, _mc)
                                _MC = max(j, _MC)
                rows = _MR - _mr + 1
                cols = _MC - _mc + 1
                grid = state_grid[self.rows_shift + _mr: self.rows_shift + _MR + 1,
                                  self.cols_shift + _mc: self.cols_shift + _MC + 1].ravel()
                with open(path, 'w+') as f:
                    for i in range(rows):
                        f.write(''.join(map(str, grid[i * cols:((i + 1) * cols)])) + '\n')
            else:
                raise ImportError('Empty initial state')
        else:
            raise FileExistsError('{}.gm already exists'.format(file))

    def __copy__(self) -> object:
        """ Make a copy of the GrowthMedium.

        This method makes a copy of the relevant attributes of the GrowthMedium, it ignores the transient variables
        used during the evolution.
        used during the evolution.

        :return a copy of the GrowthMedium
        :rtype: GrowthMedium

        """
        gm = GrowthMedium()
        gm.cur_zoom = self.cur_zoom
        gm.cur_rows = self.cur_rows
        gm.cur_cols = self.cur_cols
        gm.rows_shift = self.rows_shift
        gm.cols_shift = self.cols_shift
        gm.init_grid = (self.cur_state_grid > 0) * 1
        gm.sml_flat_earth_fallen = self.sml_flat_earth_fallen
        gm.big_flat_earth_fallen = self.big_flat_earth_fallen
        return gm

    #
    #               State Grid Getter And Setter
    #

    def get_state_grid(self, t: int) -> array([[]]):
        """ Return the updated state.

        This method calculates che new grid state from the last one in memory, if t = 0 it will load the initial state.
        To try to preserve the consistency of visible state grid, part of the hidden one is erased on regular times.

        :param t: the time in which test the grid state
        :return the 2D array with the updated cells' state {0 -> dead, 1 -> alive, 2 -> ancient}
        :type t: int
        :rtype: array([[]])

        """
        _steady_state = False
        _extinction = False
        if t == 0:
            self.cur_state_grid = self.init_grid
            self.lifetime = array([[0] * self._min_cols * (self._max_zoom + 1)] * self._min_rows * (self._max_zoom + 1))
        else:
            prev_state_grid = self.cur_state_grid

            prev_alive = (self.cur_state_grid > 0) * 1

            cur_neighbors = convolve2d(prev_alive, self._neighbors_filter, mode='same')
            cur_alive_map = (((cur_neighbors == 2) * (prev_alive > 0)) + (cur_neighbors == 3))
            if t % 10 == 0:
                self.lifetime = cur_alive_map * (self.lifetime + 1) * self.big_flat_earth_fallen
            elif t % 5 == 0:
                self.lifetime = cur_alive_map * (self.lifetime + 1) * self.sml_flat_earth_fallen
            else:
                self.lifetime = cur_alive_map * (self.lifetime + 1)

            self.cur_state_grid = ((self.lifetime > 0) * (self.lifetime < self._ancient_threshold) * 1) \
                                    + ((self.lifetime >= self._ancient_threshold) * 2)

            hr = self._hidden_rows
            hc = self._hidden_cols
            if sum(sum(self.cur_state_grid[hr:-hr, hc:-hc])) > 0:
                if (self.cur_state_grid[hr:-hr, hc:-hc] == prev_state_grid[hr:-hr, hc:-hc]).all():
                    _steady_state = True
                    self.cur_state_grid = (self.cur_state_grid > 0) * 2
            else:
                _extinction = True

        return _extinction, _steady_state, self.cur_state_grid[self.rows_shift:self.rows_shift+self.cur_rows,
                                                               self.cols_shift:self.cols_shift+self.cur_cols].ravel()

    def update_init_grid_cell(self, i: int, j: int) -> array([[]]):
        """ Set a custom modification of current init grid.

        This method modifies the initial state grid with born of death of a single cell at time.

        :param i: the row of the cell to born/kill
        :param j: the column of the cell to born/kill
        :return the updated initial state
        :type i: int
        :type j: int
        :rtype: array([[]])

        """
        if i < 0 or i >= self.cur_rows or j < 0 or j >= self.cur_cols:
            raise IndexError('Cell ({}, {}) out of feasible range'.format(i, j))
        _state = self.init_grid[self.rows_shift + i, self.cols_shift + j]
        self.init_grid[self.rows_shift + i, self.cols_shift + j] = (_state + 1) % 2
        return self.init_grid[self.rows_shift:self.rows_shift+self.cur_rows,
                              self.cols_shift:self.cols_shift+self.cur_cols].ravel()

    #
    #               Move Visible Grid Methods
    #

    def _get_grid_data(self):
        _data = {'zoom': self.cur_zoom,
                 'rows': self.cur_rows,
                 'cols': self.cur_cols,
                 'hpos': (self.cols_shift + (self.cur_cols / 2) - (self._min_cols / 2)) / ((self._max_zoom) * self._min_cols),
                 'vpos': (self.rows_shift + (self.cur_rows / 2) - (self._min_rows / 2)) / ((self._max_zoom) * self._min_rows)}
        if len(self.cur_state_grid) == 0:
            _data['grid'] = self.init_grid[self.rows_shift:self.rows_shift + self.cur_rows,
                                           self.cols_shift:self.cols_shift + self.cur_cols].ravel()
        else:
            _data['grid'] = self.cur_state_grid[self.rows_shift:self.rows_shift + self.cur_rows,
                                                self.cols_shift:self.cols_shift + self.cur_cols].ravel()
        return _data

    def increase_state_grid_dimension(self) -> dict:
        """ Increase the visible GrowthMedium dimension.

        This method tries to increase the dimension of the visible GrowthMedium, updating the corresponding values.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.cur_zoom < self._max_zoom:
            self.cur_zoom += 1
            self.cur_rows += self._min_rows
            self.cur_cols += self._min_cols
            if self._min_rows <= self.rows_shift <= (self._min_rows * (self._max_zoom+1)) - self.cur_rows:
                self.rows_shift -= int(self._min_rows / 2)
            else:
                if self.rows_shift > (self._min_rows * (self._max_zoom+1)) - self.cur_rows:
                    self.rows_shift -= self._min_rows
                elif self.rows_shift > self._min_rows:
                    self.rows_shift -= (self.rows_shift - int(self._min_rows / 2)) % self._min_rows
                else:
                    self.rows_shift -= self.rows_shift % int(self._min_rows / 2)
            if self._min_cols <= self.cols_shift <= (self._min_cols * (self._max_zoom+1)) - self.cur_cols:
                self.cols_shift -= int(self._min_cols / 2)
            else:
                if self.cols_shift > (self._min_cols * (self._max_zoom+1)) - self.cur_cols:
                    self.cols_shift -= self._min_cols
                elif self.cols_shift > self._min_cols:
                    self.cols_shift -= (self.cols_shift - int(self._min_cols / 2)) % self._min_cols
                else:
                    self.cols_shift -= self.cols_shift % int(self._min_cols / 2)
            return self._get_grid_data()
        else:
            raise IndexError('Zoom out of range')

    def decrease_state_grid_dimension(self) -> dict:
        """ Decrease the visible GrowthMedium dimension.

        This method tries to decrease the dimension of the visible GrowthMedium, updating the corresponding values.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.cur_zoom > self._min_zoom:
            self.cur_zoom -= 1
            self.cur_rows -= self._min_rows
            self.cur_cols -= self._min_cols
            self.rows_shift += int(self._min_rows / 2)
            self.cols_shift += int(self._min_cols / 2)
            return self._get_grid_data()
        else:
            raise IndexError('Zoom out of range')

    def shift_grid_right(self) -> dict:
        """ Move the current visible grid one column to the right.

        This method tries to move the current visible grid one column to the right.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.cols_shift + self.cur_cols < self._min_cols * (self._max_zoom + 0.5):
            self.cols_shift += 1
        return self._get_grid_data()

    def shift_grid_left(self) -> dict:
        """ Move the current visible grid one column to the left.

        This method tries to move the current visible grid one column to the left.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.cols_shift > int(self._min_cols / 2):
            self.cols_shift -= 1
        return self._get_grid_data()

    def shift_grid_up(self) -> dict:
        """ Move the current visible grid one row to the top.

        This method tries to move the current visible grid one row to the top, for the representation this mean move
        the grid to the bottom.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.rows_shift > int(self._min_rows / 2):
            self.rows_shift -= 1
        return self._get_grid_data()

    def shift_grid_down(self) -> dict:
        """ Move the current visible grid one row to the bottom.

        This method tries to move the current visible grid one row to the bottom, for the representation this mean move
        the grid to the top.

        :return return a dict with the updated variables :
                * **zoom**: the current zoom
                * **rows**: the current number of rows
                * **cols**: the current number of columns
                * **hpos**: the current position of col center respect all explorable grid (percentage)
                * **vpos**: the current position of row center respect all explorable grid (percentage)
        :rtype: dict

        """
        if self.rows_shift + self.cur_rows < self._min_rows * (self._max_zoom + 0.5):
            self.rows_shift += 1
        return self._get_grid_data()
