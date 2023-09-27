
FEEDBACK_LEVEL = {
    0: "Rien",
    1: "Code source",
    # 2:  "+ correction"
    3: "+ commentaires correcteur",
    4: "+ note totale",
    5: "+ barème détaillé"
}

DEFAULT_COURSE_OPTIONS = [
    "Frame screen position",

    ['positions', {
        'question':    [ 1, 29, 0, 30,'#EFEF'], # LeftTop    : The question
        'tester':      [ 1, 29,30, 70,'#EFEF'], # LeftBottom : Goal checker
        'editor':      [30, 40, 0,100,'#FFFF'], # Middle     : Source editor
        'compiler':    [70, 30, 0, 30,'#EEFF'], # RightTop   : Compiler messages
        'executor':    [70, 30,30, 70,'#EEFF'], # RightBottom: Execution messages
        'time':        [80, 20,98,  2,'#0000'], # BottomRight: Debugger for admin
        'index':       [ 0,  1, 0,100,'#0000'], # Left       : Thin table of content
        'editor_title':[0 ,  0, 0,  0,'#FFFF'], # Only the color is used.
    }, "For each bloc : [Bloc X%, Width%, Y%, Heigth%, background color]"],

    "Titles, label and messages",

    ['forbiden', "Coller du texte copié venant d'ailleurs n'est pas autorisé.", "Alert"],
    ['close', "Voulez-vous vraiment quitter cette page ?", "Alert"],
    ['question_title', 'Question', "Bloc title"],
    ['editor_title', 'Code source', "Bloc title"],
    ['editor_indent', 'Indent(F8)', "Button label"],
    ['tester_title', 'Les buts que vous devez atteindre', "Bloc title"],
    ['compiler_title', 'Compilation', "Bloc title"],
    ['compiler_title_toggle', 'Automatique (F9)', "Button label"],
    ['compiler_title_button', 'Maintenant ! (F9)', "Button label"],
    ['executor_title_button', 'GO!(F9)', "Button label"],
    ['executor_title', 'Exécution', "Bloc title"],
    ['good', ["Bravo !", "Excellent !", "Super !", "Génial !", "Vous êtes trop fort !"], "Alert on success"],
    ['icon_home', '🏠', "Button label"],
    ['icon_save', '📩', "Button label"],
    ['icon_local', '💾', "Button label"],
    ['icon_git', '<b style="font-size:50%">GIT</b>', "Button label"],
    ['icon_tag', 'TAG', "Button label"],
    ['icon_stop', 'Terminer<br>Examen', "Button label displayed if checkpoint"],
    ['stop_confirm', "Vous voulez vraiment terminer l'examen maintenant ?", "Alert"],
    ['stop_done', "<h1>C'est fini.</h1>", "Alert"],
    ['time_running', 'Fini dans', "Time message"],
    ['time_done', "Fini depuis", "Time message"],
    ['time_seconds', " secondes", "Time message"],
    ['time_days', " jours", "Time message"],
    ['time_d', " j ", "Time message"],
    ['time_m', " m ", "Time message"],
    ['time_h', " h ", "Time message"],

    "Default compiler and session options",

    ['allow_copy_paste',     1, "copy/paste allowed"],
    ['save_unlock',          0, "saving a question unlock next"],
    ['coloring',             1, "source highlighting is done"],
    ['display_local_save',   0, "question 'icon_local' displayed"],
    ['display_home',         1, "display 'icon_home'"],
    ['display_local_git',    1, "question 'icon_git' displayed"],
    ['display_local_zip',    1, "question 'icon_local' displayed"],
    ['display_timer',        1, "the timer is displayed"],
    ['display_compile_run',  1, "display the F9 button"],
    ['display_tag',          1, "display 'icon_tag'"],
    ['display_history',      1, "display version history"],
    ['display_indent',       1, "display the F8 button"],
    ['display_line_numbers', 0, "display line numbers"],
    ['automatic_compilation',True,"compilation is automatic"],

    "Options defined by the compiler used",

    ['compiler', '',        "'g++' 'gcc' 'racket'"],
    ['compile_options', [], "'-Wall' '-pedantic' '-pthread' '-std=c++11' '-std=c++20'"],
    ['ld_options', [],      "'-lm'"],
    ['language', '',        "Language to use for syntaxic coloring: 'cpp' 'python' ..."],
    ['extension', '',       "Source code filename extension for ZIP and GIT: 'cpp', 'py'..."],
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
"""]
]
