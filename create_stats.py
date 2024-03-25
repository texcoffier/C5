"""Global statistics creation and display"""

# pylint: disable=invalid-name,multiple-statements,eval-used

import os
import collections
import traceback
import json

PAUSE_TIME = 10*60 # 10 minutes

class Stat:
    nr_Focus = nr_checkpoint_in = nr_FullScreenEnter = nr_snapshot = \
    nr_checkpoint_ip_change = nr_keypress = nr_deadkey = nr_cursor_movement = \
    nr_save = nr_Blur = nr_checkpoint_move = nr_FullScreenQuit = nr_MouseDown = \
    nr_CopyAllowed = nr_checkpoint_ip_change_eject = nr_answer = nr_checkpoint_eject = \
    nr_Copy = nr_Paste = nr_PasteOk = nr_checkpoint_stop = nr_F8 = nr_CutAllowed = \
    nr_F9 = nr_tag = the_time_bonus = nr_PasteRejected = nr_BUG = nr_checkpoint_restart = \
    nr_Escape = nr_Cut = nr_CopyRejected = nr_CutRejected  = nr_JS = work_time = 0

    first_interaction = 1e100
    last_interaction = 0

    nr_compiles = nr_indents = nr_exit_bad = nr_exit_ok = nr_execs = 0
    nr_compile_without_error = nr_compile_with_error = 0

    def __init__(self):
        self.question_dict = collections.defaultdict(int) # Nr questions see
        self.allow_edit_dict = collections.defaultdict(int) # Nr forbiden actions while compiling
        self.sessions = []
        self.grade = {}

    def allow_edit(self, infos):                  self.allow_edit_dict[infos[1]] += 1
    def answer(self, _infos):                     self.nr_answer += 1
    def ArrowUp(self):                            self.nr_cursor_movement += 1
    def Blur(self):                               self.nr_Blur += 1
    def checkpoint_eject(self, _infos=None):      self.nr_checkpoint_eject += 1
    def checkpoint_in(self, _infos=None):         self.nr_checkpoint_in += 1
    def checkpoint_ip_change_eject(self, _infos): self.nr_checkpoint_ip_change_eject += 1
    def checkpoint_ip_change(self, _infos):       self.nr_checkpoint_ip_change += 1
    def checkpoint_move(self, _infos):            self.nr_checkpoint_move += 1
    def checkpoint_restart(self, _infos):         self.nr_checkpoint_restart += 1
    def checkpoint_stop(self, _infos=None):       self.nr_checkpoint_stop += 1
    def Copy(self):                               self.nr_Copy += 1
    def CopyAllowed(self):                        self.nr_CopyAllowed += 1
    def CopyRejected(self):                       self.nr_CopyRejected += 1
    def Cut(self):                                self.nr_Cut += 1
    def CutAllowed(self):                         self.nr_CutAllowed += 1
    def CutRejected(self):                        self.nr_CutRejected += 1
    def Enter(self):                              self.nr_keypress += 1
    def Escape(self):                             self.nr_Escape += 1
    def F11(self):                                pass
    def F8(self):                                 self.nr_F8 += 1
    def F9(self):                                 self.nr_F9 += 1
    def Focus(self):                              self.nr_Focus += 1
    def FullScreenEnter(self, _infos=None):       self.nr_FullScreenEnter += 1
    def FullScreenQuit(self, _infos=None):        self.nr_FullScreenQuit += 1
    def JS(self, _infos=None):                    self.nr_JS += 1
    def MouseDown(self):                          self.nr_MouseDown += 1
    def null(self):                               pass
    def Paste(self):                              self.nr_Paste += 1
    def PasteOk(self):                            self.nr_PasteOk += 1
    def PasteRejected(self):                      self.nr_PasteRejected += 1
    def question(self, infos):                    self.question_dict[infos[1]] += 1
    def save(self, _infos):                       self.nr_save += 1
    def Shift(self):                              self.nr_deadkey += 1
    def snapshot(self, _infos):                   self.nr_snapshot += 1
    def tag(self, _infos):                        self.nr_tag += 1
    def time_bonus(self, infos):                  self.the_time_bonus = infos[1]
    def BUG(self, _infos):                        self.nr_BUG += 1
    def forget(self, _infos=None):                pass

    Backspace = Tab = Delete = Enter
    Meta = Control = Alt = AltGraph = CapsLock = Super = Insert = Dead = OS = ContextMenu = NumLock = Shift
    PageUp = PageDown = ArrowDown = ArrowLeft = ArrowRight = Home = End = ArrowUp

    Process = Unidentified = click_same = \
    F1 = F2 = F3 = F4 = F5 = F6 = F7 = F10 = F12 = F13 = F14 = F15 = F16 = F17 = F18 = F24 = \
    MediaPlayPause = MediaTrackNext = MediaTrackPrevious = MediaStop = MediaPlay = \
    AudioVolumeDown = AudioVolumeUp = AudioVolumeMute = Pause = \
    LaunchApplication2 = LaunchCalculator = Standby = WakeUp = Help = \
    BrowserSearch = ScrollLock = Clear = Close = Cancel = forget

    # Deprecated
    checkpoint = checkpoint_in

    def parse(self, line_txt):
        try:
            line = iter(eval(line_txt.replace('null', '0')))
            timestamp = next(line)
            if timestamp - self.last_interaction < PAUSE_TIME:
                self.work_time += timestamp - self.last_interaction
                self.last_interaction = timestamp
            else:
                self.sessions.append(timestamp)
            if timestamp < self.first_interaction:
                self.first_interaction = timestamp
            self.last_interaction = timestamp
            for value in line:
                if isinstance(value, int):
                    timestamp += value
                    continue
                if isinstance(value, str):
                    if len(value) == 1:
                        self.Enter()
                    else:
                        if len(value) > 1 and value.startswith(('^', 'ˆ', '¨', '—', '.', '´', '"', '~', '`', 'ft ', 'N ', "'")):
                            continue # Compose key failure
                        getattr(self, value)()
                    continue
                if isinstance(value, list):
                    if isinstance(value[0], str):
                        getattr(self, value[0].replace(' ', '_').replace('-', '_'))(value)
                    else:
                        print('\n', line_txt, end='')
                    continue
            self.work_time += timestamp - self.last_interaction
            self.last_interaction = timestamp
        except:
            print('Unparsable:')
            print(line_txt)
            traceback.print_exc()
            raise

    def parse_compile(self, line_txt):
        line = eval(line_txt)
        if isinstance(line[2], tuple):
            if line[2][0] == 'COMPILE':
                self.nr_compiles += 1
            elif line[2] == ('ACTION', 'indent'):
                self.nr_indents += 1
            elif line[2] == ('ACTION', 'run'):
                self.nr_execs += 1
            if line[2][0] == 'ERRORS':
                if line[2][1] + line[2][2]:
                    self.nr_compile_with_error += 1
                else:
                    self.nr_compile_without_error += 1
            elif line[2][0] == 'EXIT':
                if line[2][1]:
                    self.nr_exit_bad += 1
                else:
                    self.nr_exit_ok += 1

    def parse_grade(self, line_txt):
        line = eval(line_txt)
        self.grade[line[2]] = line[3]

    def __repr__(self):
        self.question_dict = dict(self.question_dict)
        self.allow_edit_dict = dict(self.allow_edit_dict)
        self.nr_sessions = len(self.sessions)
        if self.nr_sessions:
            self.sessions_last = self.sessions[-1]
            self.sessions_average = sum(self.sessions) / len(self.sessions)
            self.sessions_median = self.sessions[len(self.sessions) // 2]
        else:
            self.sessions_last = self.sessions_average = self.sessions_median = -1

        if self.grade:
            self.grade = sum(int(i) for i in self.grade) / len(self.grade)
        else:
            del self.grade
        return repr(self.__dict__)

def compile_stats(courses) -> None:
    """Create a resume for each session stats"""
    full = {}
    for session in courses.values():
        resume_file = f'{session.dir_session}/session.stats'
        if (os.path.exists(resume_file)
            and os.path.getmtime(resume_file) > os.path.getmtime(session.file_cf) - 86400):
            print(f'{session.dir_session} is yet up to date (may be 1 day late)')
            with open(resume_file, 'r', encoding='utf-8') as file:
                full[session.dir_session] = eval(file.read())
            continue
        if not os.path.exists(session.dir_log):
            continue
        print(session.dir_session, end=' ')
        students = collections.defaultdict(Stat)
        for student in os.listdir(session.dir_log):
            print(student, end=' ', flush=True)
            stat = students[student]
            if os.path.exists(session.dir_log + '/' + student + '/http_server.log'):
                with open(session.dir_log + '/' + student + '/http_server.log', 'r',
                        encoding='utf-8') as file:
                    for line in file:
                        stat.parse(line)
            if os.path.exists(session.dir_log + '/' + student + '/compile_server.log'):
                with open(session.dir_log + '/' + student + '/compile_server.log', 'r',
                        encoding='utf-8') as file:
                    for line in file:
                        stat.parse_compile(line)
            if os.path.exists(session.dir_log + '/' + student + '/grades.log'):
                with open(session.dir_log + '/' + student + '/grades.log', 'r',
                        encoding='utf-8') as file:
                    for line in file:
                        stat.parse_grade(line)
        content = repr(dict(students))
        with open(resume_file, 'w', encoding='utf-8') as file:
            file.write(content)
        full[session.dir_session] = eval(content)
        print()
    with open('xxx-full-stats.js', 'w', encoding='utf-8') as file:
        file.write(f'{json.dumps(full)}')
    print(f"xxx-full-stats.js : {os.path.getsize('xxx-full-stats.js')} bytes")
