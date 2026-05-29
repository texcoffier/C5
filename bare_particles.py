"""
Particle system with springs.
"""
PI = Math.PI
cos = Math.cos
sin = Math.sin
acos = Math.acos
asin = Math.asin
def polar_first_quadrant(vec_x, vec_y):
    """Compute angle assuming vec_x>=0 et vec_y>0"""
    length = (vec_x*vec_x + vec_y*vec_y) ** 0.5
    if vec_x > vec_y:
        return acos(vec_x / length)
    return asin(vec_y / length)
def polar(vect_x, vect_y):
    """Compute angle in any quadrant"""
    if vect_x >= 0:
        if vect_y >= 0:
            return polar_first_quadrant(vect_x, vect_y)
        return -polar_first_quadrant(vect_x, -vect_y)
    if vect_y >= 0:
        return PI - polar_first_quadrant(-vect_x, vect_y)
    return -(PI - polar_first_quadrant(-vect_x, -vect_y))
class Particle: # pylint: disable=too-few-public-methods
    """A node to display on the canvas"""
    def __init__(self, name, color, x, y, fixed): # pylint: disable=too-many-arguments
        self.coord_x = x
        self.coord_y = y
        self.speed_x = self.speed_y = 0
        self.name = name
        self.position_fixed = fixed
        self.color = color
class Particles: # pylint: disable=too-many-instance-attributes
    """Network displayer"""
    selected = ctx = None
    current_x = 0
    current_y = 0
    def __init__(self, netname, masses, springs):
        self.canvas = document.getElementById('particles')
        self.canvas.onmousedown = self.onmousedown.bind(self)
        self.canvas.onmouseup = self.onmouseup.bind(self)
        self.canvas.onmouseout = self.onmouseup.bind(self)
        self.canvas.onmousemove = self.onmousemove.bind(self)
        self.canvas.setAttribute('width', self.canvas.offsetWidth)
        self.canvas.setAttribute('height', self.canvas.offsetHeight)
        width = self.canvas.offsetWidth
        height = self.canvas.offsetHeight
        self.font = 12 * width / 1024
        self.center_x = width / 2
        self.center_y = height / 2
        self.nodes = []
        self.netname = netname
        positions = JSON.parse(localStorage[netname] or '{}')
        for name, color in masses:
            if name in positions:
                x, y = positions[name]
            else:
                x = self.center_x + width * (Math.random() - 0.5) / 2
                y = self.center_y + height * (Math.random() - 0.5) / 2
            self.nodes.append(Particle(name, color, x, y, False))
        self.links = []
        for index1, index2, label1up,  label2up, label1down, label2down, length, strength in springs:
            length *= width / 1024
            self.links.append([self.nodes[index1], self.nodes[index2],
                               label1up,  label2up, label1down, label2down,
                               length, strength
                              ])

        self.canvas.intervalID = self.intervalID = setInterval(self.move.bind(self), 50)
    def onmousedown(self, _event):
        """Set the selected node"""
        self.draw(True)
    def onmouseup(self, _event):
        """Unset selected node"""
        if self.selected:
            self.selected.position_fixed = True
        self.selected = None
    def onmousemove(self, event):
        """Update current mouse position for the next drawing"""
        box = event.target.getBoundingClientRect()
        self.current_x = (event.clientX - box.x) # * 1024 / self.canvas.width
        self.current_y = (event.clientY - box.y) # * 1024 / self.canvas.height
    def draw(self, do_select=False): # pylint: disable=too-many-branches,too-many-statements
        """Draw the network.
        Use 'selected', 'current_x', 'current_y', 'nodes', 'arcs'
        """
        if self.selected:
            self.selected.coord_x = self.current_x
            self.selected.coord_y = self.current_y

        font = self.font
        if not self.ctx:
            self.ctx = self.canvas.getContext("2d")
            # self.ctx.scale(self.canvas.width / 1024, self.canvas.height / 1024)
            self.ctx.font = font + 'px sans-serif'
        ctx = self.ctx
        ctx.clearRect(0, 0, self.canvas.width, self.canvas.height)
        ctx.fillStyle = '#000'

        for node in self.nodes:
            node.text_width = ctx.measureText(node.name).width

        ctx.strokeStyle = '#000'
        spring_zoomed = None
        for link in self.links:
            node1, node2, label1up,  _label2up, label1down, _label2down, _length, _strength = link
            ctx.beginPath()
            ctx.moveTo(node1.coord_x, node1.coord_y)
            ctx.lineTo(node2.coord_x, node2.coord_y)
            ctx.closePath()
            ctx.stroke()
            dx = node1.coord_x - node2.coord_x
            dy = node1.coord_y - node2.coord_y
            angle = polar(dx, dy)
            distance = (dx*dx + dy*dy) ** 0.5
            length_label_up = ctx.measureText(label1up).width
            length_label_down = ctx.measureText(label1down).width
            goodness = distance - (max(length_label_up, length_label_down) + 2*font)
            if abs(goodness) > 2:
                # Adjust the spring length so is has the same size than label.
                if goodness < 0:
                    link[6] *= -goodness ** 0.01
                else:
                    link[6] /= goodness ** 0.01
            ctx.save()
            ctx.translate(node1.coord_x, node1.coord_y)
            offset_x = node1.text_width / 1.5
            if -PI/2 < angle < PI/2:
                ctx.rotate(angle)
                ctx.fillText(label1up  , -length_label_up   - offset_x, -4)
                ctx.fillText(label1down, -length_label_down - offset_x, font)
                offset_x = -max(length_label_up, length_label_down) - offset_x
            else:
                angle -= PI
                ctx.rotate(angle)
                ctx.fillText(label1up, offset_x, -4)
                ctx.fillText(label1down, offset_x, font)
            ctx.beginPath()
            ctx.rect(offset_x, -1.5*font, max(length_label_up, length_label_down), 3*font)
            ctx.closePath()
            if ctx.isPointInPath(self.current_x, self.current_y):
                spring_zoomed = [label1up, label1down]
            ctx.restore()
        ctx.fillStyle = '#FF0'
        for node in self.nodes:
            selectable = ((self.current_x - node.coord_x) ** 2
                          + (self.current_y - node.coord_y) ** 2) < 400
            if selectable and do_select:
                self.selected = node

            ctx.fillStyle = node.color
            ctx.fillRect(node.coord_x - node.text_width/2 - 2,
                         node.coord_y - font + 2,
                         node.text_width + 4, font + 4)
            if selectable:
                spring_zoomed = [node.name, '']
                ctx.strokeStyle = '#000'
                ctx.lineWidth = 3
                ctx.beginPath()
                ctx.arc(node.coord_x, node.coord_y, node.text_width/1.2, 0, 2*PI)
                ctx.closePath()
                ctx.stroke()
                ctx.lineWidth = 1
        ctx.fillStyle = '#000'
        for node in self.nodes:
            ctx.fillText(node.name, node.coord_x - node.text_width/2, node.coord_y + 4)
        if spring_zoomed:
            ctx.save()
            self.ctx.font = 3*font + 'px sans-serif'
            ctx.fillStyle = '#00F'
            ctx.fillText(spring_zoomed[0], self.current_x, self.current_y)
            ctx.fillText(spring_zoomed[1], self.current_x, self.current_y + 3 * font)
            ctx.restore()

    def move(self): # pylint: disable=too-many-branches
        """Physical simulation"""
        canvas = document.getElementById('particles')
        if not canvas or canvas.intervalID != self.intervalID:
            clearInterval(self.intervalID)
            return

        def update_speed(node1, node2, distance, strength):
            delta_x = node1.coord_x - node2.coord_x
            delta_y = node1.coord_y - node2.coord_y
            d = delta_x*delta_x + delta_y*delta_y  -  distance
            delta_x *= d * strength
            delta_y *= d * strength
            node1.speed_x -= delta_x
            node1.speed_y -= delta_y
            node2.speed_x += delta_x
            node2.speed_y += delta_y

        def repulsion(node1, node2):
            delta_x = node1.coord_x - node2.coord_x
            delta_y = node1.coord_y - node2.coord_y
            d = delta_x*delta_x + delta_y*delta_y
            delta_x *= -10 / (d+1)
            delta_y *= -10 / (d+1)
            node1.speed_x -= delta_x
            node1.speed_y -= delta_y
            node2.speed_x += delta_x
            node2.speed_y += delta_y

        x_min = y_min = 1e9
        x_max = y_max = -1e9
        for node in self.nodes:
            x_min = min(x_min, node.coord_x)
            y_min = min(y_min, node.coord_y)
            x_max = max(x_max, node.coord_x)
            y_max = max(y_max, node.coord_y)
        speed_x = (self.center_x - (x_max + x_min) / 2) / 100
        speed_y = (self.center_y - (y_max + y_min) / 2) / 100
        for node in self.nodes:
            node.speed_x = speed_x
            node.speed_y = speed_y
        for node1 in self.nodes:
            for node2 in self.nodes:
                if node1.name > node2.name:
                    repulsion(node1, node2)
        for node1, node2, _l1u, _l2u, _l1d, _l2d, length, strength in self.links:
            update_speed(node1, node2, length, strength)
        for node in self.nodes:
            if not node.position_fixed:
                node.coord_x += node.speed_x
                node.coord_y += node.speed_y
                # Apply resistance to stabilize
                node.speed_x /= 1.2
                node.speed_y /= 1.2

        self.draw()

        positions = {}
        for node in self.nodes:
            positions[node.name] = [node.coord_x, node.coord_y]
        localStorage[self.netname] = JSON.stringify(positions)
