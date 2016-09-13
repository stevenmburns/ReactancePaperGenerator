#!/usr/bin/env python
import cairocffi as cairo
import argparse

import math
import unittest

def e_lst( r):
    assert r in [1,2,3,4,6,12]
    e12_lst = [1.0,1.2,1.5,1.8,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]
    return [ e12_lst[i] for i in range(0,12,12//r)]

class TestELst(unittest.TestCase):
    def test_e1(self):
        self.assertEqual( e_lst(1), [1.0])
    def test_e2(self):
        self.assertEqual( e_lst(2), [1.0,3.3])
    def test_e3(self):
        self.assertEqual( e_lst(3), [1.0,2.2,4.7])
    def test_e4(self):
        self.assertEqual( e_lst(4), [1.0,1.8,3.3,5.6])
    def test_e6(self):
        self.assertEqual( e_lst(6), [1.0,1.5,2.2,3.3,4.7,6.8])


#set the size of the page here
major_dist_in_points = 72.0

wpage=major_dist_in_points*8.5
hpage=major_dist_in_points*11.0
#
xoff = major_dist_in_points*0.25
yoff = major_dist_in_points*0.50
#
nx_major = 8
ny_major = 10
#
w=major_dist_in_points*nx_major
h=major_dist_in_points*ny_major
#
major_width = .8/72.0
minor_width = .1/72.0

surf = cairo.PDFSurface("CairoOut.pdf", wpage, hpage)
ctx = cairo.Context(surf)

#set the line colour, in RGB
ctx.set_source_rgb(1,0,0) #these are red lines

class Series:
    def __init__( self, a, b):
        self.a = a
        self.b = b

    def eval( self, omega):
        return self.a.eval( omega) + self.b.eval( omega)
        
    def qeval( self, omega):
        return max(self.a.qeval( omega), self.b.qeval( omega))


class Parallel:
    def __init__( self, a, b):
        self.a = a
        self.b = b

    def par(self,a,b):
        return a*b/(a+b)

    def eval( self, omega):
        return self.par( self.a.eval( omega), self.b.eval( omega))
        
    def qeval( self, omega):
        return min(self.a.qeval( omega), self.b.qeval( omega))

class Resistor:
    def __init__( self, value):
        self.value = value

    def eval( self, omega):
        return complex(self.value,0.0)
        
    def qeval( self, omega):
        return self.value

class Inductor:
    def __init__( self, value):
        self.value = value

    def eval( self, omega):
        return complex(0.0,self.value*omega)
        
    def qeval( self, omega):
        return self.value*omega 


class Capacitor:
    def __init__( self, value):
        self.value = value

    def eval( self, omega):
        return complex(0.0,-1.0/(self.value*omega))
        
    def qeval( self, omega):
        return 1.0/(self.value*omega)

class Grid:
    def __init__( self, lst):
        self.period = len(lst)
        self.lst = lst
        self.off_l = 0
        self.off_h = 1

    @property
    def nx( self):
        return nx_major*self.period

    @property
    def ny( self):
        return ny_major*self.period

    def ismajor( self, i):
        return i % self.period == 0

    def log_value( self, i):
        majors = i // self.period
        minors = i %  self.period
        result = majors + self.lst[minors]
#        print( i, self.lst, self.period, result)
        return result

    def value( self, i):
        return math.pow( 10.0, self.log_value( i))

#sg = Grid( [ math.log10(x) for x in e_lst(6)])
sg = Grid( [math.log10(i) for i in range(1,10)])
fg = Grid( [math.log10(i*2.0*math.pi) for i in range(1,10)])
fg.off_l = -8
fg.off_h = -8
dg = Grid( [ i/float(100) for i in range(100)])

ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
ctx.set_font_size(12/72.0)

ctx.translate( 72.0*8.5/2, 72.0*11.0/2)
ctx.scale( 60.0, -60.0)
ctx.translate( -nx_major/2.0, -ny_major/2.0)

#fm = cairo.Matrix(ctx.get_matrix())
#fm.scale( 1.0, -1.0)
#ctx.set_font_matrix( fm)

def xx( x):
#    return math.log10(x)*major_dist_in_points + xoff
    return math.log10(x)

def yy( y):
#    return h - math.log10(y)*major_dist_in_points + yoff
    return math.log10(y)

# frequency lines
for o in range(fg.off_l,fg.nx+fg.off_h):
    r_min = 1.0
    r_max = math.pow( 10.0, ny_major)

    ovalue = fg.value(o)

    ctx.move_to( xx( ovalue), yy( r_min))
    ctx.line_to( xx( ovalue), yy( r_max))

    ctx.set_line_width(major_width if fg.ismajor(o) else minor_width)
    ctx.stroke()

    if fg.ismajor(o):
        fvalue = math.floor(ovalue/(2.0*math.pi)+0.5)
        if fvalue >= 1000000000:
            txt = "%.0fGHz" % (fvalue/1000000000) 
        elif fvalue >= 1000000:
            txt = "%.0fMHz" % (fvalue/1000000) 
        elif fvalue >= 1000:
            txt = "%.0fkHz" % (fvalue/1000) 
        elif fvalue >= 1:
            txt = "%.0fHz" % (fvalue) 
        else:
            txt = "%.0fmHz" % (fvalue*1000) 

        ctx.save()
        ctx.translate( xx(ovalue), yy( r_min))
        ctx.scale( 1.0, -1.0)
        (_, _, width, height, _, _) = ctx.text_extents(txt)
        ctx.move_to( -width/2, height+0.1)
        ctx.show_text( txt)
        ctx.restore()

# resistance lines
#ohm_sym = "\N{GREEK CAPITAL LETTER OMEGA}"
ohm_sym = "\N{OHM SIGN}"
mu_sym  = "\N{GREEK SMALL LETTER MU}"

for r in range(sg.ny+1):
    o_min = 1.0
    o_max = math.pow( 10.0, nx_major)

    rvalue = sg.value(r)

    ctx.move_to( xx( o_min), yy( rvalue))
    ctx.line_to( xx( o_max), yy( rvalue))
    ctx.set_line_width(major_width if sg.ismajor(r) else minor_width)
    ctx.stroke()

    if fg.ismajor(r):
        if rvalue >= 1000000000:
            txt = "%.0fG" % (rvalue/1000000000) 
        elif rvalue >= 1000000:
            txt = "%.0fM" % (rvalue/1000000) 
        elif rvalue >= 1000:
            txt = "%.0fk" % (rvalue/1000) 
        elif rvalue >= 1:
            txt = "%.0f" % (rvalue) 
        else:
            txt = "%.0fm" % (rvalue*1000) 

        txt += ohm_sym

        ctx.save()
        ctx.translate( xx(o_min), yy( rvalue))
        ctx.scale( 1.0, -1.0)
        (_, _, width, height, _, _) = ctx.text_extents(txt)
        ctx.move_to( -width-0.1, height/2)
        ctx.show_text( txt)
        ctx.restore()



# capacitance lines
#
# ny           nx+ny
#
#
# 0             nx
#
# R C = 1/Omega
# log R + log C = - log Omega
# log R = - log Omega - log C
#
# R = 1/(Omega*C)
# Omega = 1/(R*C)
#
# x = 0  => Omega=10^(0)
# x = nx => Omega=10^(nx_major)   [nx_major=nx/major_period]
# y = 0  => R=10^(0)
# y = ny => R=10^(ny_major)       [ny_major=ny/major_period]
#    

for c in range(-(sg.nx+sg.ny),1):
    r_min = 1.0
    r_max = math.pow( 10.0, ny_major)

    o_min = 1.0
    o_max = math.pow( 10.0, nx_major)

    cvalue = sg.value(c)

    r_0  = 1.0/(cvalue * o_min)
    r_nx = 1.0/(cvalue * o_max)

    o_0  = 1.0/(r_min * cvalue)
    o_ny = 1.0/(r_max * cvalue)

    if cvalue >= math.pow( 10.0, -nx_major):
        ctx.move_to(xx(o_min), yy(r_0))
        ctx.line_to(xx(o_0), yy(r_min))
    elif cvalue >= math.pow( 10.0, -ny_major):
        ctx.move_to(xx(o_min), yy(r_0))
        ctx.line_to(xx(o_max), yy(r_nx))
    else:
        ctx.move_to(xx(o_ny), yy(r_max))
        ctx.line_to(xx(o_max), yy(r_nx))

    ctx.set_line_width(major_width if sg.ismajor(c) else minor_width)
    ctx.stroke()

    if fg.ismajor(c):
        if cvalue >= 1:
            txt = "%.0fF" % (cvalue) 
        elif cvalue >= 1e-3:
            txt = "%.0fmF" % (cvalue*1e3) 
        elif cvalue >= 1e-6:
            txt = "%.0f" % (cvalue*1e6) 
            txt += mu_sym + "F"
        elif cvalue >= 1e-9:
            txt = "%.0fnF" % (cvalue*1e9) 
        elif cvalue >= 1e-12:
            txt = "%.0fpF" % (cvalue*1e12) 
        elif cvalue >= 1e-15:
            txt = "%.0ffF" % (cvalue*1e15) 
        else:
            txt = ""




        ctx.save()
        if cvalue >= math.pow( 10.0, -nx_major):
            # bottom
#            ctx.move_to( xx(o_0)-(width/2), yy( r_min)-3*height)

            ctx.translate( xx(o_0), yy( r_min))
            ctx.rotate( -math.pi/4)
            ctx.scale( 1.0, -1.0)
            (_, _, width, height, _, _) = ctx.text_extents(txt)
            ctx.move_to( .2, height/2)

        else:
            # right side
#            ctx.move_to( xx(o_max)+(width/2), yy( r_nx)-(height/2))

            ctx.translate( xx(o_max), yy( r_nx))
            ctx.rotate( -math.pi/4)
            ctx.scale( 1.0, -1.0)
            (_, _, width, height, _, _) = ctx.text_extents(txt)
            ctx.move_to( .1, height/2)


        ctx.show_text( txt)
        ctx.restore()

# inductance lines
#
# R = k/(Cs) => RC = k/s
# R = kLs    => kL/R = 1/s 
#
# We want L/R = 1/Omega
# log R = log Omega + log L
#
#

#
# x = 0  => Omega=10^(0)
# x = nx => Omega=10^(nx_major)   [nx_major=nx/major_period]
# y = 0  => R=10^(0)
# x = ny => R=10^(ny_major)       [ny_major=ny/major_period]
#    
# x,y=0,0   => L=1H
#    =0,ny  => L=10^ny_major Henries
#     =nx,0  => L=10^-nx_major Henries
#    

#
# Three regions (assuming ny_major > nx_major:
#    L=10^(-nx_major) to 1
#    L=1 to 10^(ny_major-nx_major)
#    L=10^(ny_major-nx_major) to 10^ny_major
#
for l in range(-sg.nx,sg.ny+1):

#    
# L Omega = R
# Intersects x=0: R=L
# Intersects x=nx: R=L*10^nx_major
# Intersects y=0: Omega=1/L
# Intersects y=ny: Omega=10^ny_major/L
#
    r_min = 1.0
    r_max = math.pow( 10.0, ny_major)

    o_min = 1.0
    o_max = math.pow( 10.0, nx_major)

    lvalue = sg.value(l)

    r_0  = lvalue * o_min
    r_nx = lvalue * o_max

    o_0  = r_min / lvalue
    o_ny = r_max / lvalue

    if lvalue <= 1:
        ctx.move_to(xx(o_0), yy(r_min))
        ctx.line_to(xx(o_max), yy(r_nx))
    elif lvalue <= math.pow( 10.0, ny_major-nx_major):
        ctx.move_to(xx(o_min), yy(r_0))
        ctx.line_to(xx(o_max), yy(r_nx))
    else:
        ctx.move_to(xx(o_min), yy(r_0))
        ctx.line_to(xx(o_ny),  yy(r_max))

    ctx.set_line_width(major_width if sg.ismajor(l) else minor_width)
    ctx.stroke()

    if sg.ismajor(l):
        if lvalue >= 1e3:
            txt = ""
        elif lvalue >= 1:
            txt = "%.0fH" % (lvalue*1) 
        elif lvalue >= 1e-3:
            txt = "%.0fmH" % (lvalue*1e3) 
        elif lvalue >= 1e-3:
            txt = "%.0fmH" % (lvalue*1e3) 
        elif lvalue >= 1e-3:
            txt = "%.0fmH" % (lvalue*1e3) 
        elif lvalue >= 1e-6:
            txt = "%.0f" % (lvalue*1e6) 
            txt += mu_sym + "H"
        elif lvalue >= 1e-9:
            txt = "%.0fnH" % (lvalue*1e9) 
        elif lvalue >= 1e-12:
            txt = "%.0fpH" % (lvalue*1e12) 
        elif lvalue >= 1e-15:
            txt = "%.0ffH" % (lvalue*1e15) 
        else:
            txt = ""

        ctx.save()
        if lvalue <= math.pow( 10.0, ny_major-nx_major):
            # right side

            ctx.translate( xx(o_max), yy( r_nx))
            ctx.rotate( math.pi/4)
            ctx.scale( 1.0, -1.0)
            (_, _, width, height, _, _) = ctx.text_extents(txt)
            ctx.move_to( .1, height/2)

        else:
            # top

            ctx.translate( xx(o_ny), yy( r_max))
            ctx.rotate( math.pi/4)
            ctx.scale( 1.0, -1.0)
            (_, _, width, height, _, _) = ctx.text_extents(txt)
            ctx.move_to( .1, height/2)


        ctx.show_text( txt)
        ctx.restore()


# impedance
z = Series( Inductor( 100.e-3), Series( Resistor( 50.0), Capacitor( 100.e-9)))

last = None
for f in range(0,dg.nx+1):
    omega = dg.value( f)
    y = abs(z.eval(omega))

    curr = (xx(omega), yy(y))

    if last:
        ctx.move_to( last[0], last[1])
        ctx.line_to( curr[0], curr[1])
        ctx.set_line_width(3.0/72.0)
        ctx.stroke()

    last = curr

last = None
for f in range(0,dg.nx+1):
    omega = dg.value( f)
    y = abs(z.qeval(omega))
    curr = (xx(omega), yy(y))

    if last:
        ctx.move_to( last[0], last[1])
        ctx.line_to( curr[0], curr[1])
        ctx.set_line_width(1.8/72.0)
        ctx.stroke()

    last = curr


ctx.show_page()
surf.finish()
