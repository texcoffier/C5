# The following options are used only when the session is created.
# One created, you must edit interactivly the session parameters.
COURSE_OPTIONS = {
            'title': 'Test Rust',
            'compiler': 'cargo',
            'state': 'Ready',
            'checkpoint': 0,
            'allow_copy_paste': 1,
            'positions' : {
                'question': [1, 28, 0, 30, '#EFE'],
                'tester': [1, 28, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [70, 30, 0, 30, '#EEF'],
                'executor': [70, 30, 30, 70, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                }
            }
class Q1(Question):
    def question(self):
        return "Voici l'énoncé du premier test sur la compilation et l'execution de Rust sur C5"
    def default_answer(self):
        return """
fn main() {
    println!("Hello World!");
}
"""