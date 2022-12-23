# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

COURSE_OPTIONS = {
            'automatic_compilation': False,
            'compile_options': ['-Wall', '-pedantic'],
            'allowed': ['brk', 'clock_nanosleep'],
            'forget_input': True,
            'positions' : {
                'question': [1, 28, 0, 30, '#EFE'],
                'tester': [1, 28, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [70, 30, 0, 30, '#EEF'],
                'executor': [70, 30, 30, 70, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                'line_numbers': [29, 1, 0, 100, '#EEE'],
                }
            }

class Q( Question ): # Let blank space: this is not a question
    def question(self):
        return self.__doc__
    def tester(self):
        self.display("N'hésitez pas à modifier ce programme")

Question = Q

class Q1(Question): # pylint: disable=undefined-variable
    """Tuto 1 : Rectangles et textes"""
    def default_answer(self):
        return r"""// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 300;

int main() {
    int i;
    winInit("Titre inutilisé dans C5.", DIMW, DIMW);
    backgroundColor(100, 80, 200);
    fontSize(40);
    for(i=0; i<20; ++i) {
        winClear();          // Clear the windows
        color(234, 129, 34); // Define the pen default color
        // draw a rectangle from (xmin, ymin) to (xmax, ymax)
        rectangleFill(i*10, i*10, i*10 + 100, i*10 + 100);
        color(128, 255, 128);
        print(DIMW - i*10, i*10, "Oh!");
        winDisplay();        // Display the window
        delay(20);
    }
    for(i=0; i<20; ++i)
    {
        winClear();
        color(234, 129, 34);
        rectangleFill(DIMW - i*10      , i*10,
                      DIMW - i*10 + 100, i*10 + 100);
        color(120, 200, 34);
        print(i*10, i*10, "Ah!");
        winDisplay();
        delay(20);
    }
    pressSpace();
    winQuit();
    return 0;
}
"""

class Q2(Question): # pylint: disable=undefined-variable
    """Tuto 2 : Carré centrés"""
    def default_answer(self):
        return r"""// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 300;

struct Data
{
    int n;
};

void init(Data &d)
{
    d.n = 20;
}

void draw(Data &d)
{
    int i;
    for(i=0; i < d.n; i++)
    {
        color(10*i, 255-10*i, 128);
        rectangle(DIMW/2 - 10*i, DIMW/2 - 10*i,
                  DIMW/2 + 10*i, DIMW/2 + 10*i);
    }
}

int main(int, char**)
{
    Data dat;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor(100, 50, 200);
    winClear();
    draw(dat);
    winDisplay();
    pressSpace();
    winQuit();
    return 0;
}
"""

class Q3(Question): # pylint: disable=undefined-variable
    """Tuto 3 : Divers"""
    def default_answer(self):
        return r"""// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 300;

struct Data
{
    int n;
    // Image im; // Les images ne fonctionnent pas dans C5
};
void init(Data &d)
{
    d.n = 10;
    // d.im = image("data/grapic.jpg");
}

void draw(Data &d)
{
    color(255, 0, 0); // Rectangle rouge
    rectangle(10, 10, DIMW/2 - 30, DIMW/2 - 30);

    color(0, 255, 0); // Rectangle vert plein
    rectangleFill(DIMW/2 + 30, 10, DIMW - 10, DIMW/2 - 30);

    color(0, 0, 255); // Disque bleu central
    circleFill(250, 250, 20);
    color(255, 255, 128); // Cercle Jaune central
    circle(250, 250, 30);

    color(0, 255, 255); // Ligne cyan en haut à droite
    line(DIMW/2 + 30, DIMW/2 + 30, DIMW - 10, DIMW - 10);

    color(255, 0, 255); // Grille de 3 colonnes et 5 lignes.
    grid(10, DIMW - 10, DIMW/2 - 30, DIMW/2 + 30, 3, 5);

    triangle(20, 20,  40, 30,  30, 50);
    triangleFill(50, 50,  80, 60,  70, 90);

    int p[5][2] = { {100, 100},
                    {120, 100},
                    {140, 130},
                    {130, 150},
                    {120, 170}
                  };
    polygon(p, 5);

    int p2[5][2] = { {150, 150},
                     {170, 150},
                     {190, 180},
                     {180, 200},
                     {170, 220} 
                   };
    polygonFill(p2, 5);

    color(200,123,200);
    ellipse(350, 450, 40, 20);
    color(200, 123, 100);
    ellipseFill(400, 300, 20, 40);

    // image_draw(d.im, 335, 65, 100, 100);
}

int main(int, char** )
{
    Data dat;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor(100, 50, 200);
    winClear();
    draw(dat);
    winDisplay();
    pressSpace();
    winQuit();
    return 0;
}
"""


class Q4(Question): # pylint: disable=undefined-variable
    """Tuto 4 : Clavier"""
    def default_answer(self):
        return r"""// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 370;

struct Data
{
    int frame; // Number of screen display
    int n;     // Number of squares to display
    int x, y;  // Center of the squares
    int quit;  // If != 0 exit
};
void init(Data &d)
{
    d.frame = 0;
    d.n = 10;
    d.x = d.y = DIMW / 2;
    d.quit = 0;
}

void draw(Data &d)
{
    int i;
    char frame[999];
    if (isKeyPressed(SDLK_UP))         d.y += 3;
    if (isKeyPressed(SDLK_DOWN))       d.y -= 3;
    if (isKeyPressed(SDLK_RIGHT))      d.x += 3;
    if (isKeyPressed(SDLK_LEFT))       d.x -= 3;
    if (isKeyPressed('+') && d.n < 20) d.n++;
    if (isKeyPressed('-') && d.n > 1)  d.n--;
    if (isKeyPressed('q'))             d.quit = 1;
    for(i=1; i<=d.n; i++)
    {
        color(10*i, 255-10*i, 28);
        rectangle(d.x - 10*i, d.y - 10*i,
                  d.x + 10*i, d.y + 10*i);
    }
    sprintf(frame, "Frame=%d n=%d Key=%s",
            d.frame++, d.n, current_key);
    fontSize(20);
    color(255, 255, 255);
    print(20, 20, frame);
    print(20, 50, "Use left/right/up/down keys or +|-|q key");
}

int main(int, char** )
{
    Data dat;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor(100, 50, 200);
    while( !dat.quit )
    {
        winClear();
        draw(dat);
        winDisplay();
    }
    winQuit();
    return 0;
}
"""

class Q5(Question): # pylint: disable=undefined-variable
    """Tuto 5: Souris"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 370;

const int RIEN     = 0; // Aucun rectangle
const int EN_COURS = 1; // Sélection en cours
const int TERMINEE = 2; // Sélection terminée

struct Data
{
    int x1, y1; // Premier point
    int x2, y2; // Deuxième point
    int etat; // RIEN ou EN_COURS ou TERMINEE
};

void init(Data &d)
{
    d.etat = RIEN;
}

void draw(Data &d)
{
    color(255, 255, 0);
    fontSize(14);
    int x, y;
    if (isMousePressed(SDL_BUTTON_LEFT))
    {
        mousePos(x, y);
        if (d.etat != EN_COURS)
        {
            d.etat = EN_COURS;
            d.x1 = x;
            d.y1 = y;
        }
        d.x2 = x;
        d.y2 = y;
    }
    else
    {
        if (d.etat == EN_COURS)
            d.etat = TERMINEE;
    }
    if (d.etat != RIEN)
    {
        color(255, 255, 128);
        rectangle(d.x1, d.y1, d.x2, d.y2);
    }
    color(255, 255, 255);
    print(10, 10, "Press the left mouse button and drag the mouse to draw a square");
    print(10, 480, "mouseXYGlobal=");
    mousePosGlobal(x, y);
    print(150, 480, x);
    print(180, 480, y);
}

int main(int , char** )
{
    Data dat;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor(100, 50, 200);
    do
    {
        winClear();
        draw(dat);
    }
    while(!winDisplay());
    winQuit();
    return 0;
}
'''

class Q6(Question): # pylint: disable=undefined-variable
    """Tuto 6 : Menu"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 370;

struct Data
{
    int n;
};

void init(Data &d)
{
    d.n = 10;
}

void draw(Data &d)
{
    int i;
    for(i=0; i <= d.n; i++)
    {
        color(10*i, 255 - 10*i, 128);
        rectangle(DIMW/2 - 10*i, DIMW/2 - 10*i,
                  DIMW/2 + 10*i, DIMW/2 + 10*i);
    }
}

int main(int, char**)
{
    Data dat;
    Menu m;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor( 100, 50, 200 );
    menu_add(m, "5 carrés");
    menu_add(m, "15 carrés");
    menu_add(m, "10 carrés");
    menu_add(m, "20 carrés");
    //menu_add_toggle( m, "Choix ")

    do
    {
        winClear();
        menu_draw(m, 5, 5,  100, 102);
        switch(menu_select(m))
        {
        case 0 : dat.n = 5 ; break;
        case 1 : dat.n = 15; break;
        case 2 : dat.n = 10; break;
        case 3 : dat.n = 20; break;
        }
        draw(dat);
    }
    while(! winDisplay());
    winQuit();
    return 0;
}
'''

class Q7(Question): # pylint: disable=undefined-variable
    """Tuto 7 : Animation"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int DIMW = 370;

struct Data
{
    int x,y;
    float angle;
    // Image im;
};

void update(Data &d)
{
    const float vitesse = 20.f;
    float temps = 10 + elapsedTime() / 10;
    d.angle = vitesse * temps;

    d.x = temps * cos(d.angle);
    d.y = temps * sin(d.angle);
}

void init(Data &d)
{
    update(d);
    // d.im = image("data/mines/mine.png");
}

void draw(Data &d)
{
    color(255, 255, 0);
    circleFill(DIMW/2 + d.x, DIMW/2+d.y, 10);
    // image_draw( d.im, 250, 100, 64, 64, d.angle, 2);
}

int main(int, char** )
{
    Data dat;
    bool stop=false;
    winInit("Tutorials", DIMW, DIMW);
    init(dat);
    backgroundColor(100, 50, 200);
    while( !stop )
    {
        winClear();
        draw(dat);
        stop = winDisplay();
        update(dat);
    }
    winQuit();
    return 0;
}'''

class Q8(Question): # pylint: disable=undefined-variable
    """Tuto 8 : Plot/Graph"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
using namespace grapic;

const int WIN_DIM_X = 370;
const int WIN_DIM_Y = 200;

int main(int, char**)
{
    bool stop=false;
    winInit("Demo", WIN_DIM_X, WIN_DIM_Y);
    setKeyRepeatMode(true);
    backgroundColor(255, 255, 255); // Plot background
    Plot p1, p2, p3 ;
    // 100 values maximum for graph/plot 'p2'
    plot_setSize(p2, 100);

    float x, y, y2;
    while( !stop )
    {
        ////////////////////////////// Add somes points on plots

        x = elapsedTime() * 4;
        y = cos(x);
        y2 = 0.5 * sin(x);

        // add a dot in the graph p1, curve number 0
        plot_add(p1, x, y);
        // add a dot in the graph p1, curve number 1
        plot_add(p1, x, y2, 1);

        // add a dot in the graph p2, curve0;
        // if 100 values are yet stored, the lowest is removed
        plot_add(p2, x, y);
        // if 100 values are yet stored, the lowest is removed
        plot_add(p2, x, y2, 1);

        plot_add(p3, cos(x), sin(x/1.1));

        ////////////////////////////// Draw plots

        backgroundColor(55, 0, 0);
        winClear();
        color(255, 0, 0);
        // draw the graph p1
        plot_draw(p1, 20, 20,
                  WIN_DIM_X - 20, WIN_DIM_Y / 2 - 20);
        // draw the graph p2 on the top of the window
        plot_draw(p2, 20, WIN_DIM_Y / 2 + 20,
                  WIN_DIM_X - 20, WIN_DIM_Y - 20, false);
        // draw the graph p3 with a background
        plot_draw(p3,
                  WIN_DIM_X / 2 - 50, WIN_DIM_Y / 2 - 50,
                  WIN_DIM_X / 2 + 50, WIN_DIM_Y / 2 + 50,
                  true);

        stop = winDisplay();
    }
    winQuit();
    return 0;
}'''

class Q10(Question): # pylint: disable=undefined-variable
    """Tuto 10 : Démos"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
#include <iostream>
#include <cmath>
using namespace std;
using namespace grapic;

const int WIN_DIM_X = 370;
const int WIN_DIM_Y = 300;
const int MENU_DIM_X = 100;
const int WIN_CENTER_X = (WIN_DIM_X - MENU_DIM_X) / 2;
const int WIN_CENTER_Y = WIN_DIM_Y / 2;

// An instance of this structure is passed to each functions
// init, draw and animate
struct Data
{
    int n;     // The number of demo
    int demo;  // Which demo is running
    int x, y;
    /*
    Image im;  // An image
    Image im2; // An image
    */
};

void demo0()
{
    int i, j;
    const int l = (WIN_DIM_X - MENU_DIM_X) / 10;
    for(i=0; i<10; ++i)
        for(j=0; j<10; ++j)
        {
            color(255*i*10/100, 255*j*10/100, 0);
            rectangleFill(i*l+1, j*l+1, (i+1)*l-1, (j+1)*l-1);
        }
}
void demo1()
{
    int x, y;
    mousePos(x, y); // Get the mouse position in (x,y)
    color(255,123,34);
    // Check if the mouse is in a rectangle (10,400)(50,600)
    if (x > 90 && y > 90 && x < 120 && y < 120)
    {
        fontSize(32);
        print(100, 100, "Grand");
    }
    else
    {
        fontSize(12);
        print(100, 100, "Petit");
    }
}
void demo2()
{
    // Draw a set of rectangles one inside each others
    int i, n = 10 + 10 * cos(5 * elapsedTime());
    for (i = 0; i < n; ++i)
    {
        color(10 * i, 220 - 10 * i, 150);
        rectangle((WIN_DIM_X - MENU_DIM_X) / 2 + 5 * i + 5 * i,
                  WIN_CENTER_Y + 5 * i,
                  (WIN_DIM_X - MENU_DIM_X) / 2 - 5 * i - 5 * i,
                  WIN_CENTER_Y - 5 * i);
    }
}
void demo3()
{
    float angle;
    float rayon = WIN_DIM_X / 6 ;
    int i, n = 20;
    for (i = 0; i < n; ++i)
    {
        color(10 * i, 10 * i, 50);
        angle = 2 * M_PI * i / n;
        rectangle(
            (WIN_DIM_X - MENU_DIM_X) / 2 + rayon * cos(angle) + rayon * cos(angle),
            WIN_CENTER_Y + rayon * sin(angle),
            (WIN_DIM_X - MENU_DIM_X) / 2 + 10 + rayon * cos(angle) + 10 + rayon * cos(angle),
            WIN_CENTER_Y + 10 + rayon * sin(angle));
    }
    color(255, 0, 255);
    circle((WIN_DIM_X - MENU_DIM_X) / 2,
           WIN_DIM_X / 8, 30);
    color(255, 255, 0);
    circleFill((WIN_DIM_X - MENU_DIM_X) / 2,
               3 * WIN_DIM_X / 4, 20);
}
void demo4()
{
    int i;
    int n = 250;
    for(i=0; i<n; i++)
    {
        color(i,i,i);
        rectangleFill( 2*i,0,2*i+1,500);
    }
}

void demo5(Data &d)
{
    color(255, 0, 0);
    grid(0, 0, WIN_DIM_X - MENU_DIM_X, WIN_DIM_Y, 8, 8);
    // if (isKeyPressed('a')        && d.x >   0) d.x--;
    // if (isKeyPressed(SDLK_LEFT)  && d.x >   0) d.x--;
    // if (isKeyPressed(SDLK_RIGHT) && d.x < 499) d.x++;
    // if (isKeyPressed(SDLK_DOWN)  && d.y >   0) d.y--;
    // if (isKeyPressed(SDLK_UP)    && d.y < 499) d.y++;
    // image_draw(d.im, d.x, d.y);
    int x, y;
    mousePos(x, y);
    color(0, 100, 255);
    rectangleFill(x-10, y-10, x+10, y+10);
    if (isMousePressed(SDL_BUTTON_LEFT))
    {
        int x, y;
        mousePos(x, y);
        color(255, 0, 100);
        if (x > WIN_CENTER_X && y < WIN_CENTER_Y)
            rectangleFill(WIN_CENTER_X, 0,
                        WIN_DIM_X - MENU_DIM_X, WIN_CENTER_Y);
    }
}
void demo6(Data &d)
{
    print(10, 100, "Not yet working in C5");
    /*
    int i,j;
    for(i=0;i<10;i++)
        for(j=0;j<10;j++)
        {
            if ( (i+j) % 2 == 0)
                image_draw( d.im, i*50, j*50, 50, 50);
            else
                image_draw(d.im2, i*50, j*50, 50, 50);
        }
    */
}
void demo7()
{
    int i;
    float a, b;
    print(10, WIN_DIM_Y-50, elapsedTime());
    for(i=0; i<12; ++i)
    {
        a = 0.5 * M_PI - 2 * (i+1) * M_PI / 12;
        color(25, 245, 23);
        print((WIN_DIM_X - MENU_DIM_X) / 2 + 100*cos(a),
               WIN_CENTER_Y + 100*sin(a),
               i+1);

        b = 0.5 * M_PI - 2 * elapsedTime() * M_PI / 12;
        color(255, 45, 23);
        line((WIN_DIM_X - MENU_DIM_X) / 2,
              WIN_CENTER_Y,
              (WIN_DIM_X - MENU_DIM_X) / 2 + 80*cos(b),
              WIN_CENTER_Y + 80*sin(b));
    }
}
int caseToPixel(Data &d, int c)
{
    return (d.n - c) * WIN_DIM_Y / d.n;
}
void menu(Data &d)
{
    int x, y;
    if (isMousePressed(SDL_BUTTON_LEFT))
    {
        mousePos(x, y);
        if (x > WIN_DIM_X - 100)
        {
            d.demo = d.n - 1 - y / (WIN_DIM_Y/d.n);
        }
    }
    fontSize(20);
    color(255, 0, 0);
    grid(WIN_DIM_X - 100, 0, WIN_DIM_X - 1, WIN_DIM_Y, 1, d.n);
    color(0, 255, 124);
    rectangleFill(WIN_DIM_X - 99, caseToPixel(d, d.demo  ) + 1,
                  WIN_DIM_X - 2, caseToPixel(d, d.demo+1) - 2);
    color(0, 0, 0);
    x = WIN_DIM_X - 100;
    for(int i=0; i<d.n; ++i)
    {
        y = caseToPixel(d, i+1) + 20;
        print(x + 10, y, "Demo");
        print(x + 70, y, i);
    }
}

void init(Data &d)
{
    // The init function is called once at the beginning
    // to initialize the Data.
    d.n = 8;
    d.demo = 1;
    d.x = 250;
    d.y = 250;
    /*
    // Load an image "data/grapic.bmp and store it in d.im
    d.im = image("data/pacman/pacman.png",
                 true, 255, 255, 255, 255);
    // If the image is not found, try in an other directory
    if (!image_isInit(d.im))
        d.im = image("../data/pacman/pacman.png",
                     true, 255, 255, 255, 255);
    assert( image_isInit(d.im) );
    d.im2 = image("data/pacman/fantome.png",
                  true, 255, 255, 255, 255);
    if (!image_isInit(d.im2))
        d.im = image("../data/pacman/fantome.png",
                     true, 255, 255, 255, 255);
    assert image_isInit(d.im2) ;
    */
}
void draw(Data &d)
{
    menu(d);
    switch(d.demo)
    {
    case 0: demo0(); break;
    case 1: demo1(); break;
    case 2: demo2(); break;
    case 3: demo3(); break;
    case 4: demo4(); break;
    case 5: demo5(d); break;
    case 6: demo6(d); break;
    case 7: demo7(); break;
    }
}

int main(int, char** )
{
    Data dat;
    bool stop=false;
    winInit("Demo", WIN_DIM_X, WIN_DIM_Y);
    setKeyRepeatMode(true);
    init(dat);
    while( !stop )
    {
        backgroundColor(255, 255, 255);
        winClear();
        draw(dat);
        stop = winDisplay();
        delay(50);
    }
    winQuit();
    return 0;
}
'''

class Q11(Question): # pylint: disable=undefined-variable
    """Tetris"""
    def default_answer(self):
        return r'''// Example from Alexandre Meyer, Université Lyon 1
#include <Grapic.h>
#include <cmath>
#include <iostream>
using namespace std;
using namespace grapic;

const int SIZE_X = 8;
const int SIZE_Y = 16;
const int SIZE_SPRITE_X = 32;
const int SIZE_SPRITE_Y = 32;
const int SIZE_BLOCK = 3;

struct Data
{
    int level[SIZE_X][SIZE_Y];
    int block[SIZE_BLOCK][SIZE_BLOCK];
    int pos_x, pos_y;
    float temps;
    float speed;
    int lost;
    int key_pressed;
};

int irand(int min, int max)
{
    return rand() % (max - min + 1) + min;
}

void createBlock(Data &d)
{
    int i, j, lg, dir, k;

    for(i=0;i<SIZE_BLOCK ;++i)
        for(j=0;j<SIZE_BLOCK ;++j)
        {
            d.block[i][j] = 0;
        }

    i = irand(0, SIZE_BLOCK - 1);
    j = irand(0, SIZE_BLOCK - 1);
    lg = 1 + irand(0, 4);
    for(k=0; k < lg; k++)
    {
        d.block[i][j] = 1;
        dir = irand(0, 3);
        switch(dir)
        {
            case 0: if (i < SIZE_BLOCK - 1) ++i; break;
            case 1: if (i > 0) --i; break;
            case 2: if (j < SIZE_BLOCK - 1) ++j; break;
            case 3: if (j > 0) --j; break;
        }
    }
    d.pos_x = SIZE_X / 2;
    d.pos_y = SIZE_Y - SIZE_BLOCK;
    d.speed = 0.;
}

void rotateBlockLeft(Data &d)
{
    int i, j;
    int t[SIZE_BLOCK][SIZE_BLOCK];
    for(i=0; i < SIZE_BLOCK; ++i)
        for(j=0; j < SIZE_BLOCK; ++j)
            t[i][j] = d.block[i][j];

    for(i=0; i < SIZE_BLOCK; ++i)
        for(j=0; j < SIZE_BLOCK; ++j)
            d.block[SIZE_BLOCK - 1 - j][i] = t[i][j];
}

void draw_rect(int i, int j, int c=1)
{
    color(c*100, 255 - c*20, 10*c);
    rectangleFill(
           i*SIZE_SPRITE_X + 2,     j*SIZE_SPRITE_Y + 2,
       (i+1)*SIZE_SPRITE_X - 2, (j+1)*SIZE_SPRITE_Y - 2);
}

void drawLevel(Data &d)
{
    int i, j;
    for(i=0; i < SIZE_X; ++i)
        for(j=0; j < SIZE_Y; ++j)
            if (d.level[i][j])
                draw_rect(i, j, 1);
}

void drawBlocks(Data &d)
{
    int i, j;
    for(i=0; i < SIZE_BLOCK; ++i)
        for(j=0; j < SIZE_BLOCK; ++j)
            if (d.block[i][j])
                draw_rect(i + d.pos_x, j + d.pos_y, 2);
}

bool blocksValid(Data &d, int pos_x, int pos_y)
{
    int i, j;
    for(i=0; i < SIZE_BLOCK; ++i)
        for(j=0; j < SIZE_BLOCK; ++j)
            if (d.block[i][j])
            {
                if (i + pos_x < 0 || i + pos_x >= SIZE_X)
                    return false;
                if (j + pos_y < 0 || j + pos_y >= SIZE_Y)
                    return false;
                if (d.level[i + pos_x][j + pos_y])
                    return false;
            }
    return true;
}

bool blocksTransfer(Data &d)
{
    int i, j;
    for(i=0; i < SIZE_BLOCK; ++i)
        for(j=0; j < SIZE_BLOCK; ++j)
            if (d.block[i][j])
                d.level[i + d.pos_x][j + d.pos_y] = 1;
    return true;
}

bool checkLine(Data &d, int l)
{
    int i;
    for(i=0; i < SIZE_X; ++i)
        if (!d.level[i][l])
            return false;
    return true;
}

void suppressLine(Data &d, int line)
{
    int x, l;
    for(l = line + 1; l < SIZE_Y; ++l)
        for(x=0; x < SIZE_X; ++x)
            d.level[x][l-1] = d.level[x][l];
}

void checkLines(Data &d)
{
    int l;
    for(l=0; l < SIZE_Y; ++l)
        if (checkLine(d, l))
        {
            suppressLine(d, l);
            l--;
        }
}

void init(Data &d)
{
    int i, j;
    for(i=0; i < SIZE_X; ++i)
        for(j=0; j < SIZE_Y; ++j)
            d.level[i][j] = 0;
    createBlock(d);
    d.temps = elapsedTime();
    d.lost = false;
    d.key_pressed = false;
    fontSize(20);
    checkLines(d);
}

void move_on_grid(Data &d)
{
    int delta_x[] = { 1, -1, 2, -2 } ;
    int delta_y[] = { 0, 1, 2 } ;
    for(int dy = 0; dy < 3 ; dy++)
        for(int dx = 0; dx < 4 ; dx++)
            if (blocksValid(d,
                            d.pos_x + delta_x[dx],
                            d.pos_y + delta_y[dy]))
            {
                d.pos_x += delta_x[dx] ;
                d.pos_y += delta_y[dy] ;
                return;
            }
    d.lost = true;
}

void draw(Data &d)
{
    int check_now = false;

    if (d.lost)
    {
        color(255, 0, 0);
        print(10, 100, "YOU HAVE LOST");
        print(10, 50, "press 'r' to retry");
        if (isKeyPressed('r'))
            init(d);
        winDisplay();
        return ;
    }
    if (isKeyPressed(SDLK_LEFT))
    {
        if (blocksValid(d, d.pos_x - 1, d.pos_y))
             d.pos_x--;
        d.speed = 500;
    }
    else if (isKeyPressed(SDLK_UP))
    {
        rotateBlockLeft(d);
        if (!blocksValid(d, d.pos_x, d.pos_y))
            move_on_grid(d);
        d.speed = 500;
    }
    else if (isKeyPressed(SDLK_RIGHT))
    {
        if (blocksValid(d, d.pos_x + 1, d.pos_y))
            d.pos_x++;
        d.speed = 500;
    }
    else if (isKeyPressed(SDLK_DOWN))
    {
        if ( ! d.key_pressed )
        {
            while(blocksValid(d, d.pos_x, d.pos_y - 1))
                d.pos_y--;
            check_now = true;
            d.key_pressed = true;
        }
    }
    else
        d.key_pressed = false;
    float t = elapsedTime();
    if (t - d.temps > d.speed || check_now)
    {
        if (blocksValid(d, d.pos_x, d.pos_y - 1))
            d.pos_y--;
        else
        {
            blocksTransfer(d);
            checkLines(d);
            createBlock(d);
            if (! blocksValid(d, d.pos_x, d.pos_y))
                {
                    d.lost = true;
                    return;
                }
            d.speed = 1000;
        }
        d.temps = t;
    }
    backgroundColor(100, 80, 200);
    winClear();
    color(115, 90, 210);
    grid(0, 0,
         SIZE_X * SIZE_SPRITE_X-1, SIZE_Y * SIZE_SPRITE_Y-1,
         SIZE_X, SIZE_Y);
    drawLevel(d);
    drawBlocks(d);
    winDisplay();
    d.speed = 1;
}

int main(int, char** )
{
    Data dat;
    winInit("Tetris",
        SIZE_X * SIZE_SPRITE_X,
        SIZE_Y * SIZE_SPRITE_Y);
    setKeyRepeatMode(false);
    init(dat);
    while( !winHasFinished() )
        draw(dat);
    winQuit();
    return 0;
}
'''