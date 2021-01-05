#! /usr/bin/env python3
'''
Created on Nov 29, 2020

@author: OSi
'''


class GCode:
    def __init__(self, gcode = None):
        self.file        =  gcode
        self.gcode       =  []
        self.max_cmd_len =  0
        self.id          =  1
        self.x_min       =  1000000000000
        self.x_max       = -1000000000000
        self.y_min       =  1000000000000
        self.y_max       = -1000000000000
        
        if gcode is None:
            return
        
        with open(gcode, 'r') as f:
            lines = f.readlines()
            
            for line in lines:
                self.append_line(line)
            
            self.rebuild()
    
    
    def save(self, output = None):
        file = output
        
        if not file:
            file = self.file
        
        with open(file, 'w') as f:
            self.rebuild()
            
            fmt = '{:<' + str(self.max_cmd_len + 4) + '};{}\n'
            
            for cmd in self.gcode:
                if   0 == len(cmd[1]) and 0 == len(cmd[2]):
                    f.write('\n')
                elif 0 == len(cmd[1]):
                    f.write(';{}\n'.format(cmd[2]))
                elif 0 == len(cmd[2]):
                    f.write('{}\n'.format(cmd[1]))
                else:
                    f.write(fmt.format(cmd[1], cmd[2]))
    
    
    def rebuild(self):
        self.max_cmd_len = 0
        axis_ids         = 'X', 'Y', 'Z', 'E'
        position         = { axis : 0 for axis in axis_ids }
        origin           = { axis : 0 for axis in axis_ids }
        g_moves          = 0, 1, 2, 3, 5
        g_unsupported    = 6, 10, 11, 17, 18, 19, 20, 26, 27, 29, 30, 31, 32, 33, 34, 35, 42, 53, 60, 61, 76, 80, 425
        mode_relative    = False
        
        for cmd in self.gcode:
            c = cmd[0]
            
            # Track movement
            if 'G' in c:
                g = c['G']
                
                if   g in g_unsupported:
                    raise ValueError('Unsupported code G{}'.format(g))
                elif g in g_moves:
                    for axis_id in axis_ids:
                        if mode_relative:
                            if axis_id in c: position[axis_id]  = c[axis_id] + origin[axis_id]
                        else:
                            if axis_id in c: position[axis_id] += c[axis_id]
                elif g == 90:
                    mode_relative = False
                elif g == 91:
                    mode_relative = True
                elif g == 92:
                    for axis_id in axis_ids:
                        if axis_id in c: origin[axis_id] = c[axis_id] + position[axis_id]
            
            cmd[3] = (position[val] for val in axis_ids)
            
            # Build GCode line
            l = ''
            for g in c:
                if not l == '':
                    l += ' '
                
                v = c[g[0]]
                
                if isinstance(v, float):
                    d = self._decimals(v)
                    
                    if d[2] == 0:
                        l += '{}{}'.format(g[0], d[0])
                    else:
                        f  = '{}{}.{:0%i}' % d[2]
                        l += f.format(g[0], d[0], d[1])
                else:
                    l += '{}{}'.format(g[0], v)
            
            cmd[1] = l
            self.max_cmd_len = max(self.max_cmd_len, len(l))
    
    
    def parse_line(self, line):
        cmds = []
        
        if isinstance(line, str):
            for line in line.rstrip().split('\n'):
                cmd = line.rstrip().split(';', 1)
                
                if 1 == len(cmd):
                    cmd.append('')
                    
                cmd      = [None, cmd[0], cmd[1], None, self.id]
                self.id += 1
                
                t = cmd[1].split(' ')
                g = {}
                
                for i in t:
                    if i == '':
                        continue
                    
                    c = i[0]
                    v = i[1:]
                    
                    if c in 'MGTF':
                        v = int(float(v) + 0.5)
                    elif not v == '':
                        v = float(v)
                    else:
                        v = None
                    
                    g[c] = v
                    
                    if 'M' == c and 117 == v:
                        g[' '] = cmd[1][4:]
                        break
                
                if 'X' in g:
                    v = g['X']
                    self.x_min = min(v, self.x_min)
                    self.x_max = max(v, self.x_max)
                
                if 'Y' in g:
                    v = g['Y']
                    self.y_min = min(v, self.y_min)
                    self.y_max = max(v, self.y_max)
                    
                cmd[0] = g
                cmds.append(cmd)
                
                self.max_cmd_len = max(self.max_cmd_len, len(cmd[1]))
            
            return cmds
        elif isinstance(line, list) and len(line) == 5:
            return [line]
        else:
            raise TypeError('Unsupported line representation type {}'.format(type(line)))
    
    
    def append_line(self, line):
        self.gcode.extend(self.parse_line(line))
    
    
    def append_lines(self, lines):
        for line in lines:
            self.gcode.extend(self.parse_line(line))
    
    
    @staticmethod
    def _decimals(v):
        dt   = 1000, 100, 10, 1
        base = dt[0]
        
        if v >= 0:
            v = int((v + 0.5 / base) * base)
        else:
            v = int((v - 0.5 / base) * base)
        
        d = base
        
        for n in dt:
            if 0 == v % n:
                d = n
                break
        
        if v >= 0:
            return v // base,            (v % base) // d, dt.index(d)
        else:
            return v // base + 1, base - (v % base) // d, dt.index(d)


if __name__ == '__main__':
    def run(gcode, svg):
        print('Reading ', gcode)
        gcode = GCode(gcode)
        
        print('Writing ', svg)
        gcode.save(svg)
        
        print('Done ...')
    
    
    import sys
    run(sys.argv[1], sys.argv[2])