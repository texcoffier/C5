
FEEDBACK_LEVEL = {
    0: "Rien",
    1: "Code source commenté",
    # 2:  "+ correction"
    # 3: "+ commentaires correcteur",
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
    ['display_media_list'   ,0, "Add a media menu 📷 in the source editor title bar"],
    ['save_unlock'          ,0, "Saving a question unlock next"],
    ['automatic_compilation',0, "Compilation is done on any little source change"],
    ['feedback'             ,0, "Maximum level of student feedback allowed to teachers"],
    ['grading_done'         ,1, "Graders indicate «grading done» in place of the grading level"],
    ['force_grading_done'   ,0, "Consider all gradings done even if graders did not approve"],
    ['feedback_for_all'     ,0, "Allow an empty feedback (with the examination questions) to students who did not attend to the session"],
    ['sequential'           ,1, "Questions must be answered from first to last"],
    ['git_url'              ,'', "The GIT url to fetch updates. <b>You must only commit 'questions.py' and 'MEDIA/*' nothing else.</b>"],
    ['key_stats'            ,'', 'API key for statistics (ID #good #lines):<br>https://.../adm/stats/COMPILER=session_name/API_key'],

    'Set <button onclick="exam_mode(1)" style="font-size:100%">Examination</button> or <button onclick="exam_mode(0)" style="font-size:100%">Course</button> modes for attributes:',

    ['checkpoint'           ,1, "Requires students to be placed on the map (examination mode)"],
    ['allow_copy_paste'     ,0, "Copy/paste allowed (if not allowed students must be in full screen mode)"],
    ['forbid_question_copy' ,1, "Forbid text selection in questions"],
    ['allow_ip_change'      ,0, "Allow IP change (bad Internet connection)"],

    "Checkpoint placement interface",

    ['display_student_filter', 0, "Display an INPUT field containing a list of student IDs to highlight"],
    ['display_my_rooms'      , 1, "Add a toggle to display only the rooms I dragged student into"],
    ['display_session_name'  , 1, "Display the session name"],
    ['default_building'      ,'', "Preselected building name"],

    "Student session list",

    ['highlight'            ,"#FFF", "Background color in the student and teacher session list"],
    ['hide_before'          ,24*15., """The session will be visible in the list if it starts
    in less than the number of indicated hours. 15 days = 360 hours, 6 minutes = 0.1 hours"""],
    ['title'                ,''    , "Session title"],

    "Student interface for the editor",

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

    ['forget_input',         0, "Forget old input values on execution"],
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
    ['display_grading',      1, "display grading interface"],
    ['display_global_grading',0, "display the buttons to set all grades to min or max"],
    ['diff',                 1, "Green line numbers for student inserted lines (togglable by clicking on line numbers)"],
    ['diff_original',        0, "The above diff is with the original version not the last saved."],
    ['version_for_teachers', 1, "Display version tree to teachers"],
    ['version_for_students', 0, "Display version tree to students"],
    ['display_version_toggle',1,"Display the toggle to hide/display version tree"],

    "Popup messages",

    ['forbiden', "Coller du texte copié venant d'ailleurs n'est pas autorisé.", "Alert"],
    ['stop_confirm', "Vous voulez vraiment terminer l'examen maintenant ?", "Alert"],
    ['stop_done', "<h1>C'est fini.</h1>", "Alert"],
    ['good', ["Bravo !", "Excellent !", "Super !", "Génial !", "Vous êtes trop fort !"], "Alert on success"],

    'Keyboard coach <b style="color:#F00">EXPERIMENTAL DO NOT ACTIVATE</b>',

    ['coach_tip_level',              1, "Conseils du coach (0: Désactivé, 1: Activé)"],
    ['coach_cooldown',            5000, "Délai minimum entre deux conseils en millisecondes (5000ms = 5 secondes)"],
    ['coach_mouse_short_move',       0, "Détecter les petits déplacements souris et suggérer les flèches clavier."],
    ['coach_mouse_short_move_chars', 5, "Nombre maximum de caractères pour déplacement horizontal (défaut: 5)"],
    ['coach_mouse_short_move_drift', 3, "Écart maximum de colonnes pour déplacement vertical (défaut: 3)"],
    ['coach_mouse_line_bounds',      0, "Alerter quand la souris est utilisée pour aller au début/fin de ligne au lieu de Home/End."],
    ['coach_retype_after_delete',    0, "Suggérer Ctrl+Z/Ctrl+Y lorsqu'un texte long supprimé est retapé à l'identique."],
    ['coach_retype_after_delete_chars', 10, "Nombre minimum de caractères identiques retapés (défaut: 10)"],
    ['coach_many_horizontal_arrows', 0, "Rappeler Ctrl+←/→ ou Home/End après de nombreuses flèches gauche/droite consécutives."],
    ['coach_many_horizontal_arrows_count', 15, "Nombre de flèches consécutives avant conseil (défaut: 15)"],
    ['coach_arrow_then_backspace',   0, "Signaler la séquence → puis Backspace pour proposer la touche Suppr."],
    ['coach_many_vertical_arrows',   0, "Suggérer PgUp/PgDn ou Ctrl+Home/End après de nombreuses flèches haut/bas."],
    ['coach_many_vertical_arrows_count', 10, "Nombre de flèches consécutives avant conseil (défaut: 10)"],
    ['coach_scroll_full_document',   0, "Rappeler Ctrl+Home/End quand l'étudiant atteint le début/la fin via un long défilement."],
    ['coach_scroll_full_document_edge_lines', 3, "Nombre de lignes près du bord pour détecter début/fin (défaut: 3)"],
    ['coach_scroll_full_document_min_lines', 30, "Nombre minimum de lignes dans le fichier pour activer (défaut: 30)"],
    ['coach_letter_select_word',     0, "Inviter au double-clic ou Ctrl+Shift+flèches lorsqu'un mot est sélectionné lettre par lettre."],
    ['coach_letter_select_word_min_chars', 8, "Nombre minimum de caractères sélectionnés consécutivement pour détecter (défaut: 8)"],
    ['coach_delete_word_char_by_char', 0, "Suggérer Ctrl+Backspace/Delete lorsqu'un mot est supprimé caractère par caractère."],
    ['coach_delete_word_char_by_char_count', 5, "Nombre de suppressions consécutives avant conseil (défaut: 5)"],
    ['coach_copy_then_delete', 0, "Suggérer Ctrl+X (couper) lorsque l'étudiant copie puis supprime au lieu d'utiliser directement Ctrl+X."],

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
    ['icon_version_toggle', '<span style="font-family:emoji">🌳</span>', "Button label"],

    "Time countdown",

    ['time_running', 'Fini dans', "Time message"],
    ['time_done', "Fini depuis", "Time message"],
    ['time_seconds', " secondes", "Time message"],
    ['time_days', " jours", "Time message"],
    ['time_d', " j ", "Time message"],
    ['time_m', " m ", "Time message"],
    ['time_h', " h ", "Time message"],

    "Options defined by the compiler used by the course",

    ['compiler', '',        "Compiler to use (should not be changed):<br>«g++» «gcc» «racket» «coqc» «prolog»"],
    ['compile_options', [], "C Compile options:<br>«-Wall» «-pedantic» «-pthread» «-std=c++11» «-std=c++20»"],
    ['ld_options', [],      "C Libraries to link with:<br>«-lm»"],
    ['language', '',        "Language to use for syntaxic coloring:<br> «cpp» «python» «coq»..."],
    ['extension', '',       "Source code filename extension for ZIP and GIT: «cpp», «py», «v»..."],

    "Running parameters",

    ['max_time', 1,         "Maximum CPU time allowed between 1 and 10 seconds"],
    ['max_data', 200000,    "Maximum number of kilo-bytes transfered (no more than 200_000KB)"],
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
    ['proctors', '', 'Proctors can only place the students'],
    ['expected_students', '', 'The login list of expected students, if not empty only listed students may see the session on their C5 home page.'],
    ['tt', '', 'The logins of student with ⅓ more time'],
]
