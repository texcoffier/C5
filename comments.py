#!/usr/bin/python3

import glob

def main():
    histo = [0] * 1000
    for student in glob.glob('COMPILE_*/*/*/comments.log'):
        comments = set()
        with open(student, 'r', encoding='latin1') as file:
            for line in file:
                line = line.split(', ')
                if len(line) > 1:
                    if line[5] == '""]\n':
                        comments.remove(line[4])
                    else:
                        comments.add(line[4])
        histo[len(comments)] += 1
    while histo[-1] == 0:
        histo.pop()
    print('<style>TABLE.histo SPAN { background: #8F8; display: inline-block }</style>')
    print('<table class="histo">')
    print('<tr><th>#comments<th>#copies<th></tr>')
    max_copies = max(histo)
    nr_comments = 0
    total_copies = sum(histo)
    copies = 0
    median = None
    for i, nr_copies in enumerate(histo):
        if i == 0:
            continue
        width = 40 * nr_copies / max_copies
        nr_comments += i * nr_copies
        copies += nr_copies
        if copies > total_copies // 2 and median is None:
            median = i
        print(f'<tr><td>{i}<td><span style="width:{width}em">{nr_copies}</span></tr>')
    
    average = nr_comments / total_copies
    print(f'<tr><td><td>{total_copies} étudiants. Moyenne {average:.1f} commentaires. Médiane {median} commentaires.</tr>')
    print('</table>')

main()
