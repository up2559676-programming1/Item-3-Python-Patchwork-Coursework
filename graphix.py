# pyright: reportUnnecessaryIsInstance=false

"""graphix - a simple object oriented graphics library

The library is designed to make it very easy for novice programmers to
experiment with computer graphics in an object oriented fashion. It is a
modified version of John Zelle's graphics.py module which was written
for use with the book "Python Programming: An Introduction to Computer
Science" (Franklin, Beedle & Associates).

The modifications made are to better support the M30299 Programming
module at the University of Portsmouth; they include the use of properties
in place of getter and setter methods, the use of snake case for names,
simplifying all coordinates to be integers, and the removal of some unused
features.

LICENSE: This is open-source software released under the terms of the
GPL (http://www.gnu.org/licenses/gpl.html).

PLATFORMS: The package is a wrapper around Tkinter and should run on
any platform where Tkinter is available.

INSTALLATION: Put this file somewhere where Python can see it.

OVERVIEW: There are two kinds of objects in the library. The Window
class implements a window where drawing can be done and various
GraphixObjects are provided that can be drawn into a Window. As a
simple example, here is a complete program to draw a circle of radius
10 centred in a 200x200 window:

--------------------------------------------------------------------
from graphix import Window, Circle, Point

def main():
    w = Window("My Circle", 200, 200)
    c = Circle(Point(50,50), 10)
    c.draw(w)
    w.get_mouse() # Pause to view result
    w.close()    # Close window when done

main()
--------------------------------------------------------------------
Window objects support mouse and keyboard interaction methods.

The library provides the following graphical classes:
    Point
    Line
    Circle
    Oval
    Rectangle
    Polygon
    Text
    Entry (for text-based input)

Various attributes of graphical objects can be set such as
outline-colour, fill-colour and line-width. Graphical objects also
support moving and hiding for animation effects.
"""

from __future__ import annotations
import time
import tkinter as tk
from typing import Any, cast
from abc import ABC, abstractmethod

__version__ = "1.0"
__author__ = "John Zelle (original), Matthew Poole (modifications)"


##########################################################################
# Module Exceptions


class GraphixError(Exception):
    """Generic error class for graphics module exceptions."""


OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"

##########################################################################
# global variables and functions

_root = tk.Tk()
_root.withdraw()

_update_lasttime = time.time()


def update(rate: int | None = None) -> None:
    """Force pending graphics updates to be applied to be displayed."""
    global _update_lasttime
    if rate:
        now = time.time()
        pause_length = 1 / rate - (now - _update_lasttime)
        if pause_length > 0:
            time.sleep(pause_length)
            _update_lasttime = now + pause_length
        else:
            _update_lasttime = now

    _root.update()


############################################################################
# Graphics classes start here


class Window(tk.Canvas):
    """A Window is a toplevel window for displaying graphics."""

    __slots = [
        "_items",
        "_mouse_x",
        "_mouse_y",
        "master",
        "tk",
        "_autoflush",
        "_name",
        "_w",
        "children",
        "_tclCommands",
        "background_colour",
        "_mouse_callback",
        "_closed",
        "_last_key",
        "widgetName",
    ]

    __readonly = ["width", "height"]

    def __init__(
        self,
        title: str = "Graphix Window",
        width: int = 400,
        height: int = 400,
        autoflush: bool = True,
    ) -> None:
        """Initialises and opens a graphics window."""
        if not isinstance(title, str):
            raise GraphixError("Window title must be a string")
        if not isinstance(width, int) or not isinstance(height, int):
            raise GraphixError("Window dimensions must be integers")
        if not isinstance(autoflush, bool):
            raise GraphixError("Window autoflush must be a boolean")

        master = tk.Toplevel(_root)
        master.protocol("WM_DELETE_WINDOW", self.close)
        tk.Canvas.__init__(
            self, master, width=width, height=height, highlightthickness=0, bd=0
        )
        self.master.title(title)
        self.master.attributes("-topmost", True)
        self.pack()
        master.resizable(0, 0)
        # self.foreground = "black"
        self._items: list[GraphixObject] = []
        self._mouse_x = None
        self._mouse_y = None
        self.bind("<Button-1>", self._on_click)
        self.bind_all("<Key>", self._on_key)
        self._autoflush = autoflush
        self._mouse_callback = None
        self._closed = False
        self.background_colour = "white"
        master.lift()
        self._last_key = ""
        if autoflush:
            _root.update()

    def __repr__(self) -> str:
        """Returns a string representation of the window."""
        if self.is_closed():
            return "<Closed Window>"
        else:
            return f"Window('{self.master.title()}', {self.width}, {self.height})"

    def __str__(self) -> str:
        """Returns a string representation of the window."""
        return self.__repr__()

    def __getattr__(self, name) -> Any:
        raise AttributeError(f"'Window' object has no attribute '{name}'")

    def __setattr__(self, name, value) -> None:
        if name in self.__slots:
            super(Window, self).__setattr__(name, value)
        elif name in self.__readonly:
            raise AttributeError(f"can't set attribute '{name}'")
        else:
            raise AttributeError(f"'Window' object has no attribute '{name}'")

    @property
    def background_colour(self) -> str:
        """The background colour of the window."""
        return self.cget("bg")

    @background_colour.setter
    def background_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Background colour must be a string")
        self.__check_open()
        self.config(bg=colour)
        self.__autoflush()

    @property
    def height(self) -> int:
        """The height of the window."""
        return int(self.cget("height"))

    @property
    def width(self) -> int:
        """The width of the window."""
        return int(self.cget("width"))

    def get_mouse(self) -> Point:
        """Waits for a mouse click and returns a Point object representing the
        click."""
        self.update()  # flush any prior clicks
        self._mouse_x = None
        self._mouse_y = None
        while self._mouse_x is None or self._mouse_y is None:
            self.update()
            if self.is_closed():
                raise GraphixError("get_mouse in closed window")
            time.sleep(0.1)  # give up thread
        x, y = cast(int, self._mouse_x), cast(int, self._mouse_y)
        self._mouse_x = None
        self._mouse_y = None
        return Point(x, y)

    def check_mouse(self) -> Point | None:
        """Returns last mouse click or None if mouse has not been clicked
        since last call"""
        if self.is_closed():
            raise GraphixError("check_mouse in closed window")
        self.update()
        if self._mouse_x is not None and self._mouse_y is not None:
            x, y = self._mouse_x, self._mouse_y
            self._mouse_x = None
            self._mouse_y = None
            return Point(cast(int, x), cast(int, y))
        else:
            return None

    def get_key(self) -> str:
        """Waits for user to press a key and returns it as a string."""
        self._last_key = ""
        while self._last_key == "":
            self.update()
            if self.is_closed():
                raise GraphixError("get_key in closed window")
            time.sleep(0.1)  # give up thread

        key = self._last_key
        self._last_key = ""
        return key

    def check_key(self) -> str | None:
        """Returns last key pressed or None if no key pressed since
        last call."""
        if self.is_closed():
            raise GraphixError("check_key in closed window")
        self.update()
        key = self._last_key
        self._last_key = ""
        return key

    def close(self) -> None:
        """Closes the window."""
        if self._closed:
            return
        self._closed = True
        self.master.destroy()
        self.__autoflush()

    def is_closed(self) -> bool:
        """Returns True if window closed; False otherwise."""
        return self._closed

    def is_open(self) -> bool:
        """Returns True if window open; False otherwise."""
        return not self._closed

    def flush(self) -> None:
        """Updates drawing to the window."""
        self.__check_open()
        self.update_idletasks()

    def redraw(self) -> None:
        """Redraws all objects on the window."""
        for item in self._items[:]:
            item.undraw()
            item.draw(self)
        self.update()

    def __autoflush(self):
        if self._autoflush:
            _root.update()

    def _set_mouse_handler(self, func):
        self._mouse_callback = func

    def _on_click(self, e):
        self._mouse_x = e.x
        self._mouse_y = e.y
        if self._mouse_callback:
            self._mouse_callback(Point(e.x, e.y))

    def _add_item(self, item: GraphixObject) -> None:
        self._items.append(item)

    def _del_item(self, item: GraphixObject) -> None:
        self._items.remove(item)

    def __check_open(self):
        if self._closed:
            raise GraphixError("window is closed")

    def _on_key(self, event):
        self._last_key = event.keysym


# Default values for various item configuration options. Only a subset of
#   keys may be present in the configuration dictionary for a given item
DEFAULT_CONFIG = {
    "fill": "",
    "outline": "black",
    "width": "1",
    "arrow": "none",
    "text": "",
    "justify": "center",
    "font": ("helvetica", 12, "normal"),
}


class GraphixObject(ABC):
    """Generic base class for all of the drawable objects"""

    __slots__ = ["_canvas", "_id", "_config"]

    def __init__(self, options) -> None:
        # options is a list of strings indicating which options are
        # legal for this object.

        # When an object is drawn, canvas is set to the Window(canvas)
        #    object where it is drawn and id is the TK identifier of the
        #    drawn shape.
        self._canvas = None
        self._id = None

        # config is the dictionary of configuration options for the widget.
        config = {}
        for option in options:
            config[option] = DEFAULT_CONFIG[option]
        self._config = config

    def __str__(self) -> str:
        # all subclasses must implement __repr__
        return self.__repr__()

    def __getattr__(self, name) -> Any:
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    @property
    def fill_colour(self) -> str:
        """The interior colour of the object."""
        return cast(str, self._config["fill"])

    @fill_colour.setter
    def fill_colour(self, colour) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Fill colour must be a string")
        self._reconfig("fill", colour)

    @property
    def outline_colour(self) -> str:
        """The outline colour of the object."""
        return cast(str, self._config["outline"])

    @outline_colour.setter
    def outline_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Outline colour must be a string")
        self._reconfig("outline", colour)

    @property
    def outline_width(self) -> int:
        """The outline width of the object."""
        return cast(int, self._config["width"])

    @outline_width.setter
    def outline_width(self, width: int) -> None:
        if not isinstance(width, int):
            raise GraphixError("Outline width must be an integer")
        self._reconfig("width", width)

    def draw(self, window: Window) -> None:
        """Draws the object in window, which should be a Window object.
        A GraphixObject may only be drawn into one window. Raises an error if
        attempt made to draw an object that is already visible."""
        if not isinstance(window, Window):
            raise GraphixError("Object must be drawn in a Window")
        if self._canvas and not self._canvas.is_closed():
            raise GraphixError(OBJ_ALREADY_DRAWN)
        if window.is_closed():
            raise GraphixError("Can't draw to closed window")
        self._canvas = window
        self._id = self._draw(window, self._config)
        window._add_item(self)
        if window._autoflush:
            _root.update()

    def undraw(self) -> None:
        """Undraws the object (i.e. hides it). Returns silently if the
        object is not currently drawn."""
        if not self._canvas:
            return
        if not self._canvas.is_closed():
            self._canvas.delete(cast(str | int, self._id))
            self._canvas._del_item(self)
            if self._canvas._autoflush:
                _root.update()
        self._canvas = None
        self._id = None

    def is_drawn(self) -> bool:
        """Returns True if object is currently drawn, False otherwise."""
        return self._canvas is not None

    def move(self, dx: int, dy: int) -> None:
        """Moves object dx units in x direction and dy units in y
        direction."""
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise GraphixError("Move distances must be integers")
        self._move(dx, dy)
        canvas = self._canvas
        if canvas and not canvas.is_closed():
            x = dx
            y = dy
            self._canvas.move(self._id, x, y)
            if canvas._autoflush:
                _root.update()

    def _reconfig(self, option, setting):
        # Internal method for changing configuration of the object
        # Raises an error if the option does not exist in the config
        #    dictionary for this object
        if option not in self._config:
            raise GraphixError(UNSUPPORTED_METHOD)
        options = self._config
        options[option] = setting
        if self._canvas and not self._canvas.is_closed():
            self._canvas.itemconfig(self._id, options)
            if self._canvas._autoflush:
                _root.update()

    @abstractmethod
    def _draw(self, canvas, options):
        """draws appropriate figure on canvas with options provided
        Returns Tk id of item drawn"""

    @abstractmethod
    def _move(self, dx, dy):
        """Updates internal state of object to move it dx,dy units"""


class Point(GraphixObject):
    """A class representing a point with integer coordinates in 2D space."""

    __slots__ = ["_x", "_y"]

    def __init__(self, x: int, y: int) -> None:
        """Inititialises the point with x and y coordinates."""
        if not isinstance(x, int) or not isinstance(y, int):
            raise GraphixError("Point coordinates must be integers")
        GraphixObject.__init__(self, ["outline", "fill"])
        self._x = x
        self._y = y

    def __repr__(self):
        """Returns a string representation of the point."""
        return f"Point({self.x}, {self.y})"

    # setting fill_colour to be the same as outline_colour

    @property
    def x(self) -> int:
        """The x coordinate of the point."""
        return self._x

    @property
    def y(self) -> int:
        """The y coordinate of the point."""
        return self._y

    @property
    def fill_colour(self) -> str:
        """The interior colour of the point."""
        return self.outline_colour

    @fill_colour.setter
    def fill_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Fill colour must be a string")
        self.outline_colour = colour

    def clone(self) -> Point:
        """Returns a clone of the point."""
        other = Point(self.x, self.y)
        other._config = self._config.copy()
        return other

    def _draw(self, canvas, options):
        x, y = self.x, self.y
        return canvas.create_rectangle(x, y, x + 1, y + 1, options)

    def _move(self, dx, dy):
        self._x = self._x + dx
        self._y = self._y + dy


class _BBox(GraphixObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.

    __slots__ = ["_p1", "_p2"]

    def __init__(self, p1: Point, p2: Point, options=None) -> None:
        if options is None:
            options = ["outline", "width", "fill"]
        GraphixObject.__init__(self, options)
        self._p1 = p1.clone()
        self._p2 = p2.clone()

    def _move(self, dx, dy):
        self._p1.move(dx, dy)
        self._p2.move(dx, dy)

    def get_p1(self) -> Point:
        """Returns a clone of the p1 point."""
        return self._p1.clone()

    def get_p2(self) -> Point:
        """Returns a clone of the p2 point"""
        return self._p2.clone()

    def get_centre(self) -> Point:
        """Returns a clone of the centre point."""
        p1 = self._p1
        p2 = self._p2
        return Point((p1.x + p2.x) // 2, (p1.y + p2.y) // 2)


class Rectangle(_BBox):
    """A class representing a rectangle with two opposite points p1 and p2."""

    __slots__ = []

    def __init__(self, p1: Point, p2: Point) -> None:
        """Initialises the rectangle with two opposite points."""
        if not isinstance(p1, Point) or not isinstance(p2, Point):
            raise GraphixError("Rectangle points must be Point objects")
        _BBox.__init__(self, p1, p2)

    def __repr__(self) -> str:
        """Returns a string representaiton of the rectangle."""
        return f"Rectangle({self._p1}, {self._p2})"

    def _draw(self, canvas, options):
        p1 = self._p1
        p2 = self._p2
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        return canvas.create_rectangle(x1, y1, x2, y2, options)

    def clone(self) -> Rectangle:
        """Returns a clone of the rectangle."""
        other = Rectangle(self._p1, self._p2)
        other._config = self._config.copy()
        return other


class Oval(_BBox):
    """A class representing an oval with two opposite bounding-box
    points p1 and p2."""

    __slots__ = []

    def __init__(self, p1: Point, p2: Point) -> None:
        """Initialises the oval with opposite points of bounding-box."""
        if not isinstance(p1, Point) or not isinstance(p2, Point):
            raise GraphixError("Oval points must be Point objects")
        _BBox.__init__(self, p1, p2)

    def __repr__(self) -> str:
        """Returns a string representation of the oval."""
        return f"Oval({self._p1}, {self._p2})"

    def clone(self) -> Oval:
        """Returns a clone of the oval."""
        other = Oval(self._p1, self._p2)
        other._config = self._config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self._p1
        p2 = self._p2
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        return canvas.create_oval(x1, y1, x2, y2, options)


class Circle(Oval):
    """A class representing an circle with centre point and radius."""

    __slots__ = ["_radius"]

    def __init__(self, centre: Point, radius: int) -> None:
        """Initialises the circle with a centre point and radius."""
        if not isinstance(centre, Point):
            raise GraphixError("Circle centre must be a Point object")
        if not isinstance(radius, int):
            raise GraphixError("Circle radius must be an integer")
        p1 = Point(centre.x - radius, centre.y - radius)
        p2 = Point(centre.x + radius, centre.y + radius)
        Oval.__init__(self, p1, p2)
        self._radius = radius

    def __repr__(self) -> str:
        """Returns a string representation of the circle."""
        return f"Circle({self.get_centre()}, {self.radius})"

    def clone(self) -> Rectangle:
        """Returns a clone of the circle."""
        other = Rectangle(self.get_centre(), self.radius)
        other._config = self._config.copy()
        return other

    @property
    def radius(self):
        """The radius of the circle."""
        return self._radius


class Line(_BBox):
    """A class representing a straight line between two points p1 and p2"""

    __slots__ = []

    def __init__(self, p1: Point, p2: Point) -> None:
        """Initialises the line with two end points."""
        if not isinstance(p1, Point) or not isinstance(p2, Point):
            raise GraphixError("Line points must be Point objects")
        _BBox.__init__(self, p1, p2, ["arrow", "fill", "width"])
        self.fill_colour = cast(str, DEFAULT_CONFIG["outline"])

    # setting outline_colour to be the same as fill_colour

    def __repr__(self) -> str:
        """Returns a string representation of the line."""
        return f"Line({self._p1}, {self._p2})"

    @property
    def arrow(self) -> str:
        """The arrow setting for the line."""
        return cast(str, self._config["arrow"])

    @arrow.setter
    def arrow(self, option: str) -> None:
        if not option in ["first", "last", "both", "none"]:
            raise GraphixError(BAD_OPTION)
        self._reconfig("arrow", option)

    @property
    def outline_colour(self) -> str:
        """The outline colour of the line."""
        return self.fill_colour

    @outline_colour.setter
    def outline_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Outline colour must be a string")
        self.fill_colour = colour

    def clone(self) -> Line:
        """Returns a clone of the line."""
        other = Line(self._p1, self._p2)
        other._config = self._config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self._p1
        p2 = self._p2
        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        return canvas.create_line(x1, y1, x2, y2, options)


class Polygon(GraphixObject):
    """A class representing a polygon based on a list of points."""

    __slots__ = ["_points"]

    def __init__(self, points: list[Point]) -> None:
        """Initialises the polygon with a list of points."""
        if not isinstance(points, list):
            raise GraphixError("Polygon points must be a list")
        if not all(isinstance(p, Point) for p in points):
            raise GraphixError("Polygon points must all be Point objects")
        self._points = list(map(Point.clone, points))
        GraphixObject.__init__(self, ["outline", "width", "fill"])

    def __repr__(self):
        """Returns a string representation of the polygon."""
        return f"Polygon({self._points})"

    def clone(self) -> Polygon:
        """Returns a clone of the polygon."""
        other = Polygon(self._points)
        other._config = self._config.copy()
        return other

    def get_points(self) -> list[Point]:
        """Returns a clone of the list of the points in the polygon."""
        return list(map(Point.clone, self._points))

    def _move(self, dx, dy):
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise GraphixError("Move distances must both be integers")
        for p in self._points:
            p.move(dx, dy)

    def _draw(self, canvas, options):
        args = [canvas]
        for p in self._points:
            x, y = p.x, p.y
            args.append(x)
            args.append(y)
        args.append(options)
        return Window.create_polygon(*args)


class Text(GraphixObject):
    """A class representing a text object at an anchor point with some text
    content."""

    __slots__ = ["_anchor"]

    def __init__(self, anchor: Point, text: str) -> None:
        """Initialises the text object with an anchor point and text."""
        if not isinstance(anchor, Point):
            raise GraphixError("Text anchor must be a Point object")
        if not isinstance(text, str):
            raise GraphixError("Text text must be a string")
        GraphixObject.__init__(self, ["justify", "fill", "text", "font"])
        self.text = text
        self._anchor = anchor.clone()
        self.fill_colour = cast(str, DEFAULT_CONFIG["outline"])

    def __repr__(self) -> str:
        """Returns a string representation of the text object."""
        return f"Text({self._anchor}, '{self.text}')"

    @property
    def text_colour(self) -> str:
        """The text colour of the text object."""
        return self.fill_colour

    @text_colour.setter
    def text_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Text colour must be a string")
        self.fill_colour = colour

    # setting outline_colour to be the same as text_colour

    @property
    def outline_colour(self) -> str:
        """The outline colour of the text object."""
        return self.text_colour

    @outline_colour.setter
    def outline_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Outline colour must be a string")
        self.text_colour = colour

    @property
    def text(self) -> str:
        """The text of the text object."""
        return cast(str, self._config["text"])

    @text.setter
    def text(self, text: str) -> None:
        if not isinstance(text, str):
            raise GraphixError("Text must be a string")
        self._reconfig("text", text)

    @property
    def typeface(self) -> str:
        """The typeface of the text object."""
        return cast(str, self._config["font"][0])

    @typeface.setter
    def typeface(self, face: str) -> None:
        if face in ["helvetica", "arial", "courier", "times roman"]:
            _, s, b = self._config["font"]
            self._reconfig("font", (face, s, b))
        else:
            raise GraphixError(BAD_OPTION)

    @property
    def size(self) -> int:
        """The font size of the text object."""
        return cast(int, self._config["font"][1])

    @size.setter
    def size(self, size: int) -> None:
        if not isinstance(size, int):
            raise GraphixError("Font size must be an integer")
        if 5 <= size <= 36:
            f, _, b = self._config["font"]
            self._reconfig("font", (f, size, b))
        else:
            raise GraphixError(BAD_OPTION)

    @property
    def style(self) -> str:
        """The style of the text object."""
        return cast(str, self._config["font"][2])

    @style.setter
    def style(self, style: str) -> None:
        if style in ["bold", "normal", "italic", "bold italic"]:
            f, s, _ = self._config["font"]
            self._reconfig("font", (f, s, style))
        else:
            raise GraphixError(BAD_OPTION)

    def get_anchor(self) -> Point:
        """Returns a clone of the anchor point."""
        return self._anchor.clone()

    def clone(self) -> Text:
        """Returns a clone of the text object."""
        other = Text(self._anchor, self.text)
        other._config = self._config.copy()
        return other

    def _draw(self, canvas, options):
        p = self._anchor
        x, y = p.x, p.y
        return canvas.create_text(x, y, options)

    def _move(self, dx, dy):
        self._anchor.move(dx, dy)


class Entry(GraphixObject):
    """A class representing an text entry box with anchor point and width."""

    __slots__ = [
        "_anchor",
        "_width",
        "_text",
        "_fill_colour",
        "_text_colour",
        "_font",
        "_entry",
    ]

    def __init__(self, anchor: Point, width: int) -> None:
        """Initialises the entry object with an anchor point and width."""
        if not isinstance(anchor, Point):
            raise GraphixError("Entry anchor must be a Point object")
        if not isinstance(width, int):
            raise GraphixError("Entry width must be an integer")
        GraphixObject.__init__(self, [])
        self._anchor = anchor.clone()
        self._width = width
        self._text = tk.StringVar(_root)
        self._text.set("")
        self._fill_colour = "grey"
        self._text_colour = "black"
        self._font = DEFAULT_CONFIG["font"]
        self._entry = None

    def __repr__(self) -> str:
        """Returns a string representation of the entry object."""
        return f"Entry({self._anchor}, {self._width})"

    # setting outline_colour to be the same as text_colour

    @property
    def outline_colour(self) -> str:
        """The outline colour of the entry object."""
        return self.text_colour

    @outline_colour.setter
    def outline_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Outline colour must be a string")
        self.text_colour = colour

    @property
    def text(self) -> str:
        """The text of the entry object."""
        return self._text.get()

    @text.setter
    def text(self, text: str) -> None:
        if not isinstance(text, str):
            raise GraphixError("Text must be a string")
        self._text.set(text)

    @property
    def fill_colour(self) -> str:
        """The interior colour of the entry object."""
        return self._fill_colour

    @fill_colour.setter
    def fill_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Fill colour must be a string")
        self._fill_colour = colour
        if self._entry:
            self._entry.config(bg=colour)

    @property
    def typeface(self) -> str:
        """The typeface of the entry object."""
        return self._get_font_component(0)

    @typeface.setter
    def typeface(self, face: str) -> None:
        if face in ["helvetica", "arial", "courier", "times roman"]:
            self._set_font_component(0, face)
        else:
            raise GraphixError(BAD_OPTION)

    @property
    def size(self) -> int:
        """The font size of the entry object."""
        return self._get_font_component(1)

    @size.setter
    def size(self, size: int) -> None:
        if not isinstance(size, int):
            raise GraphixError("Font size must be an integer")
        if 5 <= size <= 36:
            self._set_font_component(1, size)
        else:
            raise GraphixError(BAD_OPTION)

    @property
    def style(self) -> str:
        """The style of the entry object."""
        return self._get_font_component(2)

    @style.setter
    def style(self, style: str) -> None:
        if style in ["bold", "normal", "italic", "bold italic"]:
            self._set_font_component(2, style)
        else:
            raise GraphixError(BAD_OPTION)

    @property
    def text_colour(self) -> str:
        """The text colour of the object."""
        return self._text_colour

    @text_colour.setter
    def text_colour(self, colour: str) -> None:
        if not isinstance(colour, str):
            raise GraphixError("Text colour must be a string")
        self._text_colour = colour
        if self._entry:
            self._entry.config(fg=colour)

    def get_anchor(self) -> Point:
        """Returns a clone of the anchor point."""
        return self._anchor.clone()

    def clone(self) -> Entry:
        """Returns a clone of the entry object."""
        other = Entry(self._anchor, self._width)
        other._config = self._config.copy()
        # other._text = tk.StringVar()
        # other._text.set(self._text.get())
        other.text = self.text
        return other

    def _draw(self, canvas, options):
        p = self._anchor
        x, y = p.x, p.y
        frm = tk.Frame(canvas.master)
        self._entry = tk.Entry(
            frm,
            width=self._width,
            textvariable=self._text,
            bg=self._fill_colour,
            fg=self._text_colour,
            font=self._font,
        )
        self._entry.pack()
        self._entry.focus_set()
        return canvas.create_window(x, y, window=frm)

    def _move(self, dx, dy):
        self._anchor.move(dx, dy)

    def _set_font_component(self, which, value):
        font = list(self._font)
        font[which] = value
        self._font = tuple(font)
        if self._entry:
            self._entry.config(font=self._font)

    def _get_font_component(self, which):
        return self._font[which]


def test() -> None:
    """A test function for the graphical classes."""
    win = Window()
    t = Text(Point(300, 100), "Centred Text")
    print("Window width is", win.width)
    print("Window height is", win.height)
    t.draw(win)
    p = Polygon([Point(40, 40), Point(200, 120), Point(80, 280)])
    p.draw(win)
    e = Entry(Point(200, 240), 10)
    e.draw(win)

    # mouse click
    win.get_mouse()
    p.fill_colour = "red"
    p.outline_colour = "blue"
    p.outline_width = 3
    t.text = e.text
    e.fill_colour = "green"
    e.text = "Spam!"
    e.move(80, 0)

    # mouse click
    win.get_mouse()
    win.background_colour = "yellow"
    p.move(80, 120)
    s = ""
    for pt in p.get_points():
        s = s + f" ({pt.x},{pt.y})"
    t.text = s

    # mouse click()
    win.get_mouse()
    p.undraw()
    e.undraw()
    t.style = "bold"

    # mouse click()
    win.get_mouse()
    t.style = "normal"

    # mouse click()
    win.get_mouse()
    t.style = "italic"

    # mouse click()
    win.get_mouse()
    t.style = "bold italic"

    # mouse click()
    win.get_mouse()
    t.size = 14

    # mouse click()
    win.get_mouse()
    t.typeface = "arial"
    t.size = 20

    # mouse click()
    win.get_mouse()
    win.close()


# MacOS fix 2
# tk.Toplevel(_root).destroy()

# MacOS fix 1
update()

if __name__ == "__main__":
    test()
