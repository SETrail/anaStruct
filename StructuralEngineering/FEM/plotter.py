import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class Plotter:
    def __init__(self, system):
        self.system = system
        fig = plt.figure()
        self.one_fig = fig.add_subplot(111)
        plt.tight_layout()
        plt.style.use('ggplot')
        self.max_val = None
        self.plot_structure()
        self.max_force = 0

    def __set_factor(self, value_1, value_2):
        """
        :param value_1: value of the force/ moment at point 1
        :param value_2: value of the force/ moment at point 2
        :return: factor for scaling the force/moment in the plot
        """

        if abs(value_1) > self.max_force:
            self.max_force = abs(value_1)
        if abs(value_2) > self.max_force:
            self.max_force = abs(value_2)

        if math.isclose(self.max_force, 0):
            factor = 0.1
        else:
            factor = 1 / self.max_force
        return factor

    def __fixed_support_patch(self, max_val):
        """
        :param max_val: max scale of the plot
        """

        width = 4 / max_val
        height = 4 / max_val
        for node in self.system.supports_fixed:

            support_patch = mpatches.Rectangle((node.point.x - width * 0.25, -node.point.z - width * 0.25),
                                               width, height, color='r', zorder=9)
            self.one_fig.add_patch(support_patch)

    def __hinged_support_patch(self, max_val):
        """
        :param max_val: max scale of the plot
        """
        radius = 3 / max_val
        for node in self.system.supports_hinged:
            support_patch = mpatches.RegularPolygon((node.point.x, -node.point.z - radius),
                                                    numVertices=3, radius=radius, color='r', zorder=9)
            self.one_fig.add_patch(support_patch)

    def __roll_support_patch(self, max_val):
        """
        :param max_val: max scale of the plot
        """
        radius = 3 / max_val
        for node in self.system.supports_roll:
            support_patch = mpatches.RegularPolygon((node.point.x, -node.point.z - radius),
                                                    numVertices=3, radius=radius, color='r', zorder=9)
            self.one_fig.add_patch(support_patch)
            y = node.point.z - 2 * radius
            self.one_fig.plot([node.point.x - radius, node.point.x + radius], [y, y], color='r')

    def plot_structure(self, plot_now=False):
        """
        :param plot_now: boolean if True, plt.figure will plot.
        :return: -
        """
        max_val = 0
        for el in self.system.elements:
            # plot structure
            axis_values = plot_values_element(el)
            x_val = axis_values[0]
            y_val = axis_values[1]
            self.one_fig.plot(x_val, y_val, color='black', marker='s')

            if max(max(x_val), max(y_val)) > max_val:
                max_val = max(max(x_val), max(y_val))

            # add node ID to plot
            self.one_fig.text(x_val[0] + 0.1, y_val[0] + 0.1, '%d' % el.nodeID1, color='g', fontsize=9, zorder=10)
            self.one_fig.text(x_val[-1] + 0.1, y_val[-1] + 0.1, '%d' % el.nodeID2, color='g', fontsize=9, zorder=10)

        self.max_val = max_val
        max_val += 2
        self.one_fig.axis([-2, max_val, -2, max_val])

        for el in self.system.elements:
            # add element ID to plot
            axis_values = plot_values_element(el)
            x_val = axis_values[0]
            y_val = axis_values[1]

            factor = 1.5 / self.max_val
            x_val = (x_val[0] + x_val[-1]) / 2 - math.sin(el.alpha) * factor
            y_val = (y_val[0] + y_val[-1]) / 2 + math.cos(el.alpha) * factor

            self.one_fig.text(x_val, y_val, "%d" % el.ID, color='r', fontsize=9, zorder=10)

        # add supports
        self.__fixed_support_patch(max_val)
        self.__hinged_support_patch(max_val)
        self.__roll_support_patch(max_val)

        if plot_now:
            plt.show()

    def plot_force(self, axis_values, force_1, force_2):

            # plot force
            x_val = axis_values[0]
            y_val = axis_values[1]
            self.one_fig.plot(x_val, y_val, color='b')

            # add value to plot
            self.one_fig.text(x_val[1] - 2 / self.max_val, y_val[1] + 2 / self.max_val, "%s" % abs(round(force_1, 1)),
                              fontsize=9)
            self.one_fig.text(x_val[-2] - 2 / self.max_val, y_val[-2] + 2 / self.max_val, "%s" % abs(round(force_2, 1)),
                              fontsize=9)

    def normal_force(self):
        # determine max factor for scaling
        for el in self.system.elements:
            factor = self.__set_factor(el.N, el.N)

        for el in self.system.elements:
            axis_values = plot_values_normal_force(el, factor)
            self.plot_force(axis_values, el.N, el.N)

        plt.show()

    def bending_moment(self):
        con = 20
        # determine max factor for scaling
        for el in self.system.elements:
            factor = self.__set_factor(el.node_1.Ty, el.node_2.Ty)

        for el in self.system.elements:
            axis_values = plot_values_bending_moment(el, factor, con)
            self.plot_force(axis_values, el.node_1.Ty, el.node_2.Ty)

            if el.q_load:
                index = con // 2
                self.one_fig.text(axis_values[0][index], axis_values[1][index], "%s" % round(abs(axis_values[2]), 1))
        plt.show()

    def shear_force(self):
        # determine max factor for scaling
        for el in self.system.elements:
            sol = plot_values_shear_force(el, factor=1)
            shear_1 = sol[-2]
            shear_2 = sol[-1]
            factor = self.__set_factor(shear_1, shear_2)

        for el in self.system.elements:
            axis_values = plot_values_shear_force(el, factor)
            shear_1 = axis_values[-2]
            shear_2 = axis_values[-1]
            self.plot_force(axis_values, shear_1, shear_2)
        plt.show()


"""
### element functions ###
"""


def plot_values_element(element):
    x_val = [element.point_1.x, element.point_2.x]
    y_val = [-element.point_1.z, -element.point_2.z]
    return x_val, y_val

def plot_values_shear_force(element, factor=1):
    dx = element.point_1.x - element.point_2.x
    x1 = element.point_1.x
    y1 = -element.point_1.z
    x2 = element.point_2.x
    y2 = -element.point_2.z

    if math.isclose(dx, 0):  # element is vertical
        shear_1 = -(math.sin(element.alpha) * element.node_1.Fx + math.cos(element.alpha) * element.node_1.Fz)
        shear_2 = (math.sin(element.alpha) * element.node_2.Fx + math.cos(element.alpha) * element.node_2.Fz)

        if element.point_1.z > element.point_2.z:  # point 1 is bottom
            x_1 = x1 + shear_1 * math.cos(1.5 * math.pi + element.alpha) * factor
            y_1 = y1 + shear_1 * math.sin(1.5 * math.pi + element.alpha) * factor
            x_2 = x2 + shear_2 * math.cos(1.5 * math.pi + element.alpha) * factor
            y_2 = y2 + shear_2 * math.sin(1.5 * math.pi + element.alpha) * factor
        else:
            x_1 = x1 + shear_1 * math.cos(0.5 * math.pi + element.alpha) * factor
            y_1 = y1 + shear_1 * math.sin(0.5 * math.pi + element.alpha) * factor
            x_2 = x2 + shear_2 * math.cos(0.5 * math.pi + element.alpha) * factor
            y_2 = y2 + shear_2 * math.sin(0.5 * math.pi + element.alpha) * factor

    elif math.isclose(element.alpha, 0):  # element is horizontal
        if element.point_1.x < element.point_2.x:  # point 1 is left
            shear_1 = -(math.sin(element.alpha) * element.node_1.Fx + math.cos(element.alpha) * element.node_1.Fz)
            shear_2 = math.sin(element.alpha) * element.node_2.Fx + math.cos(element.alpha) * element.node_2.Fz
            x_1 = x1 + shear_1 * math.cos(1.5 * math.pi + element.alpha) * factor
            y_1 = y1 + shear_1 * math.sin(1.5 * math.pi + element.alpha) * factor
            x_2 = x2 + shear_2 * math.cos(1.5 * math.pi + element.alpha) * factor
            y_2 = y2 + shear_2 * math.sin(1.5 * math.pi + element.alpha) * factor
        else:
            shear_1 = math.sin(element.alpha) * element.node_1.Fx + math.cos(element.alpha) * element.node_1.Fz
            shear_2 = -(math.sin(element.alpha) * element.node_2.Fx + math.cos(element.alpha) * element.node_2.Fz)
            x_1 = x1 + shear_1 * math.cos(0.5 * math.pi + element.alpha) * factor
            y_1 = y1 + shear_1 * math.sin(0.5 * math.pi + element.alpha) * factor
            x_2 = x2 + shear_2 * math.cos(0.5 * math.pi + element.alpha) * factor
            y_2 = y2 + shear_2 * math.sin(0.5 * math.pi + element.alpha) * factor

    else:
        if math.cos(element.alpha) > 0:
            if element.point_1.x < element.point_2.x:  # point 1 is left
                shear_1 = -(math.sin(element.alpha) * element.node_1.Fx + math.cos(element.alpha) * element.node_1.Fz)
                shear_2 = math.sin(element.alpha) * element.node_2.Fx + math.cos(element.alpha) * element.node_2.Fz
                x_1 = x1 + shear_1 * math.cos(1.5 * math.pi + element.alpha) * factor
                y_1 = y1 + shear_1 * math.sin(1.5 * math.pi + element.alpha) * factor
                x_2 = x2 + shear_2 * math.cos(1.5 * math.pi + element.alpha) * factor
                y_2 = y2 + shear_2 * math.sin(1.5 * math.pi + element.alpha) * factor
            else:  # point 1 is right
                shear_1 = math.sin(element.alpha) * element.node_1.Fx + math.cos(element.alpha) * element.node_1.Fz
                shear_2 = -(math.sin(element.alpha) * element.node_2.Fx + math.cos(element.alpha) * element.node_2.Fz)
                x_1 = x1 + shear_1 * math.cos(0.5 * math.pi + element.alpha) * factor
                y_1 = y1 + shear_1 * math.sin(0.5 * math.pi + element.alpha) * factor
                x_2 = x2 + shear_2 * math.cos(0.5 * math.pi + element.alpha) * factor
                y_2 = y2 + shear_2 * math.sin(0.5 * math.pi + element.alpha) * factor

    x_val = [x1, x_1, x_2, x2]
    y_val = [y1, y_1, y_2, y2]
    return x_val, y_val, shear_1, shear_2


def plot_values_normal_force(element, factor):
    x1 = element.point_1.x
    y1 = -element.point_1.z
    x2 = element.point_2.x
    y2 = -element.point_2.z

    x_1 = x1 + element.N * math.cos(0.5 * math.pi + element.alpha) * factor
    y_1 = y1 + element.N * math.sin(0.5 * math.pi + element.alpha) * factor
    x_2 = x2 + element.N * math.cos(0.5 * math.pi + element.alpha) * factor
    y_2 = y2 + element.N * math.sin(0.5 * math.pi + element.alpha) * factor

    x_val = [x1, x_1, x_2, x2]
    y_val = [y1, y_1, y_2, y2]
    return x_val, y_val


def plot_values_bending_moment(element, factor, con):
    """
    :param factor: scaling the plot
    :param con: amount of x-values
    :return:
    """
    # plot the bending moment
    x1 = element.point_1.x
    y1 = -element.point_1.z
    x2 = element.point_2.x
    y2 = -element.point_2.z
    dx = x2 - x1
    dy = y2 - y1

    if math.isclose(element.alpha, 0.5 * math.pi, rel_tol=1e-4) or \
            math.isclose(element.alpha, 1.5 * math.pi, rel_tol=1e-4):
        # point 1 is bottom
        x_1 = x1 + element.node_1.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
        y_1 = y1 + element.node_1.Ty * math.sin(0.5 * math.pi + element.alpha) * factor
        x_2 = x2 - element.node_2.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
        y_2 = y2 - element.node_2.Ty * math.sin(0.5 * math.pi + element.alpha) * factor

    else:
        if dx > 0:  # point 1 = left and point 2 is right
            # With a negative moment (at support), left is positive and right is negative
            # node 1 is left, node 2 is right
            x_1 = x1 + element.node_1.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
            y_1 = y1 + element.node_1.Ty * math.sin(0.5 * math.pi + element.alpha) * factor
            x_2 = x2 - element.node_2.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
            y_2 = y2 - element.node_2.Ty * math.sin(0.5 * math.pi + element.alpha) * factor
        else:
            # node 1 is right, node 2 is left
            x_1 = x1 - element.node_1.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
            y_1 = y1 - element.node_1.Ty * math.sin(0.5 * math.pi + element.alpha) * factor
            x_2 = x2 + element.node_2.Ty * math.cos(0.5 * math.pi + element.alpha) * factor
            y_2 = y2 + element.node_2.Ty * math.sin(0.5 * math.pi + element.alpha) * factor

    x_val = np.linspace(0, 1, con)
    y_val = np.empty(con)
    dx = x_2 - x_1
    dy = y_2 - y_1
    count = 0

    # determine moment for 0 < x < length of the element
    for i in x_val:
        x_val[count] = x_1 + i * dx
        y_val[count] = y_1 + i * dy

        if element.q_load:
            x = i * element.l
            q_part = (-0.5 * -element.q_load * x ** 2 + 0.5 * -element.q_load * element.l * x)

            y_val[count] += math.cos(element.alpha) * q_part * factor
        count += 1

    x_val = np.append(x_val, x2)
    y_val = np.append(y_val, y2)
    x_val = np.insert(x_val, 0, x1)
    y_val = np.insert(y_val, 0, y1)

    if element.q_load:
        sagging_moment = (-element.node_1.Ty + element.node_2.Ty) * 0.5 + 0.125 * element.q_load * element.l ** 2
        return x_val, y_val, sagging_moment
    else:
        return x_val, y_val