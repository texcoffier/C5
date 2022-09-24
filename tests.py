#!/usr/bin/python3
"""
Regression Test for C5
"""
# pylint: disable=line-too-long

import os
import sys
import time
import json
import subprocess
import traceback
import contextlib
import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
import utilities

def retry(test, required=True, nbr=30):
    """Retry if test failure"""
    for _ in range(nbr):
        try:
            error = test()
            if not error:
                return
        except selenium.common.exceptions.StaleElementReferenceException:
            # Test failure because the page just update
            pass
        time.sleep(0.05)
    if required:
        raise ValueError(error)
class Test:
    """Contruct an expression to test a string"""
    def run(self, value):
        """Returns True if the value match the expression"""
        raise ValueError(f'Abstract run on {self}')
    def __invert__(self):
        return Not(self)
    def __or__(self, other):
        return Or(self, other)
    def __and__(self, other):
        return And(self, other)
class Contains(Test):
    """text is expected inside"""
    def __init__(self, text):
        self.text = text
    def run(self, value):
        return self.text in value
    def __repr__(self):
        return f'Contains({repr(self.text)})'
class Equal(Contains):
    """The value must be equal"""
    def run(self, value):
        return self.text == value
    def __repr__(self):
        return f'Equal({repr(self.text)})'
class Not(Test):
    """Boolean operator"""
    def __init__(self, test):
        self.test = test
    def run(self, value):
        return not self.test.run(value)
    def __repr__(self):
        return f'~{repr(self.test)}'
class Or(Test):
    """Boolean operator"""
    def __init__(self, test1, test2):
        self.test1 = test1
        self.test2 = test2
    def run(self, value):
        return self.test1.run(value) or self.test2.run(value)
    def __repr__(self):
        return f'Or({repr(self.test1)}, {repr(self.test2)})'
class And(Or):
    """Boolean operator"""
    def run(self, value):
        return self.test1.run(value) and self.test2.run(value)
    def __repr__(self):
        return f'And({repr(self.test1)}, {repr(self.test2)})'

def log(text):
    """Add one line par full test in the log file"""
    with open("tests.log", "a") as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text}\n")

class Tests: # pylint: disable=too-many-public-methods
    """Test for one browser"""
    ticket = None
    def __init__(self, driver):
        self.driver = driver
        for course_name in ('COMPILE_REMOTE/test', 'COMPILE_JS/introduction'):
            course = utilities.CourseConfig(course_name)
            course.set_parameter('start', '2000-01-01 00:00:01')
            course.set_parameter('stop', '2100-01-01 00:00:01')
            course.set_parameter('checkpoint', '0')
            course.record()

        start = time.time()
        self.wait_start()
        for test in (
                self.test_popup,
                self.test_f9,
                self.test_inputs,
                self.test_auto_compile,
                self.test_reset_button,
                self.test_save_button,
                self.test_copy_paste_allowed,
                self.test_question_index,
                self.test_admin_home,
                self.test_date_change,
                self.test_master_change,
                self.test_ticket_ttl,
                self.test_editor,
                ):
            print('*'*99)
            print(f'{driver.name.upper()} «{test.__func__.__name__}» {test.__doc__.strip()}')
            print('*'*99)
            test()
        self.driver.close()
        print(f'OK {driver.name.upper()} ({time.time()-start:.1f} secs)')
        log(f'OK {driver.name.upper()} ({time.time()-start:.1f} secs)')

    @staticmethod
    def update_config(action):
        """Update the configuration by running action."""
        with open('c5.cf', 'r') as file:
            config = json.loads(file.read())
        action(config)
        with open('c5.cf', 'w') as file:
            file.write(json.dumps(config))
    def make_me_admin(self):
        """Make admin the current login"""
        self.update_config(lambda config: config['masters'].append('Anon#' + self.ticket))
        self.goto('config/reload')
        self.check_alert(required=False, nbr=2)
    def clean_up_admin(self):
        """Remove all anonymous logins from admin list"""
        def clean(config):
            config['masters'] = [
                login
                for login in config['masters']
                if '#' not in login and not login.isdigit() and not login == 'john.doe'
                ]
            config['ticket_ttl'] = 86400
        self.update_config(clean)
    @contextlib.contextmanager
    def admin_rights(self):
        """Take temporarely the admin rights"""
        try:
            self.make_me_admin()
            yield
        finally:
            self.clean_up_admin()
    def select_all(self, path='.editor'):
        """Select the full editor content"""
        self.move_cursor(path, 10, 10)
        self.control('a')
        self.control('c')
    def control(self, char):
        """Send a control character"""
        action = selenium.webdriver.ActionChains(self.driver)
        action.key_down(Keys.CONTROL)
        action.key_down(char)
        action.key_up(char)
        action.key_up(Keys.CONTROL)
        action.perform()
    def goto(self, url):
        """Load page"""
        print('\tGOTO', url)
        self.driver.get(f"https://127.0.0.1:4201/{url}?ticket={self.ticket}")
    def wait_start(self):
        """Wait the server start"""
        def check():
            try:
                self.goto('')
                self.ticket = self.driver.current_url.split('?ticket=')[1]
                return None
            except selenium.common.exceptions.WebDriverException:
                return "Server connection is impossible"
        retry(check)
    def check(self, path, checks={}, expected=1): # pylint: disable=dangerous-default-value
        """Check"""
        print('\tCHECK', path, checks, expected, end=' ')
        def get_errors():
            print('*', end='', flush=True)
            elements = self.driver.find_elements_by_css_selector(path)
            if len(elements) != expected:
                return f'Expected {expected} elements with the path «{path}»'
            if len(elements) == 1:
                element = elements[0]
                self.move_to_element(element)
                for attr, check in checks.items():
                    if not check.run(element.get_attribute(attr)):
                        return f'«{path}.{attr}» = «{element.get_attribute(attr)}» {check}'
                get_errors.element = element
            return None
        get_errors.element = None
        retry(get_errors)
        print()
        return get_errors.element
    def check_alert(self, contains='', accept=True, required=True, nbr=20):
        """Check if an alert is on screen and accept or cancel it"""
        def check():
            try:
                print(f'\tALERT Contains=«{contains}» Accept=«{accept}»')
                alert = Alert(self.driver)
                if contains in alert.text:
                    if accept:
                        alert.accept()
                    else:
                        alert.dismiss()
                    return None
                return f'The alert does not contains «{contains}» but «{alert.text}'
            except selenium.common.exceptions.NoAlertPresentException:
                return 'No alert on screen'
        retry(check, required, nbr=nbr)
    def load_page(self, url):
        """Load page and clear popup"""
        self.goto(url)
        self.check_alert(required=False, nbr=10)
        self.check('.question H2').click() # Hide popup
    def move_to_element(self, element):
        """Make the element visible on screen in order to click on it"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)

    def move_cursor(self, path, relative_x=0, relative_y=0):
        """Set the cursor at the position and click"""
        element = self.driver.find_elements_by_css_selector(path)[0]
        self.move_to_element(element)
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element_with_offset(element, relative_x, relative_y)
        action.click()
        action.perform()
        return element
    def test_popup(self):
        """Page display"""
        self.goto('=REMOTE=test')
        self.check('.popup', {'innerHTML': Contains('ATTENTION')})
        action = selenium.webdriver.ActionChains(self.driver)
        action.key_down('§')
        action.key_up('§')
        action.perform()
        self.check('.popup', expected=0)
        self.check('.editor', {'innerHTML':  ~Contains('§')})
        self.check('.compiler', {'innerText': Contains('On attend') & Contains('Bravo')})
        self.check('.executor', {'innerHTML': Contains('Saisir')})
        self.check('.question', {'innerHTML': Contains('Plus de questions')})
        self.check('.tester', {'innerHTML': Contains('Les buts que')})
        self.check('.executor INPUT')
    def test_f9(self):
        """Check if F9 launch compilation"""
        self.load_page('=REMOTE=test')
        self.check('.compiler', {'innerText': Contains('On attend') & Contains('Bravo')})
        self.move_cursor('.editor')
        self.check('.editor').send_keys('\n')
        time.sleep(0.2)
        self.check('.editor').send_keys(Keys.F9)
        self.check('.compiler', {'innerText': ~Contains('On attend') & Contains('Bravo')})
    def test_inputs(self):
        """Tests inputs"""
        self.load_page('=REMOTE=test')
        self.check('.compiler', {'innerText': Contains('On attend') & Contains('Bravo')})
        self.check('.executor INPUT').send_keys('8')
        self.check('.executor INPUT').send_keys(Keys.ENTER)
        self.check('.executor INPUT:nth-child(3)', {'value': Equal('8')})
        self.check('.executor', {'innerHTML': Contains('symbole')})

        # Modify source code, INPUT is auto filled.
        self.move_cursor('.editor')
        recompile_done = False
        for _ in range(3):
            # Not a normal failure, a bug must be somewhere.
            # Rarely F9 is not working, so retry it
            self.check('.editor').send_keys('\n\n\n')
            self.check('.editor').send_keys(Keys.F9)
            try:
                self.check('.compiler', {'innerText': ~Contains('On attend') & Contains('Bravo')})
                recompile_done = True
                break
            except ValueError:
                pass
        if not recompile_done:
            raise ValueError('??????????????')
        self.check('.executor INPUT:nth-child(3)', {'value': Equal('8')})
        self.check('.executor', {'innerHTML': Contains('symbole')})

        # Fill second input
        self.check('.executor INPUT:nth-child(5)').send_keys('*')
        self.check('.executor INPUT:nth-child(5)').send_keys(Keys.ENTER)
        self.check('.executor INPUT:nth-child(5)', {'value': Equal('*')})
        self.check('.executor', {'innerHTML': Contains('·············***************············')})

        # Change first input
        self.check('.executor INPUT:nth-child(3)').send_keys(Keys.BACKSPACE)
        self.check('.executor INPUT:nth-child(3)').send_keys('1')
        self.check('.executor INPUT:nth-child(3)').send_keys(Keys.ENTER)
        self.check('.executor', {'innerHTML': Contains('····················*···················')})
    def test_auto_compile(self):
        """Tests automatic recompilation"""
        self.load_page('=JS=introduction')
        self.move_cursor('.editor')
        self.check('.editor').send_keys('§')
        self.check('.compiler', {'innerHTML': Contains('illegal') | Contains('Invalid')})
        self.check('.editor').send_keys(Keys.BACKSPACE)
        self.check('.compiler', {'innerHTML': Contains('sans')})

        self.check('.editor').send_keys(Keys.F9)
        self.check('.editor').send_keys('print("Hello")')
        time.sleep(0.3) # Wait a recompile that must not happen
        self.check('.executor', {'innerHTML': ~Contains('Hello')})
        self.check('.editor').send_keys(Keys.F9)
        self.check('.executor', {'innerHTML': Contains('Hello')})

        # Disable compilation by clicking
        self.check('.compiler LABEL').click()
        self.move_cursor('.editor')
        self.check('.editor').send_keys('§')
        time.sleep(0.3) # Wait a recompile that must not happen
        self.check('.compiler', {'innerHTML': Contains('sans')})
        self.check('.compiler LABEL').click()
        self.check('.compiler', {'innerHTML': Contains('illegal') | Contains('Invalid')})
    def test_reset_button(self):
        """Test reset button"""
        self.load_page('=JS=introduction')
        self.move_cursor('.editor')
        self.check('.editor').send_keys('§')
        self.check('.editor', {'innerHTML': Contains('§')})
        self.check('.reset_button').click()
        self.check_alert(accept=False)
        self.check('.editor', {'innerHTML': Contains('§')})
        self.check('.reset_button').click()
        self.check_alert(accept=True, contains="départ")
        self.check('.editor', {'innerHTML': ~Contains('§')})
    def test_save_button(self):
        """Test save button"""
        self.load_page('=JS=introduction')
        self.move_cursor('.editor')
        self.check('.editor', {'innerHTML': ~Contains('§')})
        self.check('.editor').send_keys('§')
        self.check('.editor', {'innerHTML': Contains('§')})
        self.check('.save_button').click()
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': Contains('§')})
        time.sleep(0.1) # For Firefox
        self.move_cursor('.editor')
        self.check('.editor').send_keys('§')
        self.check('.editor', {'innerHTML': Contains('§§')})
        self.control('s')
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': Contains('§§')})
        self.move_cursor('.editor')
        self.check('.editor').send_keys(Keys.DELETE)
        self.check('.editor').send_keys(Keys.DELETE)
        self.check('.save_button').click()
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': ~Contains('§')})
    def test_copy_paste_allowed(self):
        """Test a working copy paste"""
        self.load_page('=JS=introduction')
        self.select_all()
        self.control('v')
        self.control('v')
        self.check('.executor', {'innerText': Contains('court\nJe')})
    def test_question_index(self):
        """Test question index"""
        self.load_page('=JS=introduction')
        # Try to click on the next question
        self.check('.questions > DIV:nth-child(4)').click()
        self.check('.editor', {'innerText': Contains('court') & ~Contains('long')})

        self.check('.questions > DIV:nth-child(3)', {'innerText': Contains('1'), 'className': Equal('current possible')})
        self.check('.questions > DIV:nth-child(4)', {'innerText': Contains('2'), 'className': Equal('')})
        self.check('.questions > DIV:nth-child(5)', {'innerText': Contains('3'), 'className': Equal('')})
        self.select_all()

        try:
            self.check('.editor').send_keys("print('Je suis un texte super long')")
            self.check_alert(contains=' !')
            self.check('.questions > DIV:nth-child(3)', {'innerText': Contains('1'), 'className': Equal('good')})
            self.check('.questions > DIV:nth-child(4)', {'innerText': Contains('2'), 'className': Equal('current possible')})
            self.check('.questions > DIV:nth-child(5)', {'innerText': Contains('3'), 'className': Equal('')})
            self.check('.question', {'innerText': Contains('la_chose_a_afficher')})

            # Returns to the first question
            self.check('.questions > DIV:nth-child(3)').click()
            self.check('.editor', {'innerText': Contains('long')})
            self.check('.questions > DIV:nth-child(3)', {'innerText': Contains('1'), 'className': Equal('current good')})
            self.check('.questions > DIV:nth-child(4)', {'innerText': Contains('2'), 'className': Equal('possible')})
            self.check('.questions > DIV:nth-child(5)', {'innerText': Contains('3'), 'className': Equal('')})
        finally:
            time.sleep(0.5) # Wait save button animation end
            self.check('.reset_button').click() # Returns to the original text
            self.check_alert(accept=True)
            self.check('.save_button').click()

    def test_admin_home(self):
        """Test the admin page link"""
        self.load_page('=JS=introduction')
        self.check('.index > A').click()
        self.check_alert(required=False, nbr=10)
        self.check('H1', {'innerText': Equal(utilities.CONFIG.config['messages']['not_admin'])})
        with self.admin_rights():
            self.load_page('=JS=introduction')
            self.check('.index > A').click()
            self.check_alert(required=False, nbr=2)
            self.check('H1', {'innerText': Equal('C5 Administration')})
    def test_date_change(self):
        """Test home page course date change"""
        def set_date(path, date, expect):
            self.select_all(path)
            old_date = self.check(path).get_attribute('value')
            self.check(path).send_keys(
                date + ('1' if old_date[-1] == '0' else '0'))
            self.check(path).send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains(expect)})

        with self.admin_rights():
            self.goto('adm/home')
            set_date('.JS_introduction INPUT.start_date',
                     "2000-01-01 00:00:0", 'Start date updated')
            set_date('.JS_introduction INPUT.stop_date',
                     "2100-01-01 00:00:0", 'Stop date updated')
            self.check('TR.JS_introduction', {'className': Contains('running')})
            self.check('.JS_introduction BUTTON.stop_date').click()
            self.check('TR.JS_introduction', {'className': Contains('running_tt')})
            self.check('.JS_introduction BUTTON.start_date').click()
            self.check('TR.JS_introduction', {'className': Contains('running')})
            set_date('.JS_introduction INPUT.stop_date',
                     "2001-01-01 00:00:0", 'Stop date updated')
            self.check('TR.JS_introduction', {'className': Contains('done')})
            self.check('.JS_introduction BUTTON.start_date').click()
            self.check('TR.JS_introduction', {'className': Contains('running')})
    def test_master_change(self):
        """Test add and remove master"""
        with self.admin_rights():
            self.goto('adm/home')
            self.check('.add_master').send_keys('john.doe')
            self.check('.add_master').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains('Master «john.doe» added')})
            self.check("BUTTON.del_master_john_doe").click()
            self.check('#more', {'innerText': Contains('Master «john.doe» removed')})
    def test_ticket_ttl(self):
        """Test TTL change"""
        to_delete = "TICKETS/TO_DELETE"
        to_keep = "TICKETS/TO_KEEP"
        ttl = 123456
        with open(to_delete, "w") as file:
            file.write(f"('1.1.1.1', 'Browser', 'john.doe', {time.time() - ttl - 60})")
        with open(to_keep, "w") as file:
            file.write(f"('1.1.1.1', 'Browser', 'john.doe', {time.time() - ttl + 60})")

        with self.admin_rights():
            self.goto('adm/home')
            self.select_all('.ticket_ttl')
            self.check('.ticket_ttl').send_keys('X')
            self.check('.ticket_ttl').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains('Invalid')})
            self.select_all('.ticket_ttl')
            self.check('.ticket_ttl').send_keys(str(ttl))
            self.check('.ticket_ttl').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains(f'to {ttl} seconds')})
            self.check('.remove_olds').click()
            self.check('#more', {'innerText': Contains('tickets deleted')})
            assert not os.path.exists(to_delete)
            os.unlink(to_keep)
    def test_editor(self):
        """Test editor line insert"""
        self.load_page('=JS=introduction')
        self.check('.index STYLE + DIV').click() # Returns to the first question
        self.check('.reset_button').click() # Returns to the original text
        self.check_alert(accept=True)

        self.move_cursor('.editor').send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains('\n\n<span class="hljs-comment">// Lisez')})
        self.control('z')
        self.check('.overlay', {'innerHTML': Contains('\n<span class="hljs-comment">// Lisez')})
        self.check('.editor').send_keys(Keys.ARROW_DOWN)
        self.check('.editor').send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains('\n\n<span class="hljs-comment">// Lisez')})
        self.control('z')
        self.check('.editor').send_keys(Keys.ARROW_RIGHT)
        self.check('.editor').send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains('\n/\n/ <span class="hljs-title class_">Lisez')})
        self.control('z')
        self.check('.editor').send_keys(Keys.END)
        self.check('.editor').send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains('\n<span class="hljs-comment">// Lisez la consigne indiquée à gauche.</span>\n\n')})
        self.control('z')
        self.control(Keys.END)
        self.check('.editor').send_keys('/')
        self.check('.editor').send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains(');\n/')})
        self.check('.editor').send_keys('/')
        self.check('.overlay', {'innerHTML': Contains(');\n/\n/')})

IN_DOCKER = not os.getenv('DISPLAY')

os.system('./127 start')
PORT = 3
while os.path.exists(f'/tmp/.X{PORT}.lock'):
    PORT += 1

PORT = f':{PORT}'
if 'hidden' in sys.argv:
    X11 = ['Xvfb', PORT, '-noreset', '-screen', '0', '1024x768x24']
else:
    X11 = ['Xnest', PORT, '-noreset', '-geometry', '1024x768']
try:
    XNEST = subprocess.Popen(
        X11, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    print(X11)
    os.environ['DISPLAY'] = PORT
except FileNotFoundError:
    print(f"«{X11}» not found: run directly on your screen")
    XNEST = None

try:
    EXIT_CODE = 1
    while True:
        if not IN_DOCKER and 'FF' not in sys.argv:
            OPTIONS = selenium.webdriver.ChromeOptions()
            OPTIONS.add_argument('ignore-certificate-errors')
            Tests(selenium.webdriver.Chrome(options=OPTIONS))

        PROFILE = selenium.webdriver.FirefoxProfile()
        PROFILE.accept_untrusted_certs = True
        Tests(selenium.webdriver.Firefox(firefox_profile=PROFILE))
        if '1' in sys.argv:
            # Exit after one test
            EXIT_CODE = 0
            break
except KeyboardInterrupt:
    log('^C')
except: # pylint: disable=bare-except
    log(traceback.format_exc().strip().replace('\n', '\n\t'))
    traceback.print_exc()
finally:
    os.system('./127 stop')
    os.system('rm -r COMPILE_*/*/Anon#* ; rm $(grep -l "Anon#" TICKETS/*)')
    sys.exit(EXIT_CODE)
