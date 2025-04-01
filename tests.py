#!/usr/bin/python3
"""
Regression Test for C5
"""
# pylint: disable=line-too-long

import os
import sys
import time
import subprocess
import traceback
import contextlib
import glob
import requests
import urllib3
import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
import utilities

urllib3.disable_warnings()

def retry(test, required=True, nbr=30):
    """Retry if test failure"""
    for _ in range(nbr):
        try:
            error = test()
            if not error:
                return
        except (selenium.common.exceptions.StaleElementReferenceException,
                selenium.common.exceptions.NoSuchElementException,
                TypeError):
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
        # if self.text not in value:
        #     print("\n=====", self.text)
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
    with open("LOGS/tests.log", "a", encoding='utf-8') as file:
        file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text}\n")

def question(i):
    """Question selector"""
    return f'.index .questions:last-child > DIV:nth-child({i})'
class Tests: # pylint: disable=too-many-public-methods
    """Test for one browser"""
    ticket = None
    def __init__(self, driver):
        self.driver = driver

    def run(self):
        """Run the tests"""
        self.driver.set_window_size(1024, 1024)
        for course_name in ('COMPILE_REMOTE/test', 'COMPILE_JS/introduction', 'COMPILE_JS/example'):
            course = utilities.CourseConfig(course_name)
            course.set_parameter('proctors', 'REGTESTS\n') # Marker for 'clean.py'
            if course_name == 'COMPILE_JS/example':
                course.set_parameter('start', '2099-01-01 00:00:01')
            else:
                course.set_parameter('start', '2000-01-01 00:00:01')
            course.set_parameter('stop', '2100-01-01 00:00:01')
            course.set_parameter('allow_ip_change', '0')
            course.set_parameter('graders', '')
            course.set_parameter('stop', '2100-01-01 00:00:01')
            course.set_parameter('checkpoint', '0')
            course.set_parameter('admins', '')
            course.set_parameter('feedback', 0)
            course.set_parameter('grading_done', 0)
            course.set_parameter('expected_students_required', 0)
            course.set_parameter('hide_before', 360)
            course.set_parameter('state', "Ready")
            if os.path.exists(course_name + '/journal.log'):
                os.unlink(course_name + '/journal.log')
            for i in glob.glob(course_name + '/LOGS/*/journal.log'):
                os.unlink(i)
            for i in glob.glob(course_name + '/LOGS/*/grades.log'):
                os.unlink(i)
            for i in glob.glob(course_name + '/MEDIA/*'):
                os.unlink(i)
        os.system('rm -r COMPILE_REMOTE/XXX')

        start = time.time()
        self.wait_start()
        if 'screenshots' in sys.argv:
            self.screenshots()
            self.driver.close()
            return
        try:
            for test in (
                    self.test_before,
                    self.test_f9,
                    self.test_inputs,
                    self.test_auto_compile,
                    self.test_save_button,
                    self.test_copy_paste_allowed,
                    self.test_question_index,
                    self.test_master_change,
                    self.test_ticket_ttl,
                    self.test_editor,
                    self.test_history,
                    self.test_ip_change_c5,
                    self.test_ip_change_admin,
                    self.test_ip_change_grader,
                    self.test_exam,
                    self.test_source_edit,
                    self.test_many_inputs,
                    self.test_feedback, # Need test_ip_change_grader
                    self.test_results,
                    self.test_rename,
                    self.test_zip,
                    self.test_media,
                    self.test_completion,
                    self.test_manage_tree,
                    self.test_manage_import,
                    self.test_manage_reset,
                    # self.test_git,
                    ):
                print('*'*99)
                print(f'{self.driver.name.upper()} «{test.__func__.__name__}» {test.__doc__.strip()}')
                print('*'*99)
                try:
                    test()
                except:
                    if test is self.test_many_inputs:
                        test()
                    else:
                        raise
                alert = self.get_alert()
                if alert:
                    raise ValueError(f"Unexpected alert: {alert.text}")
            self.driver.close()
            print(f'OK {self.driver.name.upper()} ({time.time()-start:.1f} secs)')
            log(f'OK {self.driver.name.upper()} ({time.time()-start:.1f} secs)')
        except selenium.common.exceptions.WebDriverException:
            print(f'DEADDRIVER {self.driver.name.upper()} ({time.time()-start:.1f} secs) {test}')
            log(f'DEADDRIVER {self.driver.name.upper()} ({time.time()-start:.1f} secs) {test}')
            if 'Failed to decode response from marionette' not in traceback.format_exc():
                raise

    @staticmethod
    def update_config(key, value):
        """Update the configuration by running action."""
        with open('c5.cf', 'a', encoding='utf-8') as file:
            file.write(f'{(key, value)}\n')
    def make_me_admin(self):
        """Make admin the current login"""
        print(f'\t{self.ticket} become admin')
        self.update_config('masters', utilities.CONFIG.masters + ['Anon_' + self.ticket])
        self.goto('config/reload')
        self.check_alert(required=False, nbr=2)
        time.sleep(0.1)
    def clean_up_admin(self):
        """Remove all anonymous logins from admin list"""
        print(f'\t{self.ticket} clean admin')
        self.update_config('ticket_ttl', 86400)
        self.update_config('masters', utilities.CONFIG.masters)
        self.goto('config/reload')
    def make_me_root(self):
        """Make root the current login"""
        self.update_config('roots', utilities.CONFIG.roots + ['Anon_' + self.ticket])
        self.goto('config/reload')
        self.check_alert(required=False, nbr=2)
    def clean_up_root(self):
        """Remove all anonymous logins from admin list"""
        self.update_config('ticket_ttl', 86400)
        self.update_config('roots', utilities.CONFIG.roots)
        self.goto('config/reload')
    @contextlib.contextmanager
    def admin_rights(self):
        """Take temporarely the admin rights"""
        try:
            self.make_me_admin()
            yield
        finally:
            self.clean_up_admin()
    @contextlib.contextmanager
    def root_rights(self):
        """Take temporarely the root rights"""
        try:
            self.make_me_root()
            yield
        finally:
            self.clean_up_root()
    def select_all(self, path='.editor'):
        """Select the full editor content"""
        if path == '.editor':
            self.click('.editor')
        else:
            self.move_cursor(path, 10, 10)
        self.control('a')
        self.control('c')
    def control(self, char):
        """Send a control character"""
        print(f'\tCTRL+{char}')
        action = selenium.webdriver.ActionChains(self.driver)
        action.key_down(Keys.CONTROL)
        action.key_down(char)
        action.key_up(char)
        action.key_up(Keys.CONTROL)
        action.perform()
    def goto(self, url):
        """Load page"""
        print('\tGOTO', url, self.ticket)
        # This line is here to not display the confirming Leave Page popup
        # because Selenium can manage it properly:
        # It says there is a popup by deny dismissing it (sometime randomly)
        self.driver.execute_script("GRADING = true")
        self.driver.get(f"https://127.0.0.1:4201/{url}?ticket={self.ticket}")
    @contextlib.contextmanager
    def change_ip(self):
        """Change the session IP and so break it"""
        try:
            print("\tSESSION IP CHANGE")
            self.driver.execute_script(f"""
            var t = document.createElement('SCRIPT');
            t.src = 'https://127.0.0.1:4201/debug/change_session_ip?ticket={self.ticket}';
            t.onload = function() {{ document.body.className = 'done' }}
            document.body.appendChild(t);
            """)
            self.check('BODY', {'className': Contains('done')})
            yield
        finally:
            print("\tSESSION IP RESTORE")
            self.wait_start()
    def wait_start(self):
        """Wait the server start"""
        def check():
            try:
                self.goto('')
                self.ticket = self.driver.current_url.split('?ticket=')[1]
                return None
            except selenium.common.exceptions.UnexpectedAlertPresentException:
                print('\tDISMISS UNEXPECTED ALERT !!!')
                try:
                    Alert(self.driver).dismiss()
                except selenium.common.exceptions.NoAlertPresentException:
                    print('\tSelenium bug !!!')
                return None
            except selenium.common.exceptions.WebDriverException:
                return "Server connection is impossible"
        retry(check)
    def check(self, path, checks={}, expected=1, nbr=30): # pylint: disable=dangerous-default-value
        """Check"""
        print('\tCHECK', path, checks, expected, end=' ')
        def get_errors():
            print('*', end='', flush=True)
            elements = self.driver.find_elements_by_css_selector(path)
            if len(elements) != expected:
                return f'Expected {expected} elements with the path «{path}» found {len(elements)}'
            if len(elements) == 1:
                element = elements[0]
                self.move_to_element(element)
                for attr, check in checks.items():
                    if attr.startswith('..'):
                        obj = element.find_element_by_xpath('..')
                        attr = attr[2:]
                    else:
                        obj = element
                    if not check.run(obj.get_attribute(attr)):
                        return f'«{path}.{attr}» = «{element.get_attribute(attr)}» {check}'
                get_errors.element = element
            return None
        get_errors.element = None
        retry(get_errors, nbr=nbr)
        print()
        return get_errors.element
    def get_alert(self):
        """Return the alert or None"""
        alert = Alert(self.driver)
        try:
            alert.text
            return alert
        except selenium.common.exceptions.NoAlertPresentException:
            return
    def check_alert(self, contains='', accept=True, required=True, nbr=20, keys=None):
        """Check if an alert is on screen and accept or cancel it"""
        def check():
            print(f'\tALERT Contains=«{contains}» Accept=«{accept}»')
            alert = self.get_alert()
            if alert:
                if contains in alert.text:
                    if accept:
                        if keys:
                            alert.send_keys(keys)
                        alert.accept()
                    else:
                        alert.dismiss()
                    return None
                return f'The alert does not contains «{contains}» but «{alert.text}'
            else:
                return 'No alert on screen'
        retry(check, required, nbr=nbr)
    def check_dialog(self, contains='', accept=True, required=True, nbr=20):
        """Check if an alert is on screen and accept or cancel it"""
        def check():
            print(f'\tDIALOG Contains=«{contains}» Accept=«{accept}»')
            try:
                alert = self.check('DIALOG', nbr=1)
            except ValueError:
                return 'No dialog on screen'
            if not alert:
                return 'No dialog on screen'
            content = alert.get_attribute('innerHTML')
            if contains in content:
                if accept:
                    self.click('#popup_ok')
                else:
                    self.click('#popup_cancel')
                return None
            return f'The dialog does not contains «{contains}» but «{content}'
        retry(check, required, nbr=nbr)
    def load_page(self, url):
        """Load page and clear popup"""
        self.goto(url)
        self.check_alert(required=False, nbr=10)
        self.check_dialog(required=False, nbr=2, accept=False)
        try:
            self.click('.question H2') # Hide popup
        except selenium.common.exceptions.ElementClickInterceptedException:
            self.click('.question H2') # Hide popup
        self.check_dialog(required=False, nbr=2, accept=False)
    def move_to_element(self, element):
        """Make the element visible on screen in order to click on it"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
    def wait_save(self):
        """Wait the source save"""
        self.check('.save_button[state="ok"]')
        self.check('.save_history OPTION:first-child', {'innerText': Not(Equal('Non sauvegardé'))})

    def move_cursor(self, path, relative_x=0, relative_y=0):
        """Set the cursor at the position and click"""
        if path == '.editor':
            path = '.layered'
        element = self.driver.find_elements_by_css_selector(path)[0]
        self.move_to_element(element)
        action = selenium.webdriver.ActionChains(self.driver)
        action.move_to_element_with_offset(element, relative_x, relative_y)
        action.click()
        action.perform()
        if path == '.layered':
            return self.driver.find_elements_by_css_selector('.editor')[0]
        return element
    def test_f9(self):
        """Check if F9 launch compilation"""
        self.load_page('=REMOTE=test')
        self.check('.compiler', {'innerText': Contains('Bravo')})
        self.move_cursor('.editor')
        self.check('.editor').send_keys('\n/**/')
        time.sleep(0.4)
        self.check('.editor').send_keys(Keys.F9)
        self.check('.compiler', {'innerText': Contains('Bravo')})
    def test_inputs(self):
        """Tests inputs"""
        self.load_page('=REMOTE=test')
        self.check('.compiler', {'innerText': Contains('Bravo')})
        self.check('.executor INPUT').send_keys('8')
        self.check('.executor INPUT').send_keys(Keys.ENTER)
        self.check('.executor INPUT:nth-child(3)', {'value': Equal('8')})
        self.check('.executor', {'innerHTML': Contains('symbole')})

        # Modify source code, INPUT is auto filled.
        self.move_cursor('.editor')
        recompile_done = False
        for _ in range(1):
            # Not a normal failure, a bug must be somewhere.
            # Rarely F9 is not working, so retry it
            self.move_cursor('.editor')
            time.sleep(0.4)
            self.check('.editor').send_keys('\n/**/\n\n')
            # The F9 keys must be pressed twice with a delay
            # There is a problem somewhere
            # time.sleep(0.4)
            # self.check('.editor').send_keys(Keys.F9)
            try:
                self.check('.compiler', {'innerText': Contains('Bravo')})
                recompile_done = True
                break
            except ValueError:
                pass
        if not recompile_done:
            raise ValueError('??????????????')
        time.sleep(0.4)
        self.check('.executor INPUT:nth-child(3)', {'value': Equal('8')})
        self.check('.executor', {'innerHTML': Contains('symbole')})

        # Fill second input
        time.sleep(0.6)
        self.check('.executor INPUT:nth-child(7)')
        time.sleep(0.1)
        self.check('.executor INPUT:nth-child(7)').send_keys('*')
        self.check('.executor INPUT:nth-child(7)').send_keys(Keys.ENTER)
        self.check('.executor INPUT:nth-child(7)', {'value': Equal('*')}, nbr=60)
        self.check('.executor', {'innerHTML': Contains('·············***************············')}, nbr=60)

        # Change first input
        self.check('.executor INPUT:nth-child(3)').send_keys(Keys.BACKSPACE)
        self.check('.executor INPUT:nth-child(3)').send_keys('1')
        self.check('.executor INPUT:nth-child(3)').send_keys(Keys.ENTER)
        self.check('.executor', {'innerHTML': Contains('····················*···················')})
    def test_auto_compile(self):
        """Tests automatic recompilation"""
        self.load_page('=JS=introduction')
        self.move_cursor('.editor')
        self.check('.editor').send_keys('\n§')
        self.check('.compiler', {'innerHTML': Contains('illegal') | Contains('Invalid')})
        self.move_cursor('.editor') # Firefox want this
        self.check('.editor').send_keys(Keys.BACKSPACE)
        self.check('.compiler', {'innerHTML': Contains('sans')})

        self.check('.editor').send_keys(Keys.F9)
        self.check('.editor').send_keys('print("Hello")')
        time.sleep(0.3) # Wait a recompile that must not happen
        self.check('.executor', {'innerHTML': ~Contains('Hello')})
        self.check('.editor').send_keys(Keys.F9)
        self.check('.executor', {'innerHTML': Contains('Hello')})

        # Disable compilation by clicking
        self.click('.compiler LABEL')
        self.move_cursor('.editor')
        self.check('.editor').send_keys('§')
        time.sleep(0.3) # Wait a recompile that must not happen
        self.check('.compiler', {'innerHTML': Contains('sans')})
        self.click('.compiler LABEL')
        self.check('.compiler', {'innerHTML': Contains('illegal') | Contains('Invalid')})
    def goto_initial_version(self):
        """Returns to the initial version"""
        self.click('.save_history OPTION:last-child')
        time.sleep(0.2)
    def test_save_button(self):
        """Test save button"""
        self.load_page('=JS=introduction')
        self.move_cursor('.editor', 4, 4)
        self.check('.editor', {'innerHTML': Contains('§')}) # Previous test
        self.goto_initial_version()
        self.check('.editor', {'innerHTML': ~Contains('§')})
        time.sleep(0.1)
        self.move_cursor('.editor', 4, 4)
        self.check('.editor').send_keys('§')
        self.check('.editor', {'innerHTML': Contains('§')})
        self.click('.save_button')
        self.wait_save()
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': Contains('§')})
        time.sleep(0.2) # For Firefox
        self.move_cursor('.editor', 4, 4)
        self.check('.editor').send_keys('¤')
        self.check('.editor', {'innerHTML': Contains('§¤')})
        self.control('s')
        self.wait_save()
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': Contains('§¤')})
        self.move_cursor('.editor', 30, 500)
        for _ in range(6):
            self.check('.editor').send_keys(Keys.BACKSPACE)
        self.click('.save_button')
        self.load_page('=JS=introduction')
        self.check('.editor', {'innerHTML': ~Contains('§')})

    def test_copy_paste_allowed(self):
        """Test a working copy paste"""
        self.load_page('=JS=introduction')
        self.goto_initial_version()
        self.move_cursor('.editor')
        self.click('.editor')
        self.select_all()
        self.control('v')
        self.control('v')
        self.check('.executor', {'innerText': Contains('court\n\nJe')})
    def test_question_index(self):
        """Test question index"""
        self.load_page('=JS=introduction')
        self.goto_initial_version()
        # Try to click on the next question
        self.click(question(4)) # Will fail
        self.check('.editor', {'innerText': Contains('court') & ~Contains('long')})

        self.check(question(3), {'innerText': Contains('1'), 'className': Equal('current possible')})
        self.check(question(4), {'innerText': Contains('2'), 'className': Equal('')})
        self.check(question(5), {'innerText': Contains('3'), 'className': Equal('')})
        self.select_all()

        try:
            self.check('.editor').send_keys("print('Je suis un texte super long')") # Good answer
            self.check_dialog(contains=' !')
            self.check(question(3), {'innerText': Contains('1'), 'className': Equal('good')})
            self.check(question(4), {'innerText': Contains('2'), 'className': Equal('current possible')})
            self.check(question(5), {'innerText': Contains('3'), 'className': Equal('')})
            self.check('.question', {'innerText': Contains('la_chose_a_afficher')})

            # Returns to the first question
            self.click(question(3))
            self.check('.editor', {'innerText': Contains('long')})
            self.check(question(3), {'innerText': Contains('1'), 'className': Equal('current good')})
            self.check(question(4), {'innerText': Contains('2'), 'className': Equal('possible')})
            self.check(question(5), {'innerText': Contains('3'), 'className': Equal('')})
        finally:
            self.wait_save()
            self.click('OPTION:last-child') # Returns to the original text
            self.check('.editor').send_keys(' ')
            self.click('.save_button')
    def test_master_change(self):
        """Test add and remove master"""
        with self.root_rights():
            time.sleep(0.1)
            self.goto('adm/root')
            self.check('.add_master').send_keys('john.doe')
            self.check('.add_master').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains('Master add «john.doe»')})
            self.click('#more')
            self.click("BUTTON.del_master_john_doe")
            self.check('#more', {'innerText': Contains('Master del «john.doe»')})
    def test_ticket_ttl(self):
        """Test TTL change"""
        to_delete = "TICKETS/TO_DELETE"
        to_keep = "TICKETS/TO_KEEP"
        ttl = 123456
        with open(to_delete, "w", encoding='utf-8') as file:
            file.write(f"('1.1.1.1', 'Browser', 'john.doe', {time.time() - ttl - 60})")
        with open(to_keep, "w", encoding='utf-8') as file:
            file.write(f"('1.1.1.1', 'Browser', 'john.doe', {time.time() - ttl + 60})")

        with self.root_rights():
            self.goto('adm/root')
            self.select_all('.ticket_ttl')
            self.check('.ticket_ttl').send_keys('X')
            self.check('.ticket_ttl').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains('Invalid')})
            self.select_all('.ticket_ttl')
            self.check('.ticket_ttl').send_keys(str(ttl))
            self.check('.ticket_ttl').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains(f'to {ttl} seconds')})
            self.click('.remove_olds')
            self.check('#more', {'innerText': Contains('tickets deleted')})
            assert not os.path.exists(to_delete)
            os.unlink(to_keep)
    def test_editor(self):
        """Test editor line insert"""
        # Previous tests must run before this one.
        self.load_page('=JS=introduction')
        self.click(question(3)) # Returns to the first question
        self.goto_initial_version()
        self.check('.overlay', {'innerHTML': ~Contains('§')})
        self.control('y')
        self.check('.overlay', {'innerHTML': Contains('§')})
        while '§' in self.driver.find_elements_by_css_selector('.overlay')[0].get_attribute('innerHTML'):
            self.control('z')
            time.sleep(0.2)
        #for line in sys.stdin:
        #    try:
        #        self.click(question(int(line.strip())))
        #    except:
        #        pass
        editor = self.move_cursor('.editor')
        editor.click()
        self.control(Keys.HOME)
        editor.send_keys('A') # First line
        self.check('.overlay', {'innerHTML': Contains('A\n<span class="hljs-comment">// Lisez')})
        self.control('z')
        self.check('.overlay', {'innerHTML': Contains('\n<span class="hljs-comment">// Lisez')})
        editor.send_keys(Keys.ARROW_DOWN) # Second line
        editor.send_keys('B')
        self.check('.overlay', {'innerHTML': Contains('\nB<span class="hljs-comment">// Lisez')})
        self.control('z')
        editor.send_keys(Keys.ARROW_RIGHT) # Second line second char
        editor.send_keys('C')
        self.check('.overlay', {'innerHTML': Contains('\n/C/ <span class="hljs-title class_">Lisez')})
        self.control('z')
        editor.send_keys(Keys.END) # Second line second char
        editor.send_keys('D')
        self.check('.overlay', {'innerHTML': Contains('\n<span class="hljs-comment">// Lisez la consigne indiquée à gauche.D</span>\n\n')})
        self.control('z')
        self.control(Keys.END)
        editor.send_keys('/')
        editor.send_keys(Keys.ENTER)
        self.check('.overlay', {'innerHTML': Contains(');/\n')})
        editor.send_keys('/')
        self.check('.overlay', {'innerHTML': Contains(');/\n/\n')})
    def test_many_inputs(self):
        """Test IP change in grader editor"""
        nbr = 5
        self.goto('=REMOTE=test')
        # self.check_dialog(contains='', accept=True, required=False, nbr=2)
        time.sleep(1)
        self.click('.editor')
        self.check('.editor').send_keys(' ')
        self.control('a')
        time.sleep(1)
        self.check('.editor').send_keys('''
using namespace std;
#include <iostream>
int main()
{
int v, sum = 0 ;
for(int i = 0 ; i < '''+str(nbr)+'''; i++ ) { cout << i << endl ; cin >> v ; sum += v ; }
return sum ;
}
''')
        time.sleep(0.3)
        self.check('.editor').send_keys(Keys.F9)
        for i in range(nbr):
            self.check(f'.executor DIV:nth-child({4*i+2})', {'textContent': Equal(str(i)+'\n')})
            time.sleep(0.1)
            element = self.click(f'.executor INPUT:nth-child({4*i+3})')
            time.sleep(0.2)
            element.send_keys('1')
            element.send_keys(Keys.ENTER)
        self.check('.executor', {'textContent': Contains('cution = ' + str(nbr))})
    def test_before(self):
        """Goto exam before opening"""
        self.goto('=JS=example')
        self.check('BODY', {'innerHTML': Contains(utilities.CONFIG.config['messages']['pending'])
                          & Contains('SN') & Contains('Fn')})
    def test_history(self): # pylint: disable=too-many-statements
        """Test history managing and TAGs"""
        self.load_page('=TEXT=demo')
        self.check('.save_history', {'length': Equal('2')})
        editor = self.move_cursor('.editor')
        # self.check('.editor', {'textContent': Contains('Bravo')})
        editor.send_keys('univers vie')
        self.check_dialog(accept=True, required=True) # Ok to congratulation
        # We are now automaticaly on the second question
        self.check('.save_history', {'length': Equal('2')})
        time.sleep(1) # Really needed
        self.click(question(3)) # Returns to the first question
        self.check('.save_history', {'length': Equal('2')}) # Has been saved

        # Tag the good anwser on first question
        self.control('s')
        self.check('#popup_input').send_keys('A')
        self.click('#popup_ok')
        self.check('.save_history', {'innerHTML': Contains('>A1<') & Contains('<option>Vers')})

        # Change the answer and then change the question without saving
        editor.send_keys(' every')
        # self.check('.save_history', {'innerHTML': Contains('>Non')}, nbr=300)
        # time.sleep(0.2)
        self.control('s')
        self.click('#popup_ok')

        self.click(question(4)) # goto the second question
        self.wait_save() # No save needed
        self.check('.save_history', {'length': Equal('2')}) # Only initial version
        self.click(question(3)) # Returns to the first question
        self.check('.save_history', {'length': Equal('4')}) # A new save !
        self.control('s')
        self.check('#popup_input').send_keys('B')
        self.check('#popup_input').send_keys(Keys.ENTER)
        self.check('.save_history', {'length': Equal('5')}, nbr=200)
        self.check('.save_history', {'innerHTML': Contains('>A1<') & Contains('>B3<') & Contains('<option>Vers')})
        self.control('s')
        self.check('#popup_input').send_keys(Keys.ENTER)
        self.wait_save()

        # Goto in the past (A) and change question: no saving done
        self.click('.save_history OPTION:nth-child(3)')
        self.click(question(4)) # Returns to the second question
        self.check('.editor', {'textContent': Contains('Bravo')})
        self.click(question(3)) # Returns to the first question
        self.check('.save_history', {'length': Equal('6')}, nbr=200)

        # Goto in the past (A) modify and change question: saving done
        self.click('.save_history OPTION:nth-child(5)')
        editor.click()
        editor.send_keys(' thing')
        # self.check('.save_history', {'innerHTML': Contains('>Non')}, nbr=200)
        self.click(question(4)) # Returns to the second question
        self.click(question(3)) # Returns to the first question
        self.check('.save_history', {'length': Equal('6')})
        # self.check('.save_history', {'value': Equal("Non sauvegardé")})

        # Tag the new save
        self.control('s')
        self.check('#popup_input').send_keys('C')
        self.check('#popup_input').send_keys(Keys.ENTER)
        self.wait_save()
        time.sleep(0.1)
        self.check('.save_history', {'length': Equal('7')})
        self.check('.save_history', {'innerHTML': Contains('>A1<') & Contains('>B3<')
            & Contains('>C5<') & Contains('<option>Vers')})

        # Navigate in history and change question
        self.click('.save_history OPTION:nth-child(5)')
        self.click('.save_history OPTION:nth-child(4)')
        self.click('.save_history OPTION:nth-child(3)')
        self.click('.save_history OPTION:nth-child(2)')
        # self.check('.save_history', {'value': Equal("C")})
        self.click(question(4)) # Returns to the second question
        self.click(question(3)) # Returns to the first question
        self.check('.save_history', {'length': Equal('7')})
        # self.check('.save_history', {'value': Equal("C")})
        self.goto('')
        time.sleep(0.1)
        self.check_alert(accept=True, required=False, nbr=10)
    def test_ip_change_c5(self):
        """Test IP change on C5 admin"""
        with self.root_rights():
            self.goto('')
            try:
                self.check('.add_author').send_keys('titi')
            except: # pylint: disable=bare-except
                time.sleep(10000)
            self.check('.add_author').send_keys(Keys.ENTER)
            self.check('#more', {'innerText': Contains('Author add «titi»')})
            self.click('.del_author_titi')
            self.check('#more', {'innerText': Contains('Author del «titi»')})
            with self.change_ip():
                self.check('.add_author').send_keys('titi')
                self.check('.add_author').send_keys(Keys.ENTER)
                try:
                    self.check('BODY', {'innerText': Contains('session a expiré')})
                except ValueError: # XXX
                    time.sleep(10000)
    def test_ip_change_admin(self):
        """Test IP change on admin"""
        with self.admin_rights():
            self.goto('adm/session/JS=example')
            self.click('#Access')
            self.check('#admins').send_keys('titi')
            self.click('#creator')
            self.check('#admins', {'className': Contains('changed')})
            self.click('#admins')
            self.control('a')
            self.check('#admins').send_keys(Keys.BACKSPACE)
            self.click('#creator')
            self.check('#admins', {'className': Equal('')})
            self.click('#Config')
            self.check('#allow_ip_change', {'..className': Equal(''), 'checked': Equal(None)}).click()
            self.check('#allow_ip_change', {'..className': Contains('changed'), 'checked': Equal('true')}, nbr=200)
            self.click('#allow_ip_change')
            self.check('#allow_ip_change', {'..className': Equal('')}, nbr=200)
            with self.change_ip():
                self.click('#allow_ip_change')
                time.sleep(0.1)
                self.check('#allow_ip_change', {'..className': Equal('wait_answer')})
    def test_ip_change_grader(self):
        """Test IP change in grader editor"""
        self.goto('=REMOTE=test')
        self.check('.save_button', {'state': Equal('ok')})
        self.check_dialog(contains='', accept=True, required=False, nbr=2)
        self.move_cursor('.editor')
        self.check('.editor').send_keys('/**/')
        self.check('.save_button', {'state': Equal('ok')}).click()
        self.check('#popup_input').send_keys(Keys.ENTER)
        student = f'Anon_{self.ticket}'
        self.ticket = None
        self.goto('')
        self.check_alert(accept=True, required=False, nbr=10)
        self.wait_start()
        self.goto(f'grade/REMOTE=test/{student}')
        self.check('BODY', {'innerText': Contains('surveillez pas')})
        with self.admin_rights():
            # admin is allowed to grade
            # self.goto(f'grade/REMOTE=test/{student}')
            # self.check_alert('pas autorisé à noter', accept=True, required=True)

            self.goto('adm/session/REMOTE=test')
            self.click('#Access')
            self.move_cursor('#graders')
            self.control('a')
            self.check('#graders').send_keys(f'\nAnon_{self.ticket}')
            self.click('#creator')
            self.check('#graders', {'className': Contains('changed')})

            self.click('#Grading')
            self.move_cursor('#notation')
            self.control('a')
            self.check('#notation').send_keys(f'{student}\na {{A:0,1,2}}\nb {{B:0.1,0.2,0.3}}\n')
            self.click('#Access')
            self.click('#Grading')
            self.check('#notation', {'className': Contains('changed')})

            self.goto(f'grade/REMOTE=test/{student}')
            try:
                self.check('[g="1"]:nth-child(2)',
                    {'className': Contains('grade_unselected') & Contains('grade_undefined')}).click()
            except selenium.common.exceptions.StaleElementReferenceException:
                # Retry
                self.check('[g="1"]:nth-child(2)',
                    {'className': Contains('grade_unselected') & Contains('grade_undefined')}).click()

            self.check('[g="1"]:nth-child(2)',
                {'className': Contains('grade_selected')})

            return # XXX tester la saisie de commentaires

            self.check('.comments TEXTAREA:first-child', {'className': Equal('empty')}).click()
            time.sleep(0.1)
            self.check('.comments TEXTAREA:first-child').send_keys(f'=={student}==')
            self.click('[g="1"]:nth-child(2)')
            self.check('.comments TEXTAREA:first-child', {'className': Equal('filled')}).click()

            with self.change_ip():
                self.check('[g="1"]:nth-child(2)',
                    {'className': Contains('grade_unselected') & Contains('grade_undefined')}).click()
                self.check_dialog('session a expiré', accept=True, required=True)

                self.click('.comments TEXTAREA:first-child')
                self.control('a')
                self.check('.comments TEXTAREA:first-child').send_keys(Keys.BACKSPACE)
                self.click('.question H2')
                self.check_dialog('session a expiré', accept=True, required=True)

    def click(self, path):
        """Click on an element, retry if not yet possible"""
        try:
            element = self.check(path)
            element.click()
        except (selenium.common.exceptions.ElementNotInteractableException,
                selenium.common.exceptions.StaleElementReferenceException):
            time.sleep(0.5)
            element = self.check(path)
            element.click()
        return element

    def test_dates(self, start, end, check, state):
        """No feedback exam even if allowed"""
        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            self.click('#start')
            self.control('a')
            self.check('#start').send_keys(start)
            self.click('#stop')
            self.check('#server_feedback', {'innerHTML': Contains('Start date updated')})
            self.click('#stop')
            self.control('a')
            self.check('#stop').send_keys(end)
            self.click('#start')
            self.check('#server_feedback', {'innerHTML': Contains('Stop date updated')})
            self.check(f'#state OPTION[value="{state}"]').click()
        self.goto('=REMOTE=test')
        self.check('BODY', check)

    def test_feedback(self):
        """Test feedback"""
        student = f'Anon_{self.ticket}'
        no_grades = Contains('GRADES = null')
        no_grade = Contains('GRADE = null')
        no_details = Contains('NOTATION = ""')
        no_feedback = {'innerHTML': no_grades and no_grade and no_details}
        nothing = { 'innerHTML': ~Contains('ccccc.js') }
        self.test_dates('2099-01-01 01:00:50', '2100-01-01 01:00:50', nothing, 'Grade')
        self.test_dates('2000-01-01 01:00:51', '2100-01-01 01:00:51', nothing, 'Grade')
        self.test_dates('2000-01-01 01:00:52', '2001-01-01 01:00:52', nothing, 'Grade')
        self.test_dates('2099-01-01 01:00:50', '2100-01-01 01:00:50', nothing, 'Ready')
        self.test_dates('2000-01-01 01:00:51', '2100-01-01 01:00:51', no_feedback, 'Ready')
        self.test_dates('2000-01-01 01:00:52', '2001-01-01 01:00:52', nothing, 'Ready')
        cases = (
            (0, 5, {'innerHTML': Not(Contains('ccccc.js'))}),
            (5, 0, {'innerHTML': Not(Contains('ccccc.js'))}),
            (5, 1, {'innerHTML': no_grades and no_grade and no_details}),
            (1, 5, {'innerHTML': no_grades and no_grade and no_details}),
            # (3, 5, {'innerHTML': no_grades and no_grade and no_details}),
            (4, 5, {'innerHTML': ~no_grades and ~no_grade and no_details}),
            (5, 5, {'innerHTML': ~no_grades and ~no_grade and ~no_details}),
            (0, 0, {'innerHTML': Not(Contains('ccccc.js'))}),
        )
        with self.admin_rights():
            self.goto(f'grade/REMOTE=test/{student}')
            while len(self.driver.find_elements_by_css_selector(
                '.grade_unselected:first-child')) == 0:
                time.sleep(0.1)
            time.sleep(0.1)
            for grade in self.driver.find_elements_by_css_selector(
                '.grade_unselected:first-child'):
                grade.click()
            while len(self.driver.find_elements_by_css_selector(
                '.grade_unselected:first-child')) != 0:
                time.sleep(0.1)
        for admin_feeback, grader_feedback, check in cases:
            with self.admin_rights():
                self.goto('adm/session/REMOTE=test')
                self.click('#state OPTION[value="Done"]')
                self.click(f'#feedback OPTION[value="{admin_feeback}"]')
                self.click('#start')
                self.goto(f'grade/REMOTE=test/{student}')
                time.sleep(0.5)
                self.click(f'#grading_feedback OPTION[value="{grader_feedback}"]')
                self.click('.editor')
            self.goto('=REMOTE=test')
            self.check('BODY', check)
        self.test_dates('2000-01-01 01:00:01', '2001-01-01 01:00:01', nothing, 'Done')

    def test_exam(self): # pylint: disable=too-many-statements
        """Test an exam"""
        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            self.click('#start')
            self.control('a')
            self.check('#start').send_keys('2000-01-01 00:00:00')
            self.click('#stop')
            self.check('#start', {'className': Equal('changed')})
            self.control('a')
            self.check('#stop').send_keys('2000-01-01 01:00:00')
            self.check('#checkpoint', {'checked': Equal(None)}).click()
            self.click('#start')
            self.check('#stop', {'className': Equal('changed')})
        self.ticket = None
        self.wait_start()
        self.check('BODY', {'innerHTML': ~Contains('/=REMOTE=test')})
        self.goto('=REMOTE=test')
        self.check('BODY', {'textContent': Contains("Donnez votre nom à l'enseignant pour qu'il vous ouvre l'examen")})

        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            self.click('#start')
            self.control('a')
            self.check('#start').send_keys('2050-01-01 00:00:00')
            self.click('#stop')
            self.control('a')
            self.check('#stop').send_keys('2050-01-01 01:00:00')
            self.click('#hide_before')
        self.ticket = None
        self.wait_start()
        self.check('BODY', {'innerHTML': Not(Contains('/=REMOTE=test'))})

        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            self.click('#hide_before')
            self.control('a')
            self.check('#hide_before').send_keys('1000000000')
            self.click('#start')
        self.ticket = None
        self.wait_start()
        self.check('BODY', {'innerHTML': Contains('=REMOTE=test')})

        self.goto('=REMOTE=test')
        self.check('BODY', {'textContent': Contains("Donnez votre nom à l'enseignant")})

        student = self.ticket

        self.ticket = None
        self.wait_start()
        with self.admin_rights():
            self.goto('checkpoint/REMOTE=test')
            self.check(f'DIV[login=Anon_{student}]', {'innerHTML': Contains(student)})
            self.driver.execute_script(
                f"record('checkpoint/REMOTE=test/Anon_{student}/Nautibus,42,42,a')")
            admin = self.ticket
            time.sleep(0.1)

            self.ticket = student
            self.goto('=REMOTE=test')
            self.check('BODY', {'textContent': Contains("pas commencé")})

            self.ticket = admin
            self.goto('adm/session/REMOTE=test')
            self.click('#start')
            self.control('a')
            self.check('#start').send_keys('2000-01-01 00:00:00')
            self.click('#stop')
            self.control('a')
            duration = 3
            stop = time.localtime(time.time() + duration)
            self.check('#stop').send_keys(time.strftime('%Y-%m-%d %H:%M:%S', stop))
            self.click('#start')
            time.sleep(0.1)

            self.ticket = student
            self.goto('=REMOTE=test')
            self.check('.editor').send_keys(' /**/')
            self.check('.save_button', {'state': Equal('ok')}).click()
            self.check('#popup_input').send_keys(Keys.ENTER)
            self.check('.save_button', {'state': Equal('ok')})
            self.move_cursor('.editor')
            self.check('.editor').send_keys(' /*2*/')
            time.sleep(duration)
            self.check('BODY', {'innerHTML': Contains('fini')})

            self.ticket = admin
            self.goto('adm/session/REMOTE=test')
            time.sleep(0.1)
            self.check_alert(accept=True, required=False, nbr=10)
            self.check('#checkpoint', {'checked': Equal('true')}).click()
            self.click('#stop')
            self.control('a')
            self.check('#stop').send_keys('2100-01-01 01:00:00')
            self.click('#start')
            time.sleep(0.1)

    def create_session_xxx(self):
        """Create a fake session"""
        if not os.path.exists('COMPILE_REMOTE/xxx'):
            os.mkdir('COMPILE_REMOTE/xxx')
        with open('COMPILE_REMOTE/xxx/questions.py', 'w', encoding='utf-8') as file:
            file.write('''
COURSE_OPTIONS = {'state': 'Ready', 'checkpoint': False}
class Q1(Question):
    def question(self):
        return "TheQuestion"
    def tester(self):
        self.display('TheEnd')
    def default_answer(self):
        return "TheAnswer"
#

''')
        os.system('make COMPILE_REMOTE/xxx/questions.js')

    def delete_session_xxx(self):
        """Delete fake session"""
        for name in ('xxx', 'xxxx'):
            if os.path.exists('COMPILE_REMOTE/' + name):
                with self.admin_rights():
                    self.goto(f'adm/reset/REMOTE={name}/Source')
                    self.check('BODY', {'innerHTML': Contains('Delete session')})

    def test_source_edit(self):
        """Test questionnary editor"""
        self.create_session_xxx()
        with self.admin_rights():
            self.goto('adm/editor/REMOTE=xxx')
            self.check('.question', {'innerHTML': Contains('TheQuestion') & Contains('>TheAnswer<')})
            self.move_cursor('.editor')
            self.check('.editor').send_keys('''class Q2(Question):
    def question(self):
        return "AnotherQuestion"
''')
            self.check('.question', {'innerHTML': Contains('AnotherQuestion')})
            self.control('s')
            self.check('#popup_input').send_keys(Keys.ENTER)
            # self.check_alert('COMPILE_REMOTE/xxx/questions.py → COMPILE_REMOTE/xxx/questions.js', accept=True, required=True)
            self.control('w')
        self.delete_session_xxx()

    def test_results(self):
        """Check session display"""
        with self.admin_rights():
            self.goto('adm/course/REMOTE=test')
            self.check('BODY', {'innerHTML': Contains('<div id="top"></div>')})

    def test_rename(self):
        """Check session renaming"""
        self.create_session_xxx()
        self.load_page('=REMOTE=xxx')
        self.check('.editor', {'innerHTML': Contains('TheAnswer')})
        with self.admin_rights():
            self.goto('adm/session/REMOTE=xxx')
            self.click('SELECT OPTION[action="rename_session"]')
            self.check_alert(keys="xxxx")
            self.check('BODY', {'innerHTML': Contains('«REMOTE=xxx» Renamed as «REMOTE=xxxx»')})
        self.delete_session_xxx()

    def load_zip(self, url):
        """Retrieve a ZIP and returns the filename list"""
            # Using self.goto() will lock selenium firefox driver
        self.driver.execute_script(
            f"window.open('https://127.0.0.1:4201/{url}/test.zip?ticket={self.ticket}')")
        for _ in range(20):
            time.sleep(0.1)
            names = glob.glob(os.path.expanduser('~/*/test.zip'))
            if names:
                break
            names = glob.glob(os.path.expanduser('~/test.zip'))
            if names:
                break
        else:
            raise ValueError('Downloaded file not found')
        print('\t\t', names)
        self.goto('x')
        name = names[0]
        while os.path.getsize(name) == 0:
            time.sleep(0.1)
        p = subprocess.run(['unzip', '-l', name], capture_output=True, check=True)
        # subprocess.run(['cp', name, '/tmp/toto.zip'], check=True)
        os.unlink(name)
        return p.stdout

    def test_zip(self):
        """Load session ZIP"""
        with self.admin_rights():
            files = self.load_zip('adm/get/COMPILE_REMOTE')
            for value in (b'questions.py', b'questions.js', b'questions.json', b'session.cf'):
                assert b'COMPILE_REMOTE/test/' + value in files

    def test_media(self):
        """Media: Uploading Listing Removing"""
        save_ticket = self.ticket
        response = requests.get('https://127.0.0.1:4201/', verify = False)
        self.ticket = response.text.split('TICKET = "')[1].split('"')[0]
        with self.admin_rights():
            with open('COMPILE_REMOTE/grapic/MEDIA/chien.png', 'rb') as file:
                content = file.read()
            response = requests.post(
                f"https://127.0.0.1:4201/upload_media/REMOTE/grapic?ticket={self.ticket}",
                data={'filename': 'xxx-test.png'},
                files={'course': ('xxx-test.png', content, 'text/plain')},
                verify=False
            )
            assert 'src="media/REMOTE=grapic/xxx-test.png' in response.text
        self.ticket = save_ticket
        with self.admin_rights():
            self.goto('adm/session/REMOTE=grapic')
            self.click('#Media')
            self.driver.switch_to.frame(0)
            retry(lambda: len(self.driver.find_elements_by_css_selector('BUTTON')) != 2)
            for i in self.driver.find_elements_by_css_selector('BUTTON'):
                if 'grapic/delete/xxx-test.png' in i.get_attribute('outerHTML'):
                    i.click()
            retry(lambda: len(self.driver.find_elements_by_css_selector('BUTTON')) != 1)
            self.driver.switch_to.default_content()

    def test_git(self):
        """GIT"""
        def upload(src, name="_new_"):
            return requests.post(
                f"https://127.0.0.1:4201/upload_course/REMOTE/{name}?ticket={self.ticket}",
                data={'filename': 'xxx.py'},
                files={'course': ('xxx.py', src, 'text/plain')},
                verify=False)
        def get_state():
            files = [
                "COMPILE_REMOTE/xxx/" + i
                for i in "questions.py questions.json session.cf questions.js".split(' ')
            ]
            with subprocess.Popen(['cat', *files],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL) as process:
                return process.stdout.read()

        response = requests.get('https://127.0.0.1:4201/', verify = False)
        self.delete_session_xxx()
        save_ticket = self.ticket
        self.ticket = response.text.split('TICKET = "')[1].split('"')[0]
        with self.admin_rights():
            self.goto('checkpoint/*')

            print("\tUpload bad source")
            response = upload("class Q1(Question):\n pass\n")
            assert 'background:#FAA;">ERROR' in response.text
            assert not os.path.exists('COMPILE_REMOTE/xxx')

            print("\tUpload good source")
            response = upload("class Q1(Question):\n    pass\n")
            assert '<td class="clipped course"><div>xxx' in response.text
            good_content = get_state()

            print("\tUpload good source but no replace")
            response = upload("class Q2(Question):\n    pass\n")
            assert 'background:#FAA;">«COMPILE_REMOTE/xxx» file exists!' in response.text
            assert get_state() == good_content

            print("\tReplace a non existing session")
            response = upload("class Q1(Question):\n    pass\n", "xxxxx")
            assert '500 Internal Server Error' in response.text

            print("\tReplace good source by a bad one")
            response = upload("cl ass Q1(Question):\n    pass\n", "xxx")
            assert 'background:#FAA">ERROR: Unexpected token' in response.text
            if get_state() != good_content:
                for a, b in zip(get_state().split(b'\n'), good_content.split(b'\n')):
                    print(a)
                    if a != b:
                        print(b)
                        break
                bug
        self.ticket = save_ticket

        print("\tCreate a local repository")
        os.system("""
        (
        rm -rf XXX
        cp -a COMPILE_REMOTE/xxx XXX
        cd XXX
        git init
        git add questions.py
        git commit -a -m "First commit"
        ) >/dev/null
        """)

        with self.admin_rights():
            print("\tC5 pull with identical directories")
            self.goto('adm/session/REMOTE=xxx')
            self.click('#git_url')
            self.control('a')
            self.check('#git_url').send_keys(f"file://{os.getcwd()}/XXX")
            self.click('#start')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains('nothing to commit, working tree clean')
                    & Contains("questions.js' is up to date.")
                }
            )

            print("\tC5 pull good changes")
            os.system("""
                    (
                    cd XXX
                    echo '# Change 1' >>questions.py
                    git commit -a -m "Change 1"
                    ) >/dev/null
                    """)
            self.goto('adm/session/REMOTE=xxx')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains("No local changes to save")
                    & Contains("questions.py | 1 +")
                    & Contains("No stash entries")
                    & Contains("questions.js OK")
                    & Contains("questions.json OK")
                }
            )

            print("\tC5 pull no change on C5 change")
            with open('COMPILE_REMOTE/xxx/questions.py', 'a', encoding='utf-8') as file:
                file.write("# Change C5\n")
            self.goto('adm/session/REMOTE=xxx')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains("Saved working directory and index state WIP on master")
                    & Contains("Already up to date")
                    & Contains("# START #")
                    & Contains("+# Change C5")
                    & Contains("# STOP #")
                    & Contains("questions.js OK")
                    & Contains("questions.json OK")
                }
            )

            print("\tC5 pull resynchronize")
            os.system("""
                    (
                    cd XXX
                    echo '# Change C5' >>questions.py
                    git commit -a -m "Change 2"
                    ) >/dev/null
                    """)
            self.goto('adm/session/REMOTE=xxx')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains("Saved working directory and index state WIP on master")
                    & Contains("questions.py | 1 +")
                    & Contains("nothing to commit, working tree clean")
                    & Contains("questions.js OK")
                    & Contains("questions.json OK")
                }
            )

            print("\tC5 pull changes on both sides")
            os.system("""
                    (
                    cd XXX
                    sed -i 's/Q1/Q42/' questions.py
                    git commit -a -m "Change 3"
                    ) >/dev/null
                    """)
            with open('COMPILE_REMOTE/xxx/questions.py', 'a', encoding='utf-8') as file:
                file.write("# Change C5 conflict\n")
            self.goto('adm/session/REMOTE=xxx')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains("Saved working directory and index state WIP on master")
                    & Contains("Auto-merging questions.py")
                    & Contains("no changes added to commit")
                    & Contains("# START #")
                    & Contains("+# Change C5 conflict")
                    & Contains("# STOP #")
                    & Contains("questions.js OK")
                    & Contains("questions.json OK")
                }
            )

            with open('COMPILE_REMOTE/xxx/questions.py', 'r', encoding='utf-8') as file:
                content = file.read()
            assert '# Change C5 conflict' in content
            assert 'Q42' in content

            print("\tC5 pull bad Python")
            os.system("""
                    (
                    cd XXX
                    sed -i 's/Question/BadQuestion/' questions.py
                    git commit -a -m "Change 4"
                    ) >/dev/null
                    """)
            self.goto('adm/session/REMOTE=xxx')
            self.click('OPTION[action="git_pull"]')
            self.check('BODY',
                {'innerHTML':
                    Contains("Saved working directory and index state WIP on master")
                    & Contains("Auto-merging questions.py")
                    & Contains("questions.py | 2 +-\n")
                    & Contains("1 file changed, 1 insertion(+), 1 deletion(-)")
                    & Contains("# START #")
                    & Contains("\n+# Change C5 conflict")
                    & Contains("# STOP #")
                    & Contains("questions.js OK")
                    & Contains("questions.json FAIL")
                }
            )

            with open('COMPILE_REMOTE/xxx/questions.js', 'r', encoding='utf-8') as file:
                content = file.read()
            assert 'Q42' in content
            assert 'a_not_existing_variable' not in content

        self.delete_session_xxx()

    def test_completion(self):
        """Test completion"""
        self.load_page('=JS=introduction')
        self.goto_initial_version()
        base = 'aa aaa aab ab abb bbb dd\n'
        def check(expected):
            retry(lambda: self.driver.execute_script("return ccccc.source")
                          if self.driver.execute_script("return ccccc.source") != expected
                          else False)
        def options(expected):
            completion = self.check('.completion')
            if 'display: none' in completion.get_attribute('style'):
                opt = ''
            else:
                opt = completion.get_attribute('innerHTML')
                opt = opt.replace('</option>', '')
                opt = opt.replace('<option class="">', ',')
                opt = opt.replace('<option>', ',')
                opt = opt.replace('<option class="active_completion">', ',*')
                opt = opt[1:]
            if opt == expected:
                return False
            return opt

        for text, menu, expected in (
                ('b', ''                 , 'bbb'),
                ('d', ''                 , 'dd' ),
                ('a', 'aa,aaa,aab,ab,abb', 'a'  ),
                ):
            editor = self.move_cursor('.editor')
            editor.click()
            self.control('a')
            self.control('x')
            editor.send_keys(base.strip())
            editor.send_keys(Keys.ENTER) # To please Firefox
            editor.send_keys(text)
            check(base + text)

            self.control(' ')
            check(base + expected)
            retry(lambda: options('*' + menu))

            if not menu:
                retry(lambda: options(''))
                continue

            # Cursor move in menu
            menu2 = menu.replace(',', ',*', 1)
            editor.send_keys(Keys.ARROW_DOWN) # Second line
            retry(lambda: options(menu2))
            editor.send_keys(Keys.ARROW_UP) # First line
            retry(lambda: options('*' + menu))

            # Other keys hide the menu
            editor.send_keys('a')
            retry(lambda: options(''))
            check(base + text + 'a')

            # Use Enter in the menu
            editor.send_keys(Keys.BACKSPACE)
            check(base + expected)
            self.control(' ')
            retry(lambda: options('*' + menu))
            editor.send_keys(Keys.ENTER)
            first_item = menu.split(',')[0]
            check(base + first_item) # First item

            # Use click in the menu
            # Impossible to make work, clicking on datalist option is forbidden
            # for _ in range(len(first_item)-1):
            #     editor.send_keys(Keys.BACKSPACE)
            # check(base + expected)
            # self.control(' ')
            # retry(lambda: options('*' + menu))
            # second_item = menu.split(',')[1]
            # # Selenium bug: selector «.completion OPTION:nth-child(2)» is rejected
            # # self.move_cursor('.completion OPTION:nth-child(2)', 3, 3)
            # for i in self.driver.find_elements_by_css_selector('OPTION:nth-child(2)'):
            #     if i.get_attribute('innerHTML') == second_item:
            #         action = selenium.webdriver.ActionChains(self.driver)
            #         action.move_to_element(i)
            #         action.click_and_hold()
            #         action.release()
            #         action.perform()
            #         break
            # # sys.stdin.readline()
            # retry(lambda: options(''))
            # check(base + second_item)

    def test_manage_tree(self):
        """Test tree ticking and export"""
        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            self.click('#Manage')
            tree = self.check('#tree')
            labels = self.driver.find_elements_by_css_selector('#tree LABEL')
            inputs = self.driver.find_elements_by_css_selector('#tree INPUT')
            export_button, _import_button, _reset_button = self.driver.find_elements_by_css_selector('#tree_menu BUTTON')
            retry(lambda: not export_button.get_attribute('disabled'))
            state = self.driver.execute_script("return get_state()")
            assert state == ''
            labels[0].click() # Check all
            retry(lambda: export_button.get_attribute('disabled'))
            retry(lambda: not inputs[-1].get_attribute('checked'))
            state = set(self.driver.execute_script("return get_state()").split(' '))

            # Unclick last
            labels[-1].click()
            retry(lambda: inputs[-1].get_attribute('checked'))
            state2 = set(self.driver.execute_script("return get_state()").split(' '))
            assert state - state2 == set(('messages',))
            retry(lambda: export_button.get_attribute('disabled'))

            # Uncheck all
            labels[0].click() # Uncheck all
            retry(lambda: inputs[-1].get_attribute('checked')) # Always unchecked
            state2 = self.driver.execute_script("return get_state()")
            assert state2 == ''
            retry(lambda: not export_button.get_attribute('disabled'))

            # Export
            files = self.load_zip('adm/export/REMOTE=test/' + ' '.join(state))
            for name in (b'session.cf', b'questions.py'):
                assert b'C5/COMPILE_REMOTE/test/' + name in files
            assert files.count(b' C5/') - files.count(b'/Anon_') == 2

            if not os.path.exists('COMPILE_REMOTE/test/MEDIA'):
                os.mkdir('COMPILE_REMOTE/test/MEDIA')
            open('COMPILE_REMOTE/test/MEDIA/foo.png', 'wb').close()
            if not os.path.exists('COMPILE_REMOTE/test/LOGS'):
                os.mkdir('COMPILE_REMOTE/test/LOGS')
            if not os.path.exists('COMPILE_REMOTE/test/LOGS/john.doe'):
                os.mkdir('COMPILE_REMOTE/test/LOGS/john.doe')
            open('COMPILE_REMOTE/test/LOGS/john.doe/journal.log', 'wb').close()
            open('COMPILE_REMOTE/test/LOGS/john.doe/grades.log', 'wb').close()
            files = self.load_zip('adm/export/REMOTE=test/' + ' '.join(state))
            for name in (b'session.cf', b'questions.py', b'MEDIA/foo.png',
                         b'LOGS/john.doe/journal.log', b'LOGS/john.doe/grades.log'):
                assert b'C5/COMPILE_REMOTE/test/' + name in files
            assert files.count(b' C5/') - files.count(b'/Anon_') == 5

            # Filtered export (do not check individual session attributes)
            state.discard('Grades')
            state.discard('Journal')
            state.discard('Media')
            files = self.load_zip('adm/export/REMOTE=test/' + ' '.join(state))
            for name in (b'session.cf', b'questions.py'):
                assert b'C5/COMPILE_REMOTE/test/' + name in files
            assert files.count(b' C5/') - files.count(b'/Anon_') == 2

    def test_manage_import(self):
        """Test filtered import"""
        with open('tests_import.zip', 'rb') as file:
            zip_content = file.read()
        def send(what, session):
            print(f'\twhat=«{what}» session=«{session}»')
            if session:
                destination = 'one'
            else:
                destination = 'multiple'
            response = requests.post(
                f"https://127.0.0.1:4201/adm/import/{what}?ticket={self.ticket}",
                data={'destination': destination, 'session': session},
                files={'zip': ('foo.zip', zip_content, 'application/zip')},
                verify=False
                )
            return response.text

        save_ticket = self.ticket
        response = requests.get('https://127.0.0.1:4201/', verify = False)
        self.ticket = response.text.split('TICKET = "')[1].split('"')[0]
        with self.admin_rights():
            self.goto('adm/session/REMOTE=test')
            output = send('sequential', '')
            assert output == '<h1>COMPILE_REMOTE/test</h1>\n<br>C5/COMPILE_REMOTE/test/session.cf<br><span style="color:#BBB">C5/COMPILE_REMOTE/test/LOGS/john.doe/journal.log</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/LOGS/john.doe/grades.log</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/MEDIA/foo.png</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/questions.py</span><h1>Compile and Load configs</h1><h2>COMPILE_REMOTE/test</h2><pre>make: &#x27;COMPILE_REMOTE/test/questions.js&#x27; is up to date.\n</pre>'
            output = send('Source', '')
            assert output == '<h1>COMPILE_REMOTE/test</h1>\n<br><span style="color:#BBB">C5/COMPILE_REMOTE/test/session.cf</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/LOGS/john.doe/journal.log</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/LOGS/john.doe/grades.log</span><br><span style="color:#BBB">C5/COMPILE_REMOTE/test/MEDIA/foo.png</span><br>C5/COMPILE_REMOTE/test/questions.py<h1>Compile and Load configs</h1><h2>COMPILE_REMOTE/test</h2><pre>COMPILE_REMOTE/test/questions.py â\x86\x92 COMPILE_REMOTE/test/questions.js OK\nCOMPILE_REMOTE/test/questions.py â\x86\x92 COMPILE_REMOTE/test/questions.json OK\n</pre>'
            output = send('Journal Grades Media', '')
            assert output == '<h1>COMPILE_REMOTE/test</h1>\n<br><span style="color:#BBB">C5/COMPILE_REMOTE/test/session.cf</span><br>C5/COMPILE_REMOTE/test/LOGS/john.doe/journal.log<br>C5/COMPILE_REMOTE/test/LOGS/john.doe/grades.log<br>C5/COMPILE_REMOTE/test/MEDIA/foo.png<br><span style="color:#BBB">C5/COMPILE_REMOTE/test/questions.py</span><h1>Compile and Load configs</h1><h2>COMPILE_REMOTE/test</h2><pre>make: &#x27;COMPILE_REMOTE/test/questions.js&#x27; is up to date.\n</pre>'

            # Import into another session
            output = send('start Source Journal Grades Media', 'TOTO=XXX')
            assert("Bad compiler" in output)

            output = send('sequential Source Journal Grades Media', 'REMOTE=XXX')
            assert output == '<br>C5/COMPILE_REMOTE/test/session.cf<br>C5/COMPILE_REMOTE/test/LOGS/john.doe/journal.log<br>C5/COMPILE_REMOTE/test/LOGS/john.doe/grades.log<br>C5/COMPILE_REMOTE/test/MEDIA/foo.png<br>C5/COMPILE_REMOTE/test/questions.py<h1>Compile and Load configs</h1><h2>COMPILE_REMOTE/XXX</h2><pre>COMPILE_REMOTE/XXX/questions.py â\x86\x92 COMPILE_REMOTE/XXX/questions.js OK\nCOMPILE_REMOTE/XXX/questions.py â\x86\x92 COMPILE_REMOTE/XXX/questions.json OK\n</pre>'
            
            assert os.path.exists('COMPILE_REMOTE/XXX/questions.py')
            assert os.path.exists('COMPILE_REMOTE/XXX/session.cf')
            assert os.path.exists('COMPILE_REMOTE/XXX/MEDIA/foo.png')
            assert os.path.exists('COMPILE_REMOTE/XXX/LOGS/john.doe/grades.log')
            assert os.path.exists('COMPILE_REMOTE/XXX/LOGS/john.doe/journal.log')
            with open('COMPILE_REMOTE/XXX/session.cf', 'rb') as file:
                content = file.read()
            assert content.count(b'\n') == 2
            assert content.endswith(b"\n('sequential', 1)\n")    
        self.ticket = save_ticket

    def test_manage_reset(self):
        """Test filtered reset"""
        os.system('unzip tests_import.zip ; rm -r COMPILE_REMOTE/XXXXX 2>/dev/null')
        os.rename('C5/COMPILE_REMOTE/test', 'COMPILE_REMOTE/XXXXX')
        os.system('rm -r C5 ; make COMPILE_REMOTE/XXXXX/questions.js')
        # inflating: C5/COMPILE_REMOTE/test/questions.py  
        with self.admin_rights():
            for filename, what, message in (
                    ('MEDIA'                    , 'Media'          , 'Delete all media'),
                    ('LOGS/john.doe/journal.log', 'Journal'        , 'Delete COMPILE_REMOTE/XXXXX/LOGS/john.doe/journal.log'),
                    ('LOGS/john.doe/grades.log' , 'Grades'         , 'Delete COMPILE_REMOTE/XXXXX/LOGS/john.doe/grades.log'),
                    ('LOGS'                     , 'Journal Grades' , 'Delete students works, comments and grades'),
                    ):
                print(f'\tReset {what} {filename}')
                filename = f'COMPILE_REMOTE/XXXXX/{filename}'
                assert os.path.exists(filename)
                self.goto(f'adm/reset/REMOTE=XXXXX/{what}')
                assert not os.path.exists(filename)
                self.check('BODY', {'innerHTML': Contains(message) & ~Contains('BUG')})

            self.goto('adm/reset/REMOTE=XXXXX/start')
            self.check('BODY', {
                'innerHTML': Contains("Reset config attributes ['start']") & ~Contains('BUG')})
            with open('COMPILE_REMOTE/XXXXX/session.cf', 'rb') as file:
                content = file.read()
            assert b"('start', '2000-01-01 00:00:00'" in content
            assert b"('active_teacher_room', 'thi\xc3\xa9rry.excoffier'," in content

            self.goto('checkpoint/REMOTE=XXXXX')
            self.check('BODY', {'innerHTML': Contains('id="timetravel')})
            retry(lambda:
                list(self.driver.execute_script("return STUDENT_DICT")) != ['thiérry.excoffier'])

            self.goto('adm/reset/REMOTE=XXXXX/active_teacher_room state start')
            self.check('BODY', {
                'innerHTML': Contains("Reset config attributes ['active_teacher_room']") & ~Contains('BUG')})
            with open('COMPILE_REMOTE/XXXXX/session.cf', 'rb') as file:
                content = file.read()
            assert b"'active_teacher_room'" not in content

            self.goto('=REMOTE=XXXXX')
            self.check('BODY', {'innerHTML': Contains('COURSE_CONFIG') & ~Contains('BUG')})
            config = self.driver.execute_script("return COURSE_CONFIG")
            assert config['start'] == '2000-01-01 00:00:00'

            self.goto('checkpoint/REMOTE=XXXXX')
            self.check('BODY', {'innerHTML': Contains('id="timetravel')})
            retry(lambda: 'thiérry.excoffier' in self.driver.execute_script("return STUDENT_DICT"))

    def screenshots(self):
        """Dump screen shots"""
        self.goto('')
        self.driver.save_screenshot("xxx-home-student.png")
        self.goto('=JS=introduction')
        self.check('.executor', {'innerHTML': Contains('suis un texte')})
        self.driver.save_screenshot("xxx-try-student.png")

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
    XNEST = subprocess.Popen( # pylint: disable=consider-using-with
        X11, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    print(X11)
    os.environ['DISPLAY'] = PORT
except FileNotFoundError:
    print(f"«{X11}» not found: run directly on your screen")
    XNEST = None

TESTS = None
try:
    EXIT_CODE = 1
    while True:
        if not IN_DOCKER and 'FF' not in sys.argv and 'screenshots' not in sys.argv:
            OPTIONS = selenium.webdriver.ChromeOptions()
            OPTIONS.add_argument('ignore-certificate-errors')
            OPTIONS.add_argument('--password-store=basic')
            OPTIONS.add_argument('--use-mock-keychain')
            TESTS = Tests(selenium.webdriver.Chrome(options=OPTIONS))
            TESTS.run()
            TESTS = None

        PROFILE = selenium.webdriver.FirefoxProfile()
        PROFILE.set_preference("browser.download.dir", "/path/to/download_directory")  # Set your download directory
        PROFILE.set_preference("browser.download.folderList", 2)
        PROFILE.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")  # Avoid the download panel

        OPTIONS = selenium.webdriver.firefox.options.Options()
        OPTIONS.accept_untrusted_certs = True
        OPTIONS.set_preference("browser.download.panel.shown", False)
        OPTIONS.set_preference("browser.download.manager.showWhenStarting", False)
        OPTIONS.set_preference('browser.download.manager.showAlertOnComplete', False)
        OPTIONS.set_preference("browser.download.manager.closeWhenDone", True)
        OPTIONS.set_preference("browser.download.alwaysOpenPanel", False)
        OPTIONS.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
        OPTIONS.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
        OPTIONS.profile = PROFILE

        TESTS = Tests(selenium.webdriver.Firefox(options=OPTIONS))
        TESTS.run()
        TESTS = None
        if '1' in sys.argv or 'screenshots' in sys.argv:
            # Exit after one test
            EXIT_CODE = 0
            break
        os.system('find . -name "Anon_*" -exec rm -r {} +')
except KeyboardInterrupt:
    log('^C')
except: # pylint: disable=bare-except
    log(traceback.format_exc().strip().replace('\n', '\n\t'))
    traceback.print_exc()
    if 'nosleep' not in sys.argv:
        time.sleep(10000)
finally:
    if TESTS:
        try:
            TESTS.driver.close()
            TESTS.driver.quit()
        except:
            pass
    if XNEST:
        XNEST.terminate()
    os.system('./127 stop')
    os.system('./clean.py')
    sys.exit(EXIT_CODE)
