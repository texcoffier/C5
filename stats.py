"""
Works only in javascript
"""
# pylint: disable=bare-except,invalid-name,eval-used

ATTRIBUTES = {}
COORDS = []
STATS = STATS

def get_labels(x_min, x_max):
    power = 0.01
    while True:
        if (x_max - x_min) / power < 30:
            break
        if (x_max - x_min) / power / 2 < 30:
            power *= 2
            break
        # if (x_max - x_min) / power / 2.5 < 30:
        #     power *= 2.5
        #     break
        if (x_max - x_min) / power / 5 < 30:
            power *= 5
            break
        power *= 10
    if power < 1:
        digits = 2
    else:
        digits = 0
    return power * Math.floor(x_min / power), power, digits

def get_data(element):
    element.innerHTML = '\n'.join([
        str(xx) + ' ' + str(yy) + ' ' + color + ' ' + radius.toFixed(1)
        + ' ' + str(opacity) + ' ' + key
        for xx, yy, color, radius, opacity, key in COORDS])

def set_button(values):
    default_values = {
        'selector_merge': 'first_interaction > 0  && work_time > 0 && student.match(/.*[0-9][0-9].*/)',
        'selector_average': 'true',
        'x': '0',
        'y': '0',
        'red': '0',
        'green': '0',
        'blue': '0',
        'circle_radius': '10',
        'opacity': '0.3',
        'bins': '0',
        'merge': "key",
        'group': "key",
    }
    for key, default_value in default_values.Items():
        document.getElementById(key).value = values[key] or default_value

def stats_init():
    for session_name, stats in STATS.Items():
        for student, values in stats.Items():
            if 'sessions' in values:
                for timestamp in values.sessions[:1]: # Only first work session
                    d = Date()
                    d.setTime(1000 * timestamp)
                    values['Year'] = d.getFullYear()
                    values['Hour'] = d.getHours()
                    values['Date'] = d.getDate()
                    values['MinuteDay'] = d.getHours()*24 + d.getMinutes()
                    values['Month'] = d.getMonth()
                    values['WeekDay'] = d.getDay()
            values['session'] = session_name
            values['student'] = student
            values['key'] = session_name + '/' + student

    for _session_name, stats in STATS.Items():
        for _student, values in stats.Items():
            for item in values:
                ATTRIBUTES[item] = True

    document.getElementById('header').innerHTML = '''
    <style>
    BODY { font-family: sans-serif }
    #header > DIV { display:flex }
    #header > DIV > INPUT { flex:1 }
    TABLE.average TD:nth-child(2), TABLE.average TD:nth-child(3) { text-align: right }
    TABLE.average TD { font-size: 60% }
    CANVAS { width: 1024px; height: 1024px; }
    TD { vertical-align: top }

    </style>
    A disk is the resume about one student for one session but may contains several time slots ('session' attribute).<br>
    «key=session+'/'+student» is the initial disk key → merge key → average key<br>
    Click on a disk to list the values for the selected disk.<br>
    The left table is about all the disks displayed : number of times the attribute was defined and its average.<br>
    Examples : <button onclick="set_button({
        'x': 'first_interaction', 'y': 'work_time'})">X:time Y=worktime</button>
        <button onclick="set_button({
        'x': 'work_time', 'y': 'grade'})">X:worktime Y=grade</button>
    <div>
    Merge the disks if the expression is true:
    <input id="selector_merge"
           value="key.startsWith('COMPILE_REMOTE/LIFAPI') && student.indexOf('.') == -1">
    </div>
    <div>Merge the disks with the same value: <input id="merge" value="key"></div>
    <div>
    Average the disks if the expression is true:
    <input id="selector_average"
           value="true">
    </div>
    <div>Average the disks with the same value: <input id="group" value="key"></div>
    <div>X coordinate of the disk: <input id="x" value="nr_MouseDown"></div>
    <div>Y coordinate of the disk: <input id="y" value="nr_keypress + nr_deadkey"></div>
    <div>Red value (0…1) for the disk color: <input id="red" value="nr_CopyRejected + nr_PasteRejected > 0"></div>
    <div>Green value (0…1) for the disk color: <input id="green" value="nr_tag > 0"></div>
    <div>Blue value (0…1) for the disk color: <input id="blue" value="the_time_bonus > 0"></div>
    <div>Radius of the disk in pixel: <input id="circle_radius" value="1 + 2*Math.sqrt(nr_save)"></div>
    <div>Opacity (0…1) of the disk: <input id="opacity" value="0.5"></div>
    <div>Number of bins on the X axis. One curve per group name: <input id="bins" value="0"></div>
    '''
    try:
        params = str(window.location).split(RegExp('[/?]'))[-2]
        params = JSON.parse(decodeURIComponent(params))
        for key, value in params.Items():
            document.getElementById(key).value = value
    except:
        pass

def identify(event):
    rect = event.target.getBoundingClientRect()
    stats_update(event.clientX - rect.left,
                 event.clientY - rect.top)

def update_sums(sums, values):
    for item, value in values.Items():
        if item not in sums:
            sums[item] = []
        if isinstance(value, Array):
            sums[item].append(*value)
        else:
            sums[item].append(value)

def get_bounding_box(coords):
    x_min = y_min = 1e100
    x_max = y_max = radius_max = 0
    for xx, yy, _color, radius, _opacity, _key in coords:
        if xx > x_max:
            x_max = xx
        if xx < x_min:
            x_min = xx
        if yy > y_max:
            y_max = yy
        if yy < y_min:
            y_min = yy
        if radius > radius_max:
            radius_max = radius
    x_min -= radius_max / 128
    y_min -= radius_max / 128
    x_max += radius_max / 128
    y_max += radius_max / 128
    return x_min, x_max, y_min, y_max

def get_ctx(sums):
    html = []
    for key, values in sums.Items():
        if isNaN(values[0]):
            continue
        html.append('<tr><td>' + key + '<td>' + len(values)
            + '<td>' + (sum(values) / len(values)).toFixed(2) + '</tr>')
    html.sort()

    top = document.getElementById('top')
    top.innerHTML = ('''
    <table><tr><td>
    <table class="average">'''
    + ''.join(html)
    + '</table><td><canvas id="canvas" width="1024" height="1024"></canvas>'
    + '<td><div id="details"></div><br>'
    # + 'X = ' + x_min + ' → ' + x_max + '<br>'
    # + 'Y = ' + y_min + ' → ' + y_max + '<br>'
    + '<b>Click on a disk to see details</b><br>'
    + '<pre onclick="get_data(this)">Click here to get all disks raw data</pre></tr></tr>')
    canvas = document.getElementById('canvas')
    canvas.onclick = identify
    ctx = canvas.getContext('2d')
    ctx.strokeStyle = '#000'
    ctx.lineWidth = 1
    ctx.font = '10px sans-serif'
    return ctx

def value2color(values, attr):
    value = Math.floor(Number(window[attr](values) * 255))
    if isNaN(value) or value < 0:
        value = 0
    elif value > 255:
        value = 255
    value = value.toString(16)
    if len(value) == 1:
        value = '0' + value
    return value

def get_color(values):
    return (value2color(values, 'red')
          + value2color(values, 'green')
          + value2color(values, 'blue'))

def get_averages(sums, get_sum=False):
    averages = {}
    for key, values in sums.Items():
        if isNaN(values[0]):
            ok = True
            for i in values:
                if i != values[0]:
                    ok = False
                    break
            if ok:
                averages[key] = values[0]
            else:
                averages[key] = '?'
            continue
        if get_sum:
            if values[0] > 1000000000:
                # It is a time
                averages[key] = sum(values) / len(values)
            else:
                averages[key] = sum(values)
            averages['NrMerged'] = max(len(values), averages['NrMerged'] or 0)
        else:
            averages[key] = sum(values) / len(values)
            averages['NrAveraged'] = max(len(values), averages['NrAveraged'] or 0)
    return averages

def mouse_in_disc(ctx, details, event_x, event_y, x_canvas, y_canvas, radius, key, stats):
    if event_x:
        # ctx.fillRect(event_x, event_y, 10, 10)
        d = ((event_x - x_canvas)**2 + (event_y - y_canvas)**2) ** 0.5
        if d < radius:
            ctx.save()
            ctx.globalAlpha = 1
            ctx.lineWidth = 2
            ctx.strokeStyle = '#FFF'
            ctx.strokeText(key, x_canvas, y_canvas)
            ctx.fillStyle = '#000'
            ctx.fillText(key, x_canvas, y_canvas)
            ctx.restore()
            details.append([key, stats])

def display_details(details):
    if len(details):
        html = []
        for key, item in details:
            s = '<p><b>' + key + '</b><ul>'
            for k, v in item.Items():
                s += '<li>' + k + ' : ' + v
            s += '</ul>'
            html.append(s)
        document.getElementById('details').innerHTML = ''.join(html)

def get_label(txt, digits):
    if txt < 1000000000:
        return txt.toFixed(digits)
    d = Date()
    d.setTime(1000 * txt)
    return d.getFullYear() % 100 + '-' + two_digit(d.getMonth()+1)

def draw_verticals(ctx, xx_real, x_min, x_max, delta, digits):
    while xx_real < x_max:
        xx = 1024 * (xx_real - x_min) / (x_max - x_min + 1e-9)
        ctx.beginPath()
        ctx.moveTo(xx, 0)
        ctx.lineTo(xx, 1024)
        ctx.stroke()

        label = get_label(xx_real, digits)
        width = ctx.measureText(label).width
        ctx.fillText(label, xx - width/2, 1023)

        xx_real += delta

def draw_horizontals(ctx, xx_real, y_min, y_max, delta, digits):
    while xx_real < y_max:
        xx = 1024 - 1024 * (xx_real - y_min) / (y_max - y_min + 1e-9)
        ctx.beginPath()
        ctx.moveTo(0, xx)
        ctx.lineTo(1024, xx)
        ctx.stroke()

        label = get_label(xx_real, digits)
        height = ctx.measureText(label).fontBoundingBoxAscent
        ctx.fillText(label, 0, xx + height/2 - 1)

        xx_real += delta

def stats_update(event_x, event_y):
    need_update = False
    params = {}
    for variable in ['selector_merge', 'selector_average', 'x', 'y', 'red', 'green', 'blue', 'circle_radius', 'opacity', 'bins', 'merge', 'group']:
        value = document.getElementById(variable).value
        params[variable] = value
        if value != stats_init[variable]:
            need_update = True
            stats_init[variable] = value
        for attribute in ATTRIBUTES:
            value = value.replace(RegExp('\\b(' + attribute + ')\\b', 'g') , '(values.$1||0)')
        try:
            if variable != 'bins':
                window[variable] = eval('function _(values) { return ' + value + ';}; _')
            else:
                window[variable] = params[variable]
        except:
            return
    if not need_update and not event_x:
        return

    path = str(window.location).split('/')
    ticket = path[-1].split('?')[1]
    path[-1] = encodeURIComponent(JSON.stringify(params)) + '?' + ticket
    window.history.replaceState('_a_', '', '/'.join(path))
    COORDS.splice(0, COORDS.length) # Clean

    merged = {}
    for session_name, stats in STATS.Items():
        for key, values in stats.Items():
            if window.selector_merge(values):
                group = window.merge(values)
                if group not in merged:
                    merged[group] = {}
                update_sums(merged[group], values)
    for group, value in merged.Items():
        merged[group] = get_averages(value, True)

    stats_for = {}
    for session_name, values in merged.Items():
        if window.selector_average(values):
            group = window.group(values)
            if group not in stats_for:
                stats_for[group] = {}
            update_sums(stats_for[group], values)
    for group, values in stats_for.Items():
        stats_for[group] = get_averages(values)

    if window.bins > 0:
        x_min = 1e50
        x_max = 0
        for key, stats in stats_for.Items():
            xx = window.x(values)
            if xx < x_min:
                x_min = xx
            if xx > x_max:
                x_max = xx
        x_max += 0.001 # To not lost the max value
        all_lines = []
        for key, stats in stats_for.Items():
            all_sums = []
            for i in range(window.bins):
                all_sums.append({})
            for student, values in stats.Items():
                xx = window.x(values)
                i = int(window.bins * (xx - x_min) / (x_max - x_min))
                update_sums(all_sums[i], values)
            coords = []
            for i, sums in enumerate(all_sums):
                averages = get_averages(sums)
                # XXX trop param
                coords.append([0,
                            window.y(averages),
                            get_color(averages),
                            window.circle_radius(averages),
                            window.opacity(averages),
                            'group:' + key,
                            (x_min + i/window.bins*(x_max-x_min)) +
                            '→' + (x_min + (i+1)/window.bins*(x_max-x_min)),
                            averages])
                COORDS.append(coords[-1])
            all_lines.append(coords)

        ctx = get_ctx({})
        x_min, x_max, y_min, y_max = get_bounding_box(COORDS)
        ctx.strokeStyle = '#EEE'
        xx_real, delta, digits = get_labels(x_min, x_max)
        draw_verticals(ctx, xx_real, x_min, x_max, delta, digits)
        xx_real, delta, digits = get_labels(y_min, y_max)
        draw_horizontals(ctx, xx_real, y_min, y_max, delta, digits)
        ctx.strokeStyle = '#000'
        details = []
        for line in all_lines:
            i = 0
            coords = []
            for xx, yy, color, radius, opacity, key, averages in line:
                x_canvas = (i + 0.5) * 1024 / window.bins
                y_canvas = 1024 - 1024 * (yy - y_min) / (y_max - y_min + 1e-9)
                coords.append([x_canvas, y_canvas])
                ctx.globalAlpha = opacity
                ctx.fillStyle = '#' + color
                ctx.beginPath()
                ctx.arc(x_canvas, y_canvas, radius, 0, 2*Math.PI)
                ctx.stroke()
                ctx.fill()
                i += 1
                mouse_in_disc(ctx, details, event_x, event_y, x_canvas, y_canvas, radius, key, averages)
            ctx.beginPath()
            ctx.moveTo(*coords[0])
            for x_canvas, y_canvas in coords[1:]:
                ctx.lineTo(x_canvas, y_canvas)
            ctx.stroke()
        display_details(details)
        return

    sums = {}
    for key, values in stats_for.Items():
        try:
            COORDS.append([window.x(values),
                           window.y(values),
                           get_color(values),
                           window.circle_radius(values),
                           window.opacity(values),
                           key])
        except:
            pass
    x_min, x_max, y_min, y_max = get_bounding_box(COORDS)
    ctx = get_ctx(sums)

    ctx.strokeStyle = '#EEE'
    xx_real, delta, digits = get_labels(x_min, x_max)
    draw_verticals(ctx, xx_real, x_min, x_max, delta, digits)
    xx_real, delta, digits = get_labels(y_min, y_max)
    draw_horizontals(ctx, xx_real, y_min, y_max, delta, digits)

    details = []
    ctx.strokeStyle = '#000'
    for xx, yy, color, radius, opacity, key in COORDS:
        x_canvas =        1024 * (xx - x_min) / (x_max - x_min + 1e-9)
        y_canvas = 1024 - 1024 * (yy - y_min) / (y_max - y_min + 1e-9)
        ctx.globalAlpha = opacity
        ctx.fillStyle = '#' + color
        ctx.beginPath()
        ctx.arc(x_canvas, y_canvas, radius, 0, 2*Math.PI)
        ctx.stroke()
        ctx.fill()
        mouse_in_disc(ctx, details, event_x, event_y, x_canvas, y_canvas,
                      radius, key, stats_for[key])
    display_details(details)

stats_init()
setInterval(stats_update, 100)
