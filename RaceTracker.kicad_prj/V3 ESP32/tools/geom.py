"""Pin-position math for placing symbols in a .kicad_sch (project memory
rules 11/29): abs_x = inst_x + local_x*cos(t) - local_y*sin(t)
              abs_y = inst_y - local_x*sin(t) - local_y*cos(t)
(note the minus sign on the whole rotated-Y term -- verified empirically
against kicad-cli sch export netlist in the v2-simple session)."""
import math


def pin_abs(inst_x, inst_y, inst_angle, local_x, local_y):
    t = math.radians(inst_angle)
    c, s = math.cos(t), math.sin(t)
    ax = inst_x + local_x * c - local_y * s
    ay = inst_y - local_x * s - local_y * c
    return round(ax, 3), round(ay, 3)
