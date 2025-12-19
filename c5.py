#!/usr/bin/python3

import os
import sys
import json
import time
import socket
import html
import options

def init_globals(global_dict):
    """Initialise global variables of this module from shell variables"""
    for name, _comment, default in CONFIGURATIONS:
        if not isinstance(default, (int, str)):
            default = default()
        value = os.getenv(name, default)
        if isinstance(default, int):
            value = int(value)
        global_dict[name] = value

def local_ip() -> str:
    """Get the local IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'

# To please pylint:
C5_HOST = C5_IP = C5_LOGIN = C5_HTTP = C5_SOCK = C5_MAIL = C5_CERT = None
C5_LOCAL = C5_URL = C5_DIR = C5_WEBSOCKET = C5_REDIRECT = C5_VALIDATE = C5_LDAP = None
C5_LDAP_LOGIN = C5_LDAP_PASSWORD = C5_LDAP_BASE = C5_LDAP_ENCODING = C5_CUSTOMIZE = None
C5_ROOT = ''

CONFIGURATIONS = (
    ('C5_HOST'         ,'Production host (for SSH)'            , local_ip()),
    ('C5_IP'           ,'For Socket IP binding'                , local_ip()),
    ('C5_ROOT'         ,'login allowed to sudo'                , 'root'),
    ('C5_LOGIN'        ,'user C5 login'                        , os.getlogin()),
    ('C5_HTTP'         ,'Port number for HTTP'                 , 8000),
    ('C5_SOCK'         ,'Port number for WebSocket'            , 4200),
    ('C5_MAIL'         ,"To create Let's Encrypt certificate"  , lambda: 'root@' + C5_ROOT),
    ('C5_CERT'         ,"SS: C5/SSL directory, NGINX: NGINX"   , 'SS'),
    ('C5_LOCAL'        ,'Run on local host'                    , 1),
    ('C5_URL'          ,'Browser visible address'              , ''),
    ('C5_DIR'          ,'C5 install directory name'            , 'C5'),
    ('C5_WEBSOCKET'    ,'Browser visible address for WebSocket', lambda: f'{C5_HOST}:{C5_SOCK}'),
    ('C5_REDIRECT'     ,'CAS redirection'                      , ''), # https://cas.univ-lyon1.fr/login?service=
    ('C5_VALIDATE'     ,'CAS get login'                        , ''), # https://cas.univ-lyon1.fr/cas/validate?service=%s&ticket=%s
    ('C5_LDAP'         ,'LDAP URL'                             , ''),
    ('C5_LDAP_LOGIN'   ,'LDAP reader login'                    , ''),
    ('C5_LDAP_PASSWORD','LDAP reader password'                 , ''),
    ('C5_LDAP_BASE'    ,'LDAP user search base'                , ''),
    ('C5_LDAP_ENCODING','LDAP character encoding'              , 'utf-8'),
    ('C5_COMPILE_UID'  ,'Starts of UID for compiling'          , 3000),
    ('C5_CUSTOMIZE'    ,'File with «common.py» overloading'    , 'local_my.py'),
)

init_globals(globals())

def var(name, comment, export='export '):
    """Display a shell affectation with the current variable value"""
    val = globals()[name]
    escaped = str(val).replace("'", "'\"'\"'")
    affectation = f"{export}{name}='{escaped}'"
    return affectation.ljust(50) + " # " + comment


def print_state() -> None:
    """Print the current configuration"""
    print("Uses environment shell variables :")
    for name, comment, _default in CONFIGURATIONS:
        print(var(name, comment, export=''))

def create_start_script():
    """Create the start script on the distant host"""
    with open('xxx-start-c5', 'w', encoding='utf-8') as file:
        file.write('#!/bin/sh\n')
        file.write('# Starts C5 with configuration\n')
        file.write(''.join(var(name, comment).replace("LOCAL='0'", "LOCAL='1'") + '\n'
                           for name, comment, _default in CONFIGURATIONS))
        file.write('[ "" = "$1" ] && ARG=$1 || ARG=start\n')
        file.write('./c5.py $ARG\n')
    os.chmod('xxx-start-c5', 0o755)

def start_server(name):
    """Shell script to start the server"""
    date = time.strftime('%Y%m%d')
    return f"""
        python3 {name}.py >>LOGS/{date}-{name} 2>&1 &
        echo \\$! >LOGS/{name}.pid
        rm -f LOGS/{name} 2>/dev/null || true
        ln -s {date}-{name} LOGS/{name}
        find LOGS -name '????????-*[!z]' -mtime +1 -exec gzip --verbose -9 {{}} +
        find TICKETS/ -mtime +60 -exec rm {{}} +
        """

def print_help() -> None:
    """Print help and default configuration values"""
    print("""Arguments may be:
   * os : configure production OS
   * SSL-LE : create SSL Certificate with Let's Encrypt (NGINX does the encrypting)
              or renew it if it exists.
   * SSL-SS : create a Self Signed certificate (c5 does the encrypting itself)
   * nginx : configure NGINX (needs SSL-LE certificate)
   * c5 : update C5 source (pull)
   * pipenv : create the Python environment
   * launcher : create 'launcher' (need to be root)
   * start : servers
   * stop : servers
   * restart : servers
   * restart_compile_server : only compile_server.py
   * compile : create JS
   * create_start_script : create 'xxx-start-c5' on server
   * open : launch web browser (second argument may be js|python|cpp|remote)
   * cp : copy local files to production ones
   * diff : compare local files to production ones
   * getall : copy production course (but not logs) locally
   * cleanup_session_cf : removes any modification history from 'session.cf' files
                          to do between semesters to speedup C5 startup time.
   * create_stats : compute stats file per session
""")
    print_state()
    os.system("ps -fe | grep -e http_server.py -e compile_server.py -e dns_server.py -e infos_server.py | grep -v grep")
    print('for I in http compile infos dns; do pkill -f "$I"_server.py ; done')
    sys.exit(1)

ACTIONS = {
    'os': """#C5_ROOT
        sudo sh -c '
            set -e
            apt update
            apt -y install astyle nginx certbot python3-venv python3-wheel python3-dev libldap-dev libsasl2-dev python3-psutil python3-certbot-nginx npm racket zip curl rsync coq swi-prolog
            apt -y upgrade
            # set-timezone Europe/Paris
            '
        """,
    'launcher': f"""#C5_ROOT
        sudo sh -c '
            set -e
            cd ~{C5_LOGIN}/{C5_DIR}
            make launcher
            '
        """,
    'pipenv': f"""#C5_LOGIN
        cd {C5_DIR}
        if ! python3 -m venv PIPENV
            then
                echo =================FAIL=======================
                exit 1
            fi
        . PIPENV/bin/activate
        pip install aiohttp websockets python-ldap
    """,
    'c5': f"""#C5_LOGIN
        set -e
        if [ -d {C5_DIR} ]
        then
            cd {C5_DIR}
            git pull
        else
            git clone https://github.com/texcoffier/C5.git
            git config pull.ff only
            cd {C5_DIR}
        fi
        """,
    'cp': f"""
        tar -cf - $(git ls-files | grep -v -e DOCUMENTATION -e BUILDINGS) |
        ssh {C5_LOGIN}@{C5_HOST} 'cd {C5_DIR} && tar -xvf -'
        """,
    'diff': f"""
        mkdir DIFF
        git ls-files | grep -v -e DOCUMENTATION -e BUILDINGS >xxx.tocopy
        rsync --files-from=xxx.tocopy '{C5_LOGIN}@{C5_HOST}:{C5_DIR}' DIFF
        for I in $(cat xxx.tocopy)
        do
        diff -u $I DIFF/$I
        done
        rm -rf DIFF
        """,
    'getall': f"""
        rsync --archive --exclude '*/*/**' --exclude '*~' --prune-empty-dirs --verbose '{C5_LOGIN}@{C5_HOST}:{C5_DIR}/COMPILE_*' .
        rsync --archive --verbose '{C5_LOGIN}@{C5_HOST}:{C5_DIR}/BUILDINGS' .
        """,
    'nginx': f"""#C5_ROOT
        sudo sh -c '
            cat >/etc/nginx/sites-available/default <<%
server {{
    listen 443 ssl;
    server_name {C5_URL};
    ssl_certificate /etc/letsencrypt/live/{C5_URL}/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/{C5_URL}/privkey.pem; # managed by Certbot
    location /WebSocket/ {{
        proxy_pass http://127.0.0.1:{C5_SOCK};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\\\\$http_upgrade;
        proxy_set_header Connection Upgrade;
        proxy_set_header Host \\\\\\$host;
        proxy_set_header X-Forwarded-For \\\\\\$proxy_add_x_forwarded_for;
        }}
    location ~ {{
    proxy_pass http://127.0.0.1:{C5_HTTP};
    }}
  }}
server {{
    listen 80;
    server_name {C5_URL};
    rewrite  ^/(.*)$  https://{C5_URL}/$1  permanent;
}}
%
            systemctl restart nginx
'
    """,
    'SSL-LE': f"""#C5_ROOT
        sudo sh -c '
            set -e
            if [ -d /etc/letsencrypt/live/{C5_URL} ]
                then
                certbot renew --nginx
                exit 0
                fi
            certbot certonly --standalone -d {C5_URL} -m {C5_MAIL}
            '
        """,
    'SSL-SS': f"""#C5_LOGIN
        set -e
        cd {C5_DIR}
        if [ -d SSL ]
            then
            exit 0
            fi
        mkdir SSL
        cd SSL
        openssl req -x509 -nodes -new -sha256 -days 1024 -newkey rsa:2048 -keyout RootCA.key -out RootCA.pem -subj '/C=US/CN=_______C5_______'
        openssl x509 -outform pem -in RootCA.pem -out RootCA.crt
        echo '
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost:{C5_SOCK}
DNS.2 = 127.0.0.1:{C5_SOCK}
DNS.3 = localhost:{C5_HTTP}
DNS.4 = 127.0.0.1:{C5_HTTP}
DNS.5 = {local_ip()}:{C5_HTTP}
DNS.6 = {local_ip()}:{C5_SOCK}
DNS.7 = {C5_HOST}:{C5_SOCK}
DNS.8 = {C5_URL}
' >domains.ext
        cat domains.ext
        openssl req -new -nodes -newkey rsa:2048 -keyout localhost.key -out localhost.csr -subj '/C=US/ST=YourState/L=YourCity/O=Example-Certificates/CN=localhost.local'
        openssl x509 -req -sha256 -days 1024 -in localhost.csr -CA RootCA.pem -CAkey RootCA.key -CAcreateserial -extfile domains.ext -out localhost.crt

        echo '
********************************************************************
********************************************************************
You must indicate to the browser to add a security exception
********************************************************************
********************************************************************
With Firefox:
    * about:preferences
    * Search «certificate»
    * Click on the button «View certificates»
    * Goto on tab «Servers»
    * Click on «Add exception»
    * Add : «https://{C5_URL}»
    * Add : «https://{C5_WEBSOCKET}»
    * Confirm
********************************************************************
        '
    """,
    'restart_compile_server': fr"""#C5_LOGIN
        set -e
        echo RESTART compile_server
        cd {C5_DIR} 2>/dev/null || true
        pkill --oldest -u \$(id -u) -f compile_server.py || true
        sleep 1
        {start_server("compile_server")}
        """,
    'restart_http_server': fr"""#C5_LOGIN
        set -e
        echo RESTART http_server
        cd {C5_DIR} 2>/dev/null || true
        pkill --oldest -f http_server.py || true
        sleep 1
        {start_server("http_server")}
        """,
    'start': fr"""#C5_LOGIN
        set -e
        echo START SERVERS {C5_DIR}
        cd {C5_DIR} 2>/dev/null || true
        chmod 700 . # No access for students
        mkdir TICKETS LOGS 2>/dev/null || true
        make prepare
        if [ '' != '{C5_URL}' ]
        then
            {start_server("http_server")}
            {start_server("compile_server")}
            sleep 2
            echo ============================== Last 4 lines of http_server logs:
            tail -5 LOGS/http_server
            echo ============================== Last 3 lines of compile_server logs:
            tail -3 LOGS/compile_server
        fi
        """,
    'stop': r"""#C5_LOGIN
        echo STOP SERVERS
        for I in http_server compile_server infos_server dns_server
        do
            pkill --uid \$(id -u) --oldest -f ^python3.\$I
        done
        sleep 0.1
        for I in http_server compile_server infos_server dns_server
        do
            pkill -1 --uid \$(id -u) --oldest -f ^python3.\$I
        done
        """,
    'open': f"""
        xdg-open https://{C5_URL}/{'=' + sys.argv[2] if len(sys.argv) >= 3 else ''}
        """,
    'load': "./load_testing.py",
    'compile': fr"""#C5_LOGIN
        echo COMPILE
        cd {C5_DIR} 2>/dev/null || true
        mkdir TICKETS 2>/dev/null || true
        make prepare
        """,
    'create_start_script': fr"""#C5_LOGIN
        echo CREATES START SCRIPT 'xxx-start-c5'
        cd {C5_DIR}
        ./c5.py __create_start_script__
        """,
    'cleanup_session_cf': fr"""#C5_LOGIN
        echo 'CLEAN UP SESSION CF (remove history)'
        cd {C5_DIR}
        ./c5.py __cleanup_session_cf__
        """,
    'create_stats': fr"""#C5_LOGIN
        echo CREATES STATS
        cd {C5_DIR}
        ./c5.py __create_stats__
        """,
}
ACTIONS['restart'] = ACTIONS['compile'] + '\n' + ACTIONS['stop'] + 'sleep 2\n' + ACTIONS['start']
ACTIONS['c5'] = ACTIONS['c5'] + '\n' + ACTIONS['pipenv']

def main() -> None:
    """MAIN"""
    os.system(f"make xxx_local.py >&2")
    dumps = json.dumps
    json.dumps = lambda x: dumps(x).replace('<', '\\074')

    if '__create_start_script__' in sys.argv:
        create_start_script()
        return
    if '__cleanup_session_cf__' in sys.argv:
        for course in CourseConfig.load_all_configs():
            try:
                os.rename(course.file_cf, course.file_cf + '~')
                course.record_config()
                CourseConfig(course.dir_session)
                print('CLEANED ', course.file_cf,
                    os.path.getsize(course.file_cf + '~') // 1024, 'KB →',
                    os.path.getsize(course.file_cf) // 1024, 'KB')
            except: # pylint: disable=bare-except
                # Revert changes
                print('BUG ', course.file_cf)
                os.rename(course.file_cf + '~', course.file_cf)
        return
    if '__create_stats__' in sys.argv:
        import create_stats
        create_stats.compile_stats(CourseConfig.load_all_configs())
        return

    if 'options.html' in sys.argv:
        print('<table>')
        for line in options.DEFAULT_COURSE_OPTIONS:
            if len(line) == 3:
                if isinstance(line[1], str):
                    value = '<tt>' + html.escape(repr(line[1])) + '</tt>'
                elif isinstance(line[1], list):
                    value = '<pre>[\n' + ''.join(f'  {html.escape(repr(i))},\n'
                                            for i in line[1]) + ']</pre>'
                elif isinstance(line[1], dict):
                    value = '<pre>{\n' + ''.join(f'  {repr(key)}: {html.escape(repr(val))},\n'
                                            for key, val in line[1].items()) + '}</pre>'
                else:
                    value = repr(line[1])
                print(f'<tr><td>{line[0]}<td>{value}<td>{line[2]}</tr>')
            else:
                print(f'<tr><th style="background: #FFF" colspan="3">{html.escape(line)}</tr>')
        print('</table>')
        return
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print_help()
    action = sys.argv[1]
    if action != 'open':
        print(f"{' '.join(sys.argv)}")
        print_state()
    action = (''.join(var(name, comment) + '\n'
                        for name, comment, _default in CONFIGURATIONS)
              + f'[ -d {C5_DIR}/PIPENV ] && . {C5_DIR}/PIPENV/bin/activate\n'
              + ACTIONS[action])

    assert '"' not in action
    if '#C5_ROOT' in action:
        if C5_LOCAL:
            action = 'cd ..; sh -c "' + action + '"'
        else:
            action = f'ssh {C5_ROOT}@{C5_HOST} "' + action + '"'
    elif '#C5_LOGIN' in action:
        action = r'''
. /etc/profile
[ -e /etc/bash.bashrc ] && bash -c '
    PS1=TORUNBASHRC
    . /etc/bash.bashrc
    echo export http_proxy=\$http_proxy >~/xxx.proxy
    echo export https_proxy=\$https_proxy >>~/xxx.proxy
    ' && pwd && hostname && . \$HOME/xxx.proxy
''' + action
        if C5_LOCAL:
            action = 'cd ..; sh -c "' + action + '"'
        else:
            action = f'ssh {C5_LOGIN}@{C5_HOST} "' + action + '"'
    # print(action)
    sys.exit(os.system(action))

if __name__ == '__main__':
    main()
