"""
Do nothing compiler
"""

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """Do nothing compiler and evaluator"""
    def init(self):
        """Initialisations"""
        self.set_options(
            {'coloring': False,
             'positions' : {
                'question': [1, 46, 0, 30, '#EFE'],
                'tester': [1, 46, 30, 70, '#EFE'],
                'editor': [50, 50, 0, 100, '#FFF'],
                'compiler': [100, 30, 0, 30, '#EEF'],
                'executor': [100, 30, 30, 70, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                'line_numbers': [49, 1, 0, 100, '#EEE']
            }})
