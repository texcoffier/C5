"""An editor for grading ladder"""

COURSE_OPTIONS = {
    'title': "Session utilisée uniquement pour éditer les barèmes",
    'allow_copy_paste': 1,
    'forbid_question_copy': 0,
    'state': 'Ready',
    'checkpoint': 0,
    'automatic_compilation': 1,
    'expected_students_required': 1, # Do not display to student
    'question_title': 'Explications',
    'tester_title': 'Les points',
    'editor_title': 'Définition du barème',
    'executor_title': 'Le barème affiché',
    'display_indent': 0,
    'positions' : {
        "question":[72,28,0,30,"#EFEF"],
        "tester":[72,28,30,70,"#EFEF"],
        "editor":[36,36,0,100,"#FFFF"],
        "compiler":[100,30,0,30,"#EEFF"],
        "executor":[1,35,0,100,"#FFFF"],
        "time":[81,20,98,2,"#0000"],
        "index":[0,1,0,100,"#0000"]
    }}

class Q1(Question):
    """Nothing"""
    def question(self): # pylint: disable=no-self-use
        """Doc"""
        return """
 If the grading part is:<br>
<tt>{printf:Key:-1,-0.5,0,0.5,1,1.5,2}</tt>
<ul>
    <li> «Key» will be automaticaly added if undefined.
    <li> «Key» uniquely identify the grade,
    <li> «Key» is not displayed to the graders.
    <li> integer «Key» → positive or negative grade.
    <li> text «Key» → it is a competence key<br>

    <ul>
        <li>  if the same competence is evaluated multiple times,
              «'» are appended to the key to remove duplicates.
        <li>  «?» is for «Not Evaluated» and «0» for «Not Acquired».
        <li>  Competences are not used to compute the grade.
    </ul>
</ul>

Each grading definition line found in the student code
is clickable to scroll the student code to the right place.
To disable this, add a '▶' in the lines you want to be clickable. 
        """
    def default_answer(self):
        return """/*
 Example of grading definition for the «hello world».
 The grading is right aligned with one button per grade.
*/

#include <stdio.h>            {stdio.h:0,1}
int main()                    {main declaration:0,1}
{
   printf("Hello World\n");   {printf:0,0.5,1,1.5,2}
}
// Malus                      {No comments:-1,0}

// Is competence «f22» acquired?
// ? : Not Evaluated
// 0 : Not acquired
// 1 : Faiblement acquis
// 2 : Acquis
// 3 : Acquis solidement
// 4 : Acquis au delà des attentes
// {Can make a main:f22:?,0,1,2,3,4}

/*
On save, an identifying key will be automaticaly added
to every grades to allow changing their order.
*/
"""
