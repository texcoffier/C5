"""
Network simulator and grader
"""

##############################################################################
##############################################################################
# Network simulator.
##############################################################################
##############################################################################

def dotted_to_int(dotted):
    """A.B.C.D → int"""
    value = 0
    dotted = dotted.split('.')
    if len(dotted) != 4:
        return -1
    for number in dotted:
        number = int(number)
        if 0 <= number < 256:
            value = 256 * value + number
        else:
            return -1
    return value
def int_to_dotted(value):
    """int → A.B.C.D"""
    if value == -1:
        return ''
    return '.'.join([
        str((value // i) & 0xFF)
        for i in [256*256*256, 256*256, 256, 1]])
def nr_bits_to_dotted(nr_bits):
    """24 will return 255.255.255.0"""
    value = 0
    power = 0x80000000
    while nr_bits:
        value += power
        power //= 2
        nr_bits -= 1
    return int_to_dotted(value)
def netmask_to_nr_bits(value):
    """int → nr_bits_netmask"""
    if value <= 0 or value == '':
        return 0
    nr_0 = 0
    while (value & 1) == 0:
        nr_0 += 1
        value //= 2
    nr_1 = 0
    while value & 1:
        nr_1 += 1
        value //= 2
    if nr_0 + nr_1 == 32:
        return nr_1
    return -1
def bit_and(a_int, b_int):
    """Biwise AND"""
    return int(BigInt(a_int) & BigInt(b_int)) * 1
class Interface:
    """Define the interface and where it is connected"""
    def __init__(self, host, ip_dot, netmask_dot, switche, line_col):
        self.init(host, ip_dot, netmask_dot, switche, '', line_col)
    def init(self,
            host,       # An Host or Router instance
            ip_dot,     # Interface IP
            netmask_dot,# Interface netmask
            switche    , # The switch (network) index. '' for a Route
            gateway_dot,
            line_col
            ):
        self.host = host
        self.ip_dot = ip_dot
        self.netmask_dot = netmask_dot
        self.switche = int(switche)
        self.gateway_dot = gateway_dot
        self.line_col = line_col
        self.prepare()
    def prepare(self):
        # Prepare common values
        self.ip_int = dotted_to_int(self.ip_dot)
        self.netmask_int = dotted_to_int(self.netmask_dot)
        self.network_int = bit_and(self.ip_int, self.netmask_int)
        self.gateway_int = dotted_to_int(self.gateway_dot)
        self.network_dot = int_to_dotted(self.network_int)
        # «|» operator does not work, «+» is correct
        self.broadcast_int = self.network_int + (0xFFFFFFFF - self.netmask_int)
        if self.network_int >= 0:
            self.netmask = netmask_to_nr_bits(self.netmask_int)
        else:
            self.netmask = ''
    def table(self):
        """Returns the table contain the interfaces"""
        return self.host.interfaces
    def active(self):
        """The interface has been configured"""
        return self.switche and self.ip_dot != '' and self.netmask_dot != ''
    def reachable(self, ip_int):
        """Return True if the IP is reachable through this interface"""
        for interfac in self.host.network.by_switch[self.switche]:
            if interfac.ip_int == ip_int and self.netmask_int == interfac.netmask_int:
                return True
class Route(Interface):
    """A route"""
    gateway = None # The Interface of the gateway or None
    def __init__(self, host, ip_dot, netmask_dot, gateway_dot, line_col):
        self.init(host, ip_dot, netmask_dot, '', gateway_dot, line_col)
    def active(self):
        return self.gateway_dot and self.netmask_dot and self.network_dot
    def mergeable(self, other):
        if self.network_int > other.network_int:
            return other.mergeable(self)
        if self.gateway_int != other.gateway_int:
            return False # Pas la même passerelle
        if self.network_int == other.network_int:
            # Même réseau, même passerelle, taille différente.
            if self.netmask_int > other.netmask_int:
                return other
            return self
        if self.netmask_int != other.netmask_int:
            return False # On ne peut agréger que des réseaux de même taille
        new_netmask = (self.netmask_int << 1) & 0xFFFFFFFF
        broadcast_r1 = self.network_int + (0xFFFFFFFF - self.netmask_int)
        if broadcast_r1 + 1 != other.network_int:
            return False # Pas consécutif
        if self.network_int & (new_netmask ^ self.netmask_int):
            return False # Le petit n'a pas son dernier bit à 0
        return Route(None, None, self.network_dot, int_to_dotted(new_netmask))
    def table(self):
        """Returns the table contain the routes"""
        return self.host.routes
class Node:
    """An host or a router. The switches are not defined at all"""
    def __init__(self, network, index, interfaces, routes):
        self.running = True # XXX PARAMETRE
        self.network = network
        self.index = index
        self.interfaces = []
        for switche, ip_dot, netmask_dot, line_col in interfaces:
            i = Interface(self, ip_dot, netmask_dot, switche, line_col)
            self.interfaces.append(i)
        self.is_a_router = len(interfaces) != 1
        if self.is_a_router:
            self.name = 'ABCDEFGH'[index]
        else:
            self.name = 'M' + (index + 1)
        self.routes = []
        for ip_dot, netmask_dot, gateway_dot, line_col in routes:
            i = Route(self, ip_dot, netmask_dot, gateway_dot, line_col)
            self.routes.append(i)
        # Update network.by_ip network.by_switch
        for interfac in self.interfaces:
            if interfac.ip_int < 0:
                continue
            network.by_ip[interfac.ip_int] = interfac
            if interfac.switche not in network.by_switch:
                network.by_switch[interfac.switche] = []
            network.by_switch[interfac.switche].append(interfac)
        # Create the sorted route list
        sorted_routes = []
        for i, route in enumerate(self.routes):
            route.network_int = dotted_to_int(route.network_dot)
            route.netmask_int = dotted_to_int(route.netmask_dot)
            route.gateway_int = dotted_to_int(route.gateway_dot)
            if route.netmask_int >= 0: # and route.gateway_int in network.by_ip:
                route.netmask = netmask_to_nr_bits(route.netmask_int)
                sorted_routes.append([999 - route.netmask, i, route]) # Bugged JS sort
        sorted_routes.sort()
        self.sorted_routes = [route[2] for route in sorted_routes]
    def ping(self, destination_int, depth=0, trace=None): # pylint: disable=too-many-branches
        """Returns the distance of the ping.
        999 if it is unpinguable.
        """
        if not self.running:
            return 999
        if depth > 10:
            if trace:
                trace.append("TTL dépassé")
            return 999
        for interfac in self.interfaces:
            if interfac.ip_int == destination_int:
                if trace:
                    trace.append("C'est moi même !")
                return depth + 1

        for interfac in self.interfaces:
            if interfac.active() and bit_and(destination_int, interfac.netmask_int) == interfac.network_int:
                if trace:
                    trace.append("Envoi sur le réseau local "
                                 + interfac.network_dot + ' ' +  interfac.netmask_dot)
                if destination_int in self.network.by_ip:
                    i = self.network.by_ip[destination_int]
                    if i in self.network.by_switch[interfac.switche]:
                        # if trace:
                        #     trace.append("La destination est sur ce switch")
                        return depth + 1
        for route in self.sorted_routes:
            if bit_and(destination_int, route.netmask_int) == route.network_int:
                an_interface_up_to_the_gateway = False
                for interfac in self.interfaces:
                    if interfac.active() and bit_and(route.gateway_int, interfac.netmask_int) == interfac.network_int:
                        an_interface_up_to_the_gateway = True
                        break
                if route.gateway and an_interface_up_to_the_gateway and route.gateway_int in self.network.by_ip:
                    if route.gateway.host.running:
                        if trace:
                            trace.append(self.name + " utilise la route : " + route.network_dot
                                        + ' ' + route.netmask_dot
                                        + ' via ' + route.gateway_dot)
                        return route.gateway.host.ping(destination_int, depth+1, trace=trace)
                    if trace:
                        trace.append("La passerelle " + route.gateway_dot + " est éteinte")
                elif trace:
                    trace.append("La passerelle " + route.gateway_dot + " n'est pas atteignable")
            # if trace:
            #     trace.append("Route non utilisable : " + route.network_dot
            #                  + ' ' + route.netmask_dot
            #                  + ' via ' + route.gateway_dot
            #                  + ' parce que ' + int_to_dotted(destination_int)
            #                  + ' &amp; ' + route.netmask_dot
            #                  + ' = ' + int_to_dotted(bit_and(destination_int, route.netmask_int))
            #                  + ' != '
            #                  + route.network_dot
            #                  )
        if trace:
            trace.append("Réseau destination non atteignable")
        return 999
class Analyze:
    nr_bad_network_number = 0
    nr_bad_netmask = 0
    nr_ip_not_in_network = 0
    nr_duplicate_ip = 0
    nr_not_last_ip = 0
    nr_route_network_netmask_incoherent = 0
    nr_route_to_itself = 0
    nr_bad_gateway_ip = 0
    nr_routers = 0
    nr_routes = 0
    nr_interfaces = 0
    nr_max_routers_per_switch = 0
    is_connexe = 0
    total_ping_fails = 0
    total_ping_distance = 0
    r_total_ping_fails = 0
    r_total_ping_distance = 0
    s_total_ping_fails = 0
    s_total_ping_distance = 0
    l_total_ping_fails = 0
    l_total_ping_distance = 0
    nr_aggregatable = 0
    nr_too_big_destination_network = 0
class Network:
    """The full network"""
    canvas = None
    element_td = None # TD to explain in ping table
    question = 0

    def __init__(self,
            nodes     # List of: [ interfaces [Switch,IP,Netmask], routes [IP,Netmask, gatway]]
            ):
        self.name = name
        self.hosts = []
        self.routers = []
        self.nodes = []
        self.by_switch = {}
        self.by_ip = {}
        self.analyze = Analyze()
        for interfaces, routes in nodes:
            if len(routes) == 1:
                node = Node(self, len(self.hosts), interfaces, routes)
                self.hosts.append(node)
            else:
                node = Node(self, len(self.routers), interfaces, routes)
                self.routers.append(node)
            self.nodes.append(node)
        self.first_router = len(self.hosts)

        # Create a direct link to the gateway
        for node in self.nodes:
            for route in node.routes:
                route.gateway = None
                if route.gateway_int not in self.by_ip:
                    continue # Gateway does not exist
                gateway = self.by_ip[route.gateway_int]
                gateway_usable = False
                for interfac in node.interfaces:
                    if (interfac.switche == gateway.switche
                            and interfac.network_int == gateway.network_int
                            and interfac.netmask_int == gateway.netmask_int):
                        # The 2 interfaces are on the same switch and same network
                        gateway_usable = True
                        break
                if not gateway_usable:
                    continue
                route.gateway = gateway
    def analyze_nr_routers(self):
        analyze = self.analyze
        nr_routers_per_switch = {}
        for node in self.nodes:
            if not node.is_a_router:
                continue
            analyze.nr_interfaces = 0
            for interfac in node.interfaces:
                if interfac.active():
                    if interfac.switche not in nr_routers_per_switch:
                        nr_routers_per_switch[interfac.switche] = 0
                    nr_routers_per_switch[interfac.switche] += 1
                    analyze.nr_interfaces += 1
            if analyze.nr_interfaces == 0:
                continue
            if analyze.nr_interfaces > nbr_interface_used:
                nbr_interface_used = analyze.nr_interfaces
            analyze.nr_routers += 1
            for route in node.routes:
                if route.network_dot and route.netmask_dot and route.gateway_dot:
                    analyze.nr_routes += 1

        for i in nr_routers_per_switch: # pylint: disable=consider-using-dict-items
            if nr_routers_per_switch[i] > analyze.nr_max_routers_per_switch:
                analyze.nr_max_routers_per_switch = nr_routers_per_switch[i]
    def analyze_connexity(self):
        todo = [0]
        done = {}
        while len(todo):
            i = todo.pop()
            for interfac in self.by_switch[i+1]:
                host = interfac.host
                if host.is_a_router:
                    for interf in host.interfaces:
                        if interf.switche:
                            j = interf.switche - 1
                            if not done[j]:
                                todo.append(j)
                                done[j] = True
        if len(done) == len(self.hosts):
            self.analyze.is_connexe = 1
        else:
            self.analyze.is_connexe = 0
    def pings_stats(self):
        nr_ping_fails = 0
        pings_distance = 0
        for node1 in self.hosts:
            if not node1.interfaces[0].active():
                continue
            for node2 in self.hosts:
                if node2.interfaces[0].active():
                    distance = node1.ping(node2.interfaces[0].ip_int, 0)
                    if distance == 999:
                        nr_ping_fails += 1
                    else:
                        pings_distance += distance
        return nr_ping_fails, pings_distance
    def analyze_pings(self):
        analyze = self.analyze

        # No failure
        analyze.total_ping_fails, analyze.total_ping_distance = self.pings_stats()

        # One router failure
        for router in self.routers:
            router.running = False # XXX
            ping_fail, ping_distance = self.pings_stats()
            analyze.r_total_ping_fails += ping_fail
            analyze.r_total_ping_distance += ping_distance
            router.running = True

        # One switch failure
        for switche in self.hosts:
            switche = switche.index + 1
            for router in self.routers:
                for interf in router.interfaces:
                    interf.ip_dot_sav = interf.ip_dot
                    if interf.switche == switche:
                        del self.by_ip[interf.ip_int]
                        interf.ip_dot = ''
                        interf.prepare()
            ping_fail, ping_distance = self.pings_stats()
            analyze.s_total_ping_fails += ping_fail
            analyze.s_total_ping_distance += ping_distance
            for router in self.routers:
                for interf in router.interfaces:
                    interf.ip_dot = interf.ip_dot_sav
                    interf.prepare()
                    self.by_ip[interf.ip_int] = interf

        # One link failure
        for router in self.routers:
            for interf in router.interfaces:
                if interf.active():
                    interf.ip_dot_sav = interf.ip_dot
                    del self.by_ip[interf.ip_int]
                    interf.ip_dot = ''
                    interf.prepare()
                    ping_fail, ping_distance = self.pings_stats()
                    analyze.l_total_ping_fails += ping_fail
                    analyze.l_total_ping_distance += ping_distance
                    interf.ip_dot = interf.ip_dot_sav
                    interf.prepare()
                    self.by_ip[interf.ip_int] = interf
    def analyze_aggregation(self):
        """Compute the number of aggregatable routes"""
        def aggregate(routes):
            for r1 in routes:
                if not r1.active():
                    continue
                for r2 in routes:
                    if r1 is r2:
                        continue
                    if not r2.active():
                        continue
                    m = r1.mergeable(r2)
                    if m:
                        routes = [r for r in routes if r is not r1 and r is not r2]
                        routes.append(m)
                        return 1 + aggregate(routes)
            return 0
        self.analyze.nr_aggregatable = 0
        for router in self.routers:
            self.analyze.nr_aggregatable += aggregate(router.routes)
    def aggregated_networks(self):
        """The minimal network containing all subnets"""
        network_min = 0xFFFFFFFF
        broadcast_max = 0
        for hosts in self.hosts:
            network_min = min(network_min, hosts.interfaces[0].network_int)
            broadcast_max = max(broadcast_max, hosts.interfaces[0].broadcast_int)
        netmask_int = 0xFFFFFFFF
        size = 1
        for _ in range(32):
            netmask_int -= size
            size *= 2
            network_int = bit_and(network_min, netmask_int)
            if network_int == bit_and(broadcast_max, netmask_int):
                # All IPS on the same network
                return [network_int, netmask_int, network_int + size - 1]
        bug_aggregated_networks
    def analyze_destination_size(self):
        network_int, _netmask_int, broadcast_int = self.aggregated_networks()
        for router in self.routers:
            for route in router.routes:
                if not route.active():
                    continue
                if route.network_int < network_int or route.broadcast_int > broadcast_int:
                    self.analyze.nr_too_big_destination_network += 1

    def get_stats_html(self):
        analyze = self.analyze
        texts = []
        texts.append('<p>' + analyze.nr_routers + ' routeurs configurés. ')
        texts.append('' + analyze.nr_routes + ' routes définies sur les routeurs.')
        texts.append('<p>≤' + analyze.nr_interfaces + ' interfaces utilisées sur les routeurs. ')
        texts.append('≤' + analyze.nr_max_routers_per_switch + ' routeurs par switch.')
        texts.append('<table style="background: #0004"><tr><th>Pannes :<th>Aucune<th>1 routeur<th>1 switch<th>1 interface</tr>'
                     + '<tr><th>#échec ping<td>' + analyze.total_ping_fails
                     + '<td>' + analyze.r_total_ping_fails
                     + '<td>' + analyze.s_total_ping_fails
                     + '<td>' + analyze.l_total_ping_fails
                     + '<tr><th>Distances pings<td>' + analyze.total_ping_distance
                     + '<td>' + analyze.r_total_ping_distance
                     + '<td>' + analyze.s_total_ping_distance
                     + '<td>' + analyze.l_total_ping_distance
                     + '</table>'
                     )
        analyze.nr_problems = (
            (1 - analyze.is_connexe) + analyze.nr_bad_network_number + analyze.nr_bad_netmask
             + analyze.nr_ip_not_in_network + analyze.nr_duplicate_ip + analyze.nr_not_last_ip
             + analyze.nr_route_network_netmask_incoherent + analyze.nr_route_to_itself
             + analyze.nr_bad_gateway_ip + analyze.nr_aggregatable
             + analyze.nr_too_big_destination_network)
        texts.append('Problèmes : <div class="problems">'
            + ' <div>' + (1 - analyze.is_connexe) + '<div>Réseau non connexe</div></div>'
            + '+<div>' + analyze.nr_bad_network_number + '<div>Mauvaise adresse réseau</div></div>'
            + '+<div>' + analyze.nr_bad_netmask + '<div>Mauvais netmaks</div></div>'
            + '+<div>' + analyze.nr_ip_not_in_network + '<div>IP hors du réseau</div></div>'
            + '+<div>' + analyze.nr_duplicate_ip + '<div>IP en double</div></div>'
            + '+<div>' + analyze.nr_not_last_ip + '<div>Pas la dernière IP du réseau</div></div>'
            + '+<div>' + analyze.nr_route_network_netmask_incoherent + '<div>Incohérence adresse réseau et netmask</div></div>'
            + '+<div>' + analyze.nr_route_to_itself + '<div>Passerelle vers soit-même</div></div>'
            + '+<div>' + analyze.nr_bad_gateway_ip + '<div>Passerelle non atteignable</div></div>'
            + '+<div>' + analyze.nr_aggregatable + '<div>Route aggrégeable</div></div>'
            + '+<div>' + analyze.nr_too_big_destination_network + '<div>Réseau destination trop grand</div></div>'
            + '</div> → ' + analyze.nr_problems
            )
        # PINGS MATRICE
        texts.append('<TABLE><TR><TD><TABLE><TR><TH style="text-align: right">↗')
        for node2 in self.hosts:
            if node2.interfaces[0].active():
                texts.append('<TH>' + node2.name)
        texts.append("</TR>")
        for node1 in self.hosts:
            if not node1.interfaces[0].active():
                continue
            texts.append('<TR><TH>' + node1.name)
            for node2 in self.hosts:
                if node2.interfaces[0].active():
                    trace = []
                    distance = node1.ping(node2.interfaces[0].ip_int, 0, trace)
                    if distance == 999:
                        distance = ''
                        html_class = 'badping'
                    else:
                        if distance == 1:
                            distance = '·'
                        html_class = 'goodping'
                    texts.append('<TD onclick="document.getElementById(\'traceroute\').innerHTML=unescape(\''
                        + escape(JSON.stringify('<br>'.join(trace))[1:-1])
                        + '\');" class="' + html_class + '">' + distance)
            texts.append('</TR>')
        texts.append('</TABLE><TD id="traceroute">Cliquez sur une case pour voir le chemin</TR></TABLE>')
        return ''.join(texts)

    def dump(self):
        """
        For debugging
        """
        for host in self.hosts:
            print('Host ' + host.name
                + ' ' + host.interfaces[0].ip_dot
                + ' ' + host.interfaces[0].network_dot
                + ' ' + host.interfaces[0].netmask_dot
                + ' ' + host.routes[0].gateway_dot
                )
        for interfac, _ in enumerate(self.routers[0].interfaces):
            for router in self.routers:
                print('Interf ' + router.name
                      + ' ' + router.interfaces[interfac].ip_dot
                      + ' ' + router.interfaces[interfac].network_dot
                      + ' ' + router.interfaces[interfac].netmask_dot
                      + ' ' + router.interfaces[interfac].line_col
                )
        for route, _ in enumerate(self.routers[0].routes):
            for router in self.routers:
                print('Route ' + router.name
                        + ' ' + router.routes[route].network_dot
                        + ' ' + router.routes[route].netmask_dot
                        + ' ' + router.routes[route].gateway_dot
                        + ' ' + router.routes[route].line_col
                )

##############################################################################
##############################################################################
# C5 interface
##############################################################################
##############################################################################

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """Network simulator"""
    default_options = {
        'language': 'none',
        'extension': 'txt',
        'coloring': 0,
        'positions' :
            {
            "question":[100,46,0,30,"#EFE"],
            "tester":[100,1,0,1,"#EFE"],
            "editor":[1,55,0,100,"#FFF"],
            "compiler":[56,44,0,100,"#EEF"],
            "executor":[100,50,30,70,"#EEF"],
            "time":[80,20,98,2,"#0000"],
            "index":[0,1,0,100,"#0000"]
            },
        "display_indent": 0,
        "display_compile_run": 0,
        "display_line_numbers": 0,
        "automatic_compilation": 1,
        }
    def run_compiler(self, source):
        """Compile, display errors and return the executable"""
        def split():
            cells = []
            j = -1
            for cell in line.split('│')[:-1]:
                j += 1
                cells.append([[i, j], replace_all(cell, ' ', '')])
                j += len(cell)
            return cells[2:]

        ######################################################################
        # EXTRACT NETWORK DEFINITION FROM TEXT
        ######################################################################
        source = replace_all(source, '┃', '│')
        state = 'init'
        interfaces = []
        routes = []
        networks = []
        for i, line in enumerate(source.split('\n')):
            if not line.startswith('│'):
                if line.startswith('┗'):
                    state = 'routes'
                else:
                    if '«' in line:
                        for i in range(1, 9):
                            key = i + ':«'
                            if key in line:
                                network = line.split(key)[1].split('»')[0]
                                if '/' not in network:
                                    self.post('compiler', "Il manque '/' : " + network)
                                    return
                                ip, bits = network.split('/')
                                ip_int = dotted_to_int(ip)
                                if ip_int == -1:
                                    self.post('compiler', "IP de réseau invalide : " + ip)
                                    return
                                nr_bits = int(bits)
                                if nr_bits < 1 or nr_bits > 30:
                                    self.post('compiler', "Nombre de bits invalide : " + bits)
                                    return
                                nbr_ip = 1 << (32-bits)
                                networks.append([
                                    # Host single interface
                                    [[i, int_to_dotted(ip_int+1), nr_bits_to_dotted(nr_bits)]],
                                    # Host single route
                                    [['0.0.0.0', '0.0.0.0', int_to_dotted(ip_int + nbr_ip - 2)]]
                                    ])
                                if len(networks) != i:
                                    self.post('compiler', "Il faut indiquer les réseaux dans l'ordre")
                                    return
                continue
            if state == 'init':
                state = 'interfaces'
            elif state == 'interfaces':
                interfaces.append(split())
            elif state == 'routes':
                routes.append(split())
        routes = routes[1:]
        if len(interfaces) % 3 != 0:
            self.post('compiler', "Il n'y a pas 3 lignes par interface.<br>" + JSON.stringify(interfaces))
            return
        if len(routes) % 3 != 0:
            self.post('compiler', "Il n'y a pas 3 lignes par route.")
            return
        nbr_routers = len(interfaces[0])
        for interf in interfaces:
            if len(interf) != nbr_routers:
                self.post('compiler', "Dans la première table il n'y a pas les bonnes colonnes")
                return
        for route in routes:
            if len(route) != nbr_routers:
                self.post('compiler', "Dans la deuxième table il n'y a pas les bonnes colonnes")
                return
        if len(networks) == 0:
            self.post('compiler', "Aucun réseau défini. 1:«10.0.0.0/8» 2:«192.168.0.1/24» ...")
            return
        ######################################################################
        # CREATE THE NETWORK
        ######################################################################
        for r in range(nbr_routers):
            node_interfaces = []
            node_routes = []
            for i in range(len(interfaces)//3):
                node_interfaces.append(
                    [interfaces[3*i][r][1], interfaces[3*i+1][r][1], interfaces[3*i+2][r][1], interfaces[3*i][r][0]]
                )
            for i in range(len(routes)//3):
                node_routes.append(
                    [routes[3*i][r][1], routes[3*i+1][r][1], routes[3*i+2][r][1], routes[3*i][r][0]]
                )
            networks.append([node_interfaces, node_routes])
        if False:
            print('Router interface')
            for i in interfaces:
                print(JSON.stringify(i))
            print('Routes')
            for r in routes:
                print(JSON.stringify(r))
            print('networks')
            for n in networks:
                print(JSON.stringify(n))
        net = Network(networks)
        # net.dump()
        net.analyze_nr_routers()
        net.analyze_connexity()
        net.analyze_pings()
        net.analyze_aggregation()
        net.analyze_destination_size()
        ######################################################################
        # UPDATE PROBLEM STATISTICS AND DISPLAY RED HIGHLIGHTING FEEDBACK
        ######################################################################
        analyze = net.analyze
        for router in net.routers:
            if not router.running:
                continue
            for interf_router in router.interfaces:
                if not interf_router.switche or not interf_router.ip_dot:
                    continue
                interf_sw = net.by_switch[interf_router.switche][0]
                ip_int = interf_router.ip_int
                line, col = interf_router.line_col
                line += 1
                col += 1
                if interf_router.switche < 1 or interf_router.switche > len(net.hosts):
                    analyze.nr_bad_network_number += 1
                    self.post('error', [line, col, 15])
                if ip_int <= interf_sw.network_int or ip_int >= interf_sw.broadcast_int:
                    analyze.nr_ip_not_in_network += 1
                    self.post('error', [line+1, col, 15])
                elif ip_int in net.by_ip and net.by_ip[ip_int] is not interf_router:
                    analyze.nr_duplicate_ip += 1
                    self.post('error', [line+1, col, 15])
                elif interf_router.ip_int < interf_sw.broadcast_int - 3:
                    analyze.nr_not_last_ip += 1
                    self.post('error', [line+1, col, 15])
                if interf_sw.netmask_int != interf_router.netmask_int:
                    analyze.nr_bad_netmask += 1
                    self.post('error', [line+2, col, 15])
            for route in router.routes:
                line, col = route.line_col
                line += 1
                col += 1
                if route.gateway_dot:
                    if router.ping(route.gateway_int) != 1:
                        analyze.nr_bad_gateway_ip += 1
                        self.post('error', [line+2, col, 15])
                    elif net.by_ip[route.gateway_int].host is router:
                        analyze.nr_route_to_itself += 1
                        self.post('error', [line+2, col, 15])
                if route.ip_dot and route.netmask_dot:
                    if bit_and(route.ip_int, route.netmask_int) != route.ip_int:
                        analyze.nr_route_network_netmask_incoherent += 1
                        self.post('error', [line, col, 15])
                        self.post('error', [line+1, col, 15])
                if route.ip_dot.replace(RegExp('[^0-9.]*'), '') and route.ip_int <= 0:
                    self.post('error', [line, col, 15])
                if route.netmask_dot and (route.netmask_int <= 0 or route.netmask < 0):
                    self.post('error', [line+1, col, 15])
                if route.gateway_dot and route.gateway_int <= 0:
                    self.post('error', [line+2, col, 15])
        ######################################################################
        # DISPLAY HTML
        ######################################################################
        self.post('compiler',
            '''<style>
            TD, TH { background: #FFF8 }
            .compiler > DIV:nth-child(n+1) { font-family: sans-serif; white-space: normal }
            .compiler > DIV:nth-child(n+1) P { margin: 0px }
            .compiler TABLE TD { vertical-align: top; text-align: center }
            .compiler .goodping { background: #0F08 }
            .compiler .badping { background: #F008 }
            #particles {
                  position: absolute;
                  width: 100%;
                  margin-left: calc(0em - var(--pad));
                  height: 70vh;
                  bottom: 0px;
                  z-index: 1;
            }
            #traceroute { font-size: 80% }
            .problems, .problems DIV { display: inline }
            .problems > DIV > DIV { display: none; position: absolute; margin-top: 1em; background: #FF0 }
            .problems > DIV:hover > DIV { display: inline }
            </style>
            <img src="data:dfsd" style="visibility: hidden; position:absolute" onerror="
              var e = document.createElement('SCRIPT');
              e.src = 'JS/bare_particles.js' + window.location.search;
              document.body.appendChild(e);
              "><div style="z-index:10; position: absolute;">
            ''' + net.get_stats_html())
        ######################################################################
        # DISPLAY GRAPHIC
        ######################################################################
        nodes = []
        links = []
        for host in net.hosts:
            nodes.append(['M'+(host.index+1), '#DDD'])
            nodes.append(['S'+(host.index+1), '#BBB'])
            links.append([2*host.index, 2*host.index+1,
                          host.interfaces[0].ip_dot, '',
                          host.interfaces[0].netmask_dot, '',
                          2000, 0.000001])
        start = 2*len(net.hosts)
        for router in net.routers:
            nodes.append([router.name, '#8F8'])
            for interf in router.interfaces:
                if interf.switche:
                    links.append([start, 2*(interf.switche-1)+1,
                                interf.ip_dot, '',
                                interf.netmask_dot, '',
                                40000, 0.000001])
            start += 1
        nodes = "'" + escape(JSON.stringify(nodes)) + "'"
        links = "'" + escape(JSON.stringify(links)) + "'"
        self.post('compiler',
            '''<canvas id="particles"></canvas>
            <img src="data:dfsd" style="visibility: hidden" onerror="
            function wait() {
            if ( window.Particles )
            new Particles(COURSE+':'+ccccc.current_question, JSON.parse(unescape('''
            + nodes + ')),JSON.parse(unescape('
            + links + ''')));
            else setTimeout(wait, 100); }
            wait();">''')

        return net

    def run_executor(self):
        """Execute the compiled code"""
        self.post('executor', "Nada")
