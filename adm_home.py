
def display():
    """Create the admin home page"""
    document.title = "C5 " + COURSE
    students = []
    for student in STUDENTS:
        students.append(student)
    students.sort()
    text = []
    for student in students:
        text.append('<p>' + student)
        for filename in STUDENTS[student].files:
            text.append(' <a target="_blank" href="adm_get/' + COURSE + '/')
            text.append(student)
            text.append('/')
            text.append(filename)
            text.append(window.location.search)
            text.append('">')
            text.append(filename)
            text.append('</a>')
    document.body.innerHTML = text.join('')



display()

"""
String student.http_server =
[1656599644,"course_js.js","Question=0",5,"MouseDown","Enter",279,"Control"]
[1656599929,"course_js.js","Question=0",97,"Control"]
"""