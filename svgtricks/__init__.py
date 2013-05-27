# -*- python; charset: utf-8 -*-

import atexit
import sys
from xml.dom import minidom


#
# CONTEXT STACK
#

class Document(object):
    instance = None

    def __init__(self):
        self._create_document()

    def _create_document(self):
        self.dom = minidom.Document()
        self._contexts = [DOMContext()]

    def root_context(self):
        return self._contexts[1]

    def context(self):
        return self._contexts[-1]
    
    def push_context(self, element):
        self._contexts.append(element)

    def pop_context(self):
        self._contexts.pop()
    
    def new_element(self, tag):
        elem = self.dom.createElement(tag)
        self.context().get_element().appendChild(elem)
        return elem

    def output(self, fd=sys.stdout):
        doctype = '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
        fd.write(self.dom.toprettyxml().replace('<svg', '\n%s\n<svg' % doctype, 1))


#
# DOCUMENT-LEVEL FUNCTIONS
#

def canvas(x, y):
    root = document.root_context().get_element()
    root.setAttribute('width', str(x))
    root.setAttribute('height', str(y))

def viewport(x, y, w, h):
    root = document.root_context().get_element()
    root.setAttribute('viewBox', '%s %s %s %s' % (x, y, w, h))


#
# CONTEXT STACK
#

class Context(object):
    parent = None
    document = None

    def __init__(self):
        document = Document.instance

    def __enter__(self):
        self.parent = document.context()
        document.push_context(self)

    def __exit__(self, type, value, traceback):
        document.pop_context()

    def get_element(self):
        return self.parent.get_element()


class DOMContext(Context):
    def get_element(self):
        return document.dom


class ElementContext(Context):
    def __init__(self, **kwargs):
        super(ElementContext, self).__init__()
        self._element = document.new_element(self.tag)
        self._set_attributes(kwargs)

    def _set_attributes(self, attributes):
        for attr, value in attributes.items():
            if attr.endswith('_'):
                attr = attr[:-1]
            cb_name = '_fmt_' + attr
            if hasattr(self, cb_name):
                value = getattr(self, cb_name)(value)
            self._element.setAttribute(attr.replace('_', '-'), str(value))

    def _fmt_style(self, value):
        return '; '.join('%s: %s' % (a.replace('_', '-'), v) for (a, v) in value.items())

    def get_element(self):
        return self._element


#
# SVG ELEMENTS
#

class svg(ElementContext):
    tag = 'svg'

    def __init__(self):
        super(svg, self).__init__(xmlns="http://www.w3.org/2000/svg")

class group(ElementContext):
    tag = 'g'

class line(ElementContext):
    tag = 'line'

    def __init__(self, pt1, pt2, **kwargs):
        super(line, self).__init__(x1=pt1[0], y1=pt1[1], x2=pt2[0], y2=pt2[1], **kwargs)

class circle(ElementContext):
    tag = 'circle'

    def __init__(self, center, r, **kwargs):
        super(circle, self).__init__(cx=center[0], cy=center[1], r=r, **kwargs)

class ellipse(ElementContext):
    tag = 'ellipse'

class rectangle(ElementContext):
    tag = 'rect'

    def __init__(self, corner, w, h, **kwargs):
        super(rectangle, self).__init__(x=corner[0], y=corner[1], width=w, height=h, **kwargs)

class polyline(ElementContext):
    tag = 'polyline'

    def _fmt_points(self, value):
        return ' '.join('%s,%s' % x for x in value)

class polygon(polyline):
    tag = 'polygon'

class text(ElementContext):
    tag = 'text'

    def __init__(self, pt, txt, **kwargs):
        super(text, self).__init__(x=pt[0], y=pt[1], **kwargs)
        self.get_element().appendChild(document.dom.createTextNode(str(txt)))


#
# COORDINATES STUFF
#

class origin(group):
    def __init__(self, point, invert_y=False):
        transform = 'matrix(1, 0, 0, %d, %d, %d)' % (-1 if invert_y else 1, point[0], point[1])
        super(origin, self).__init__(transform=transform)


#
# EXTRA ELEMENTS
#

LEFT, RIGHT = range(2)
TOP, BOTTOM = range(2)

def hrule(xcoord, y, side=BOTTOM, rule_length=20):
    xcoord.sort()
    with group(class_='hrule', style={'stroke': 'black', 'stroke-width': 2}):
        for i in range(0, len(xcoord)-1):
            x1 = xcoord[i]
            x2 = xcoord[i+1]
            line((x1, y), (x2, y))
            text_y = y - 20 if side == TOP else y + 80
            text(((x1+x2)/2., text_y), abs(x2-x1),
                 style={'font-size': 42, 'fill': 'black', 'stroke': 'none', 'text-anchor': 'middle'})

        for x in xcoord:
            line((x, y-rule_length), (x, y+rule_length))

def vrule(x, ycoord, side=RIGHT, rule_length=20):
    ycoord.sort()
    with group(class_='vrule', style={'stroke': 'black', 'stroke-width': 2}):
        for i in range(0, len(ycoord)-1):
            y1 = ycoord[i]
            y2 = ycoord[i+1]
            line((x, y1), (x, y2))
            text_x = x - 10 if side == LEFT else x + 10
            text_anchor = 'end' if side == LEFT else 'start'
            text((text_x, (y1+y2)/2.+20), abs(y2-y1),
                 style={'font-size': 42, 'fill': 'black', 'stroke': 'none', 'text-anchor': text_anchor})

        for y in ycoord:
            line((x-rule_length, y), (x+rule_length, y))


#
# MODULE INITIATION
#

document = Document()
atexit.register(document.output)
document.push_context(svg())
