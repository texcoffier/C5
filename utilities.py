#!/usr/bin/python3
"""
Script to put C5 in production on a remote host
And some utilities
"""

import os
import sys
import socket
import ssl

def local_ip():
    """Get the local IP"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]

def get_certificate(server=True):
    """Returns None if no certificate needed"""
    if C5_CERT == 'SS': # Encryption is done by NGINX
        if server:
            cert = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        else:
            cert = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        cert.load_cert_chain(certfile="SSL/localhost.crt", keyfile="SSL/localhost.key")
        return cert
    return None

C5_HOST = os.getenv('C5_HOST', local_ip())           # Production host
C5_ROOT = os.getenv('C5_ROOT', 'root')               # login allowed to sudo
C5_LOGIN = os.getenv('C5_LOGIN', os.getlogin())      # c5 login
C5_HTTP = int(os.getenv('C5_HTTP', '8000'))          # HTTP server port
C5_SOCK = int(os.getenv('C5_SOCK', '4200'))          # WebSocket server port
C5_MAIL = os.getenv('C5_MAIL', f'root@{C5_ROOT}')    # For Let's encrypt certificate
C5_CERT = os.getenv('C5_CERT', 'SS')                 # Encrypt by self or NGINX
C5_URL = os.getenv('C5_URL', f'{C5_HOST}:{C5_HTTP}') # c5 public URL
C5_WEBSOCKET = os.getenv('C5_WEBSOCKET', f'{C5_HOST}:{C5_SOCK}') # c5 public websocket
# CAS redirection as: 'https://cas.univ-lyon1.fr/login?service='
C5_REDIRECT = os.getenv('C5_REDIRECT', '')
# CAS login validation as:  'https://cas.univ-lyon1.fr/cas/validate?service=%s&ticket=%s'
C5_VALIDATE = os.getenv('C5_VALIDATE', '')

def print_state():
    print(f"""Uses environment shell variables :
{'C5_HOST=' + str(C5_HOST):<40}     # Production host (for SSH)
{'C5_ROOT=' + str(C5_ROOT):<40}     # login allowed to sudo
{'C5_LOGIN=' + str(C5_LOGIN):<40}     # c5 login
{'C5_HTTP=' + str(C5_HTTP):<40}     # Port number for HTTP
{'C5_SOCK=' + str(C5_SOCK):<40}     # Port number for WebSocket
{'C5_MAIL=' + str(C5_MAIL):<40}     # Mail address to create Let's Encrypt certificate
{'C5_CERT=' + str(C5_CERT):<40}     # SS: C5/SSL directory, NGINX: NGINX
{'C5_URL=' + str(C5_URL):<40}     # Browser visible address
{'C5_WEBSOCKET=' + str(C5_WEBSOCKET):<40}     # Browser visible address for WebSocket
{'C5_REDIRECT=' + str(C5_REDIRECT):<40} # CAS redirection
{'C5_VALIDATE=' + str(C5_VALIDATE):<40} # CAS get login
""")

def print_help():
    """Print help and default configuration values"""
    print(f"""Arguments may be:
   * os : configure production OS
   * SSL-LE : create SSL Certificate with Let's Encrypt (NGINX does the encrypting)
   * SSL-SS : create a Self Signed certificate (c5 does the encrypting itself)
   * nginx : configure NGINX (needs SSL-LE certificate)
   * c5 : update C5 source (pull)
   * start : servers
   * stop : servers
   * restart : servers
   * open : launch web browser (second argument may be js|python|cpp|remote)
""")
    print_state()
    os.system("ps -fe | grep -e http_server.py -e compile_server.py | grep -v grep")
    sys.exit(1)

ACTIONS = {
    'os': """#C5_ROOT
        sudo sh -c '
            set -e
            apt update
            apt -y install nginx certbot python3-websockets python3-aiohttp npm
            apt -y upgrade
            '
        """,
    'c5': f"""#C5_LOGIN
        set -e
        if [ -d C5 ]
        then
            cd C5
            git pull
        else
            git clone https://github.com/texcoffier/C5.git
            git config pull.ff only
            cd C5
        fi
        """,
    'cp': f"""
        scp $(git ls-files) {C5_LOGIN}@{C5_HOST}:C5
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
        }}
    location ~ {{
    proxy_pass http://127.0.0.1:{C5_HTTP};
    }}
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
                exit 0
                fi
            certbot certonly --standalone -d {C5_URL} -m {C5_MAIL}
            '
        """,
    'SSL-SS': f"""#C5_LOGIN
        set -e
        cd C5
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
DNS.7 = {C5_URL}
' >domains.ext
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
    'start': """#C5_LOGIN
        set -e
        cd C5
        ./http_server.py >>http_server.log 2>&1 &
        ./compile_server.py >>compile_server.log 2>&1 &
        sleep 0.5
        tail -1 http_server.log
        tail -1 compile_server.log
        """,
    'stop': """#C5_LOGIN
        pkill -f 'http_server.py|compile_server.py'
        """,
    'open': f"""
        xdg-open https://{C5_URL}/=course_{sys.argv[2] if len(sys.argv) >= 3 else 'js'}.js
        """
}
ACTIONS['restart'] = ACTIONS['stop'] + ACTIONS['start']

def main():
    """MAIN"""
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print_help()
    action = sys.argv[1]
    if action != 'open':
        print(f"{' '.join(sys.argv)}")
        print_state()
    action = f"""
export C5_HOST={C5_HOST}
export C5_ROOT={C5_ROOT}
export C5_LOGIN={C5_LOGIN}
export C5_HTTP={C5_HTTP}
export C5_URL={C5_URL}
export C5_SOCK={C5_SOCK}
export C5_MAIL={C5_MAIL}
export C5_CERT={C5_CERT}
export C5_WEBSOCKET='{C5_WEBSOCKET}'
export C5_REDIRECT='{C5_REDIRECT}'
export C5_VALIDATE='{C5_VALIDATE}'
""" + ACTIONS[action]
    assert '"' not in action
    if '#C5_ROOT' in action:
        action = f'ssh {C5_ROOT}@{C5_HOST} "' + action + '"'
    elif '#C5_LOGIN' in action:
        action = f'ssh {C5_LOGIN}@{C5_HOST} "' + action + '"'
    sys.exit(os.system(action))

if __name__ == "__main__":
    main()