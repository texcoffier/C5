
FEEDBACK_LEVEL = {
    0: "Rien",
    1: "Code source",
    # 2:  "+ correction"
    3: "+ commentaires correcteur",
    4: "+ note totale",
    5: "+ barème détaillé"
}

DEFAULT_COURSE_OPTIONS = [

    "Session options",

    ['start'                ,'2000-01-01 00:00:00', "Start date of the session"],
    ['stop'                 ,'2100-01-01 00:00:00', 'Stop date of the session <div id="invalid_date">START&gt;END</div>'],
    ['state'                ,'Draft', """
<pre>┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
┃ State  ┃    Visible by      ┃    Usable by       ┃
┣━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
┃Draft   ┃creator admin       │creator admin       │
┣━━━━━━━━╉────────────────────┼────────────────────┤
┃Ready   ┃                    │                    │
┃  before┃all                 │creator admin grader│
┃  while ┃all                 │all if no checkpoint│
┃  after ┃all except students │creator admin grader│
┣━━━━━━━━╉────────────────────┼────────────────────┤
┃Grade   ┃creator admin grader│creator admin grader│
┣━━━━━━━━╉────────────────────┼────────────────────┤
┃Done    ┃creator admin grader│creator admin grader│
┃        ┃Students if allowed │                    │
┃        ┃by admin and grader │                    │
┣━━━━━━━━╉────────────────────┼────────────────────┤
┃Archive ┃creator admin       │creator admin       │
┗━━━━━━━━┹────────────────────┴────────────────────┘</pre>"""],
    ['checkpoint'           ,0, "Requires students to be placed on the map (examination mode)"],
    ['allow_copy_paste'     ,0, "Copy/paste allowed (if not allowed students must be in full screen mode)"],
    ['save_unlock'          ,0, "Saving a question unlock next"],
    ['automatic_compilation',1, "Compilation is automatic"],
    ['feedback'             ,0, "Maximum level of student feedback allowed to teachers"],
    ['allow_ip_change'      ,0, "Allow IP change (bad Internet connection)"],
    ['sequential'           ,1, "Questions must be answered from first to last"],
    ['highlight'            ,"#FFF", "Background color in the student and teacher session list"],

    "Checkpoint placement interface",

    ['display_student_filter', 0, "Display an INPUT field containing a list of student IDs to highlight"],
    ['display_my_rooms'      , 1, "Add a toggle to display only the rooms I dragged student into"],
    ['display_session_name'  , 0, "Display the session name"],
    ['default_building'      ,'', "Preselected building name"],

    "Student interface",

    ['positions', {
        'question':    [ 1, 29, 0, 30,'#EFEF'], # LeftTop    : The question
        'tester':      [ 1, 29,30, 70,'#EFEF'], # LeftBottom : Goal checker
        'editor':      [30, 40, 0,100,'#FFFF'], # Middle     : Source editor
        'compiler':    [70, 30, 0, 30,'#EEFF'], # RightTop   : Compiler messages
        'executor':    [70, 30,30, 70,'#EEFF'], # RightBottom: Execution messages
        'time':        [80, 20,98,  2,'#0000'], # BottomRight: Debugger for admin
        'index':       [ 0,  1, 0,100,'#0000'], # Left       : Thin table of content
        'editor_title':[0 ,  0, 0,  0,'#FFFF'], # Only the color is used.
    }, "For each bloc :<br>[Bloc X%, Width%, Y%, Heigth%, background color]"],

    ['coloring',             1, "source highlighting is done"],
    ['theme',                'a11y-light', "Syntaxic coloring theme for source code"],
    ['display_local_save',   0, "display 'icon_local' to download the current source code"],
    ['display_home',         1, "display 'icon_home'"],
    ['display_local_git',    1, "display 'icon_git' to download a repository of all history"],
    ['display_local_zip',    1, "display 'icon_local' to download a repository of all questions"],
    ['display_timer',        1, "display the timer"],
    ['display_compile_run',  1, "display the F9 button"],
    ['display_tag',          1, "display 'icon_tag'"],
    ['display_history',      1, "display version history"],
    ['display_indent',       1, "display the F8 button"],
    ['display_line_numbers', 1, "display line numbers"],

    "Popup messages",

    ['forbiden', "Coller du texte copié venant d'ailleurs n'est pas autorisé.", "Alert"],
    ['close', "Voulez-vous vraiment quitter cette page ?", "Alert"],
    ['stop_confirm', "Vous voulez vraiment terminer l'examen maintenant ?", "Alert"],
    ['stop_done', "<h1>C'est fini.</h1>", "Alert"],
    ['good', ["Bravo !", "Excellent !", "Super !", "Génial !", "Vous êtes trop fort !"], "Alert on success"],

    "Bloc titles",

    ['question_title', 'Question', "Bloc title"],
    ['tester_title', 'Les buts que vous devez atteindre', "Bloc title"],
    ['editor_title', 'Code source', "Bloc title"],
    ['compiler_title', 'Compilation', "Bloc title"],
    ['executor_title', 'Exécution', "Bloc title"],

    "Labels of button and toggles",

    ['editor_indent', 'Indent(F8)', "Button label"],
    ['compiler_title_toggle', 'Automatique (F9)', "Button label"],
    ['compiler_title_button', 'Maintenant ! (F9)', "Toggle label"],
    ['executor_title_button', 'GO!(F9)', "Button label"],
    ['icon_home', '🏠', "Button label"],
    ['icon_save', '📩', "Button label"],
    ['icon_local', '💾', "Button label"],
    ['icon_git', '<b style="font-size:50%">GIT</b>', "Button label"],
    ['icon_tag', 'TAG', "Button label"],
    ['icon_stop', 'Terminer<br>Examen', "Button label displayed if checkpoint"],

    "Time countdown",

    ['time_running', 'Fini dans', "Time message"],
    ['time_done', "Fini depuis", "Time message"],
    ['time_seconds', " secondes", "Time message"],
    ['time_days', " jours", "Time message"],
    ['time_d', " j ", "Time message"],
    ['time_m', " m ", "Time message"],
    ['time_h', " h ", "Time message"],

    "Options defined by the compiler used by the course",

    ['compiler', '',        "Compiler to use (should not be changed):<br>«g++» «gcc» «racket»"],
    ['compile_options', [], "Compile options:<br>«-Wall» «-pedantic» «-pthread» «-std=c++11» «-std=c++20»"],
    ['ld_options', [],      "Libraries to link with:<br>«-lm»"],
    ['language', '',        "Language to use for syntaxic coloring:<br> «cpp» «python» ..."],
    ['extension', '',       "Source code filename extension for ZIP and GIT: «cpp», «py»..."],
    ['filetree_in', [],     "Initialize file tree [['foo', 'content'], ['BAR/1', 'one']]"],
    ['filetree_out', [],    "File contents to get as ['foo', 'BAR/1']"],
    ['allowed', [], """
System call always allowed for g++/gcc, no need to specify them:
      clock_gettime close exit exit_group fstat futex lseek
      mmap munmap newfstatat openat read write
<p>
System calls allowable for g++/gcc:
      access arch_prctl brk clock_nanosleep
      clone clone3 execve getpid getrandom gettid madvise mprotect
      pipe pread64 prlimit64 rseq rt_sigaction rt_sigprocmask
      sched_yield set_robust_list set_tid_address tgkill open
"""],

    "Access tab",

    ['admins', '', 'Administrators with all the access rights'],
    ['graders', '', 'Teachers allowed to try the session, grade and place the students'],
    ['proctors', '', 'Can only place the students'],
    ['expected_students', '', 'The login list of expected students, the session is in bold in their session list.'],
    ['expected_students_required', 0, 'Unexpected students do not see the session, but a teacher can send them the link to it'],
    ['tt', '', 'The logins of student with ⅓ more time'],
]
