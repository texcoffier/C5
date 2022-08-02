"""
Display checkpoint page
"""
try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    LOGIN = LOGIN
    COURSE = COURSE
    STUDENTS = STUDENTS
    document = document
except ValueError:
    pass

class Student: # pylint: disable=too-many-instance-attributes
    """To simplify code"""
    def __init__(self, data):
        self.login = data[0]
        self.active = data[1][0]
        self.teacher = data[1][1]
        self.room = data[1][2]
        self.checkpoint_time = data[1][3]
        self.firstname = data[2]['fn']
        self.surname = data[2]['sn']
        self.sort_key = self.surname + '\001' + self.firstname + '\001' + self.login

    def box(self, room):
        """A nice box clickable and draggable"""
        return ''.join([
            '<div class="name" onclick="location = \'/checkpoint/',
            COURSE, '/', self.login, '/', room, '?ticket=', TICKET, '\'">',
            '<span>', self.login, '</span>',
            '<div>', self.firstname, '</div>',
            '<div>', self.surname, '</div>',
            '<span>', self.room, '</span>',
            '</div>'])

    def with_me(self):
        """The student is in my room"""
        return self.teacher == LOGIN and self.active

def cmp_student(student_a, student_b):
    """Compare 2 students names"""
    if student_a.sort_key > student_b.sort_key:
        return 1
    return -1

STUDENTS = [Student(student) for student in STUDENTS if student[0]]
STUDENTS.sort(cmp_student)

def create_page():
    """Fill the page content"""
    content = ['<h1>', COURSE, '</h1>', '''
            <style>
            .name { display: inline-block; background: #EEE; vertical-align: top; cursor: pointer }
            .name:hover { background: #DFD }
            .name SPAN { color: #888 }
            </style>
            <p>Student waiting:
            ''']
    for student in STUDENTS:
        if not student.with_me():
            content.append(' ')
            content.append(student.box('A_room'))
    content.append('<p>Your students:')
    for student in STUDENTS:
        if student.with_me():
            content.append(' ')
            content.append(student.box('STOP'))
    document.body.innerHTML = ''.join(content)

create_page()
