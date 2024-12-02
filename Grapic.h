#include <iostream>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>

namespace grapic {

using namespace std;

#define CW(X, ...) \
    do { \
    printf("\001\002EVAL") ; \
    printf(X, ##__VA_ARGS__) ; \
    putchar('\001') ; \
    } while(0)

int canvas_height ;
struct timeval canvas_time ;

void winInit(const char *title, int width, int height) {
    canvas_height = height;
    CW("G.init(%d,%d)", width, height);
    gettimeofday(&canvas_time, NULL);
}
float elapsedTime() {
    struct timeval now;
    gettimeofday(&now, NULL);
    return now.tv_sec - canvas_time.tv_sec
           + (now.tv_usec - canvas_time.tv_usec) / 1000000.;
}

void backgroundColor(int r, int v, int b, int alpha) {
    CW("G.backgroundColor(%d,%d,%d,%d)", r, v, b, alpha);
}
void backgroundColor(int r, int v, int b) {
    CW("G.backgroundColor(%d,%d,%d)", r, v, b);
}
void fontSize(int size) {
    CW("G.fontSize(%d)", size);
}
void rectangleFill(int x1, int y1, int x2, int y2) {
    CW("G.rectangleFill(%d,%d,%d,%d)", x1, y1, x2, y2);
}
void rectangle(int x1, int y1, int x2, int y2) {
    CW("G.rectangle(%d,%d,%d,%d)", x1, y1, x2, y2);
}
void circle(int x, int y, int radius) {
    CW("G.circle(%d,%d,%d)", x, y, radius);
}
void circleFill(int x, int y, int radius) {
    CW("G.circleFill(%d,%d,%d)", x, y, radius);
}
void line(int x1, int y1, int x2, int y2) {
    CW("G.line(%d,%d,%d,%d)", x1, y1, x2, y2);
}
void triangle(int x1, int y1, int x2, int y2, int x3, int y3) {
    CW("G.triangle(%d,%d,%d,%d,%d,%d)", x1, y1, x2, y2, x3, y3);
}
void triangleFill(int x1, int y1, int x2, int y2, int x3, int y3) {
    CW("G.triangleFill(%d,%d,%d,%d,%d,%d)", x1, y1, x2, y2, x3, y3);
}
void ellipse(int x, int y, int rx, int ry) {
    CW("G.ellipse(%d,%d,%d,%d)", x, y, rx, ry);
}
void ellipseFill(int x, int y, int rx, int ry) {
    CW("G.ellipseFill(%d,%d,%d,%d)", x, y, rx, ry);
}
void _polygon(const char *what, int points[][2], int n) {
    printf("\001\002EVALG.%s([[%d,%d]", what, points[0][0], points[0][1]);
    for(int i = 1; i < n; i++)
        printf(",[%d,%d]", points[i][0], points[i][1]);
    printf("])\001");
}
void polygon(int points[][2], int n) {
    _polygon("polygon", points, n);
}
void polygonFill(int points[][2], int n) {
    _polygon("polygonFill", points, n);
}
void grid(int x1, int y1, int x2, int y2, int nx, int ny) {
    CW("G.grid(%d,%d,%d,%d,%d,%d)", x1, y1, x2, y2, nx, ny);
}
void color(int r, int v, int b) {
    CW("G.color(%d,%d,%d)", r, v, b);
}
void winClear() {
    CW("G.clear()");
}

void print(int x, int y, const char *text) {
    const char *read ;
    char *write, escaped[1000];
    if ( strlen(text) > sizeof escaped / 2 ) {
        CW("G.print(%d,%d,'Texte trop long')", x, y);
        return;
    }
    write = escaped;
    for(read=text; *read; read++) {
        switch(*read) {
            case '\'':
            case '\\':
                *write++ = '\\';
                break ;
            case '\n':
                *write++ = '\\';
                *write++ = 'n';
                continue;
            case '\r':
                *write++ = '\\';
                *write++ = 'r';
                continue;
            case '&':
                *write++ = '\\';
                *write++ = 'x';
                *write++ = '2';
                *write++ = '6';
                continue;
            case '<':
                *write++ = '\\';
                *write++ = 'x';
                *write++ = '3';
                *write++ = 'C';
                continue;
            case '>':
                *write++ = '\\';
                *write++ = 'x';
                *write++ = '3';
                *write++ = 'E';
                continue;
        }
        *write++ = *read;
        }
    *write++ = '\0';
    CW("G.print(%d,%d,'%s')", x, y, escaped);
}

void print(int x, int y, int value) {
    CW("G.print(%d,%d,%d)", x, y, value);
}

char current_key[99];
int current_mouse = 0 ;
int current_x = 0, current_y = 0;
int images[999][2];

int winDisplay() {
    int len;
    printf("\001\002WAITD\001");
    fflush(stdout);
    fgets(current_key, sizeof(current_key), stdin);
    len = strlen(current_key);
    if (current_key[len-1] == '\n')
        current_key[len-1] = '\0';
    fscanf(stdin, "%d%*c", &current_mouse);
    fscanf(stdin, "%d%*c", &current_x);
    fscanf(stdin, "%d%*c", &current_y);
    current_y = canvas_height - current_y;
    len = 0;
    while(getc(stdin) == ' ') {
        fscanf(stdin, "%d%d", &images[len][0], &images[len][1]);
        len++ ;
    }
    return 0;
}

void delay(int millisecs) {
    char x[99];
    if (millisecs < 100)
        return;
    printf("\001\002WAITT%d\001", millisecs);
    fflush(stdout);
    fgets(x, sizeof(x), stdin);
}
void pressSpace() {
    char x[99];
    print(10, 10, "Press a key");
    printf("\001\002WAITK\001");
    fflush(stdout);
    fgets(x, sizeof(x), stdin);
}

#define SDLK_UP "ArrowUp"
#define SDLK_DOWN "ArrowDown"
#define SDLK_LEFT "ArrowLeft"
#define SDLK_RIGHT "ArrowRight"
#define SDL_BUTTON_LEFT 0
#define SDL_BUTTON_MIDDLE 2
#define SDL_BUTTON_RIGHT 3
#define SDL_FLIP_NONE 0
#define SDL_FLIP_HORIZONTAL 1
#define SDL_FLIP_VERTICAL 2

int isKeyPressed(int key) {
    return current_key[0] == key;
}

int isKeyPressed(const char *key) {
    return strcmp(current_key, key) == 0;
}

int isMousePressed(int button) {
    return button == current_mouse;
}

void mousePos(int &x, int &y) {
    x = current_x ;
    y = current_y ;
}

void mousePosGlobal(int &x, int &y) {
    x = current_x ;
    y = current_y ;
}

void winQuit() {
    CW("G.quit()");
}

int winHasFinished() {
    return 0;
}

class Menu {
public:
    const char *label = NULL;
    Menu *next = NULL ;
    int selected = -1; // Item selected or -1
    int choosing = 0; // 1 if button was down
};

void menu_add(Menu &menu, const char *label) {
    if (menu.next)
        menu_add(*menu.next, label);
    else {
        menu.label = label;
        menu.next = new Menu();
    }
}

int menu_nr_items(Menu &menu) {
    if ( menu.next )
        return 1 + menu_nr_items(*menu.next);
    return 0;
}

void menu_draw(Menu &menu,
               int xmin, int ymin,
               int xmax, int ymax) {
    int nr_items = menu_nr_items(menu);
    int dy ;
    Menu *m = &menu;
    menu.selected = -1;
    dy = (ymax - ymin) / nr_items;
    for(int i = 0; i < nr_items; i++) {
        if (current_x > xmin && current_x < xmax
                && current_y > ymin + i * dy
                && current_y < ymin + (i+1) * dy) {
            // On a button
            if (current_mouse == 0) {
                // Mouse down on a button
                if (! menu.choosing)
                    menu.choosing = 1;
                color(255, 0, 0);
            }
            else {
                if (menu.choosing) {
                    menu.selected = i;
                    menu.choosing = 0;
                }
                else
                    color(255, 0, 0);
            }
        }
        else
            color(255, 255, 255);
        rectangleFill(
            xmin, ymin + i * dy + 2,
            xmax, ymin + (i+1) * dy - 2);
        color(0, 0, 0);
        print(xmin + 5, ymin + (i+0.5) * dy, m->label);
        m = m->next;
    }
}

int menu_select(Menu &menu) {
    return menu.selected;
}

void setKeyRepeatMode(int x) {
}

int nr_plots = 0;
class Plot {
public:
    int id;
    Plot () {
        this->id = nr_plots++ ;
        CW("G.plot(%d)", this->id);
    }
};

void plot_setSize(Plot &p, int nr_points) {
    CW("G.plots[%d].set_size(%d)", p.id, nr_points);
}

void plot_add(Plot &p, float x, float y, int curve) {
    CW("G.plots[%d].add(%g,%g,%d)", p.id, x, y, curve);
}

void plot_add(Plot &p, float x, float y) {
    plot_add(p, x, y, 0);
}

void plot_draw(Plot &p, int xmin, int ymin, int xmax, int ymax, bool clear)
{
    CW("G.plots[%d].draw(%d,%d,%d,%d,%d)", p.id, xmin, ymin, xmax, ymax, clear);
}
void plot_draw(Plot &p, int xmin, int ymin, int xmax, int ymax)

{
    plot_draw(p, xmin, ymin, xmax, ymax, false);
}

int nr_images = 0;
class Image {
public:
    int id;
    Image() {
        this->id = -1;
    }
    Image(const char *url) {
        this->id = nr_images++;
        CW("G.new_image('%s')", url);
        winClear();
        winDisplay();
    }
    Image(int w, int h) {
        this->id = nr_images++;
        CW("G.new_image(%d,%d)", w, h);
    }
};

Image image(int w, int h) {
    return Image(w, h);
}

Image image(const char *url) {
    return Image(url);
}

void image_printInfo(Image &im) {
    cout << "id=" << im.id << endl;
}

void image_draw(Image &im, int x, int y, int w=-1, int h=-1) {
     CW("G.image_draw(%d,%d,%d,%d,%d)", im.id, x, y, w, h);
}

void image_draw(Image &im, int x, int y, int w, int h, float angle, float flip=SDL_FLIP_NONE) {
    CW("G.image_draw(%d,%d,%d,%d,%d,%g,%g)", im.id, x, y, w, h, angle, flip);
}


void image_set(Image &im, int x, int y,
        unsigned char r, unsigned char g, unsigned char b, unsigned char a) {
     CW("G.image_set(%d,%d,%d,%d,%d,%d,%d)", im.id, x, y, r, g, b, a);
}

int image_width(Image &im) {
    return images[im.id][0];
}

int image_height(Image &im) {
    return images[im.id][1];
}

}