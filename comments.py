#!/usr/bin/python3

import collections
import glob
import os

def main():
    histo = [0] * 1000
    sessions = collections.defaultdict(list)
    for session in glob.glob('COMPILE_*/*'):
        exam = False
        if not os.path.exists(f'{session}/session.cf'):
            print(f'rm -rf {session}')
            continue
        with open(f'{session}/session.cf', 'r', encoding='latin1') as f:
            for line in f:
                if line.startswith("('allow_copy_paste', 0)"):
                    exam = True
                if line.startswith("('allow_copy_paste', 1)"):
                    exam = False
        if not exam:
            continue
        for student in glob.glob(f'{session}/LOGS/*/journal.log'):
            if not os.path.exists(student.replace('journal.log', 'grades.log')):
                continue
            comments = 0
            with open(student, 'r', encoding='latin1') as file:
                for line in file:
                    if line.startswith('bC') and '???' not in line:
                        comments += 1
                    if line.startswith('b+'):
                        line = line.split(' ', 7)
                        if line[7] != '\n':
                            comments += 1
            sessions[session].append(comments)
            histo[comments] += 1
        if sessions[session]:
            if sum(sessions[session]) == 0:
                # No comments for any students
                print('Remove', len(sessions[session]), session)
                histo[0] -= len(sessions[session])
            else:
                print(session, ' '.join(str(i) for i in sessions[session]))
        else:
            del sessions[session]

    while histo[-1] == 0:
        histo.pop()

    for session in sorted(sessions, key=lambda x: len(sessions[x])):
        comments = sessions[session]
        if not comments:
            continue
        commented = [i for i in comments if i]
        pc_commented = int(100*len(commented)/len(comments))
        if commented:
            avg_commented = sum(commented) / len(commented)
        else:
            avg_commented = 0
        print(f'{len(comments):3} copies notées.{pc_commented:>3}% commentées.'
              f' Moy. nbr. commentaires des commentées {avg_commented:.1f} {session}')
    print(histo)

    print('<style>TABLE.histo SPAN { background: #8F8; display: inline-block }</style>')
    print('<table class="histo">')
    print('<tr><th>#comments<th>%<th>#copies<th></tr>')
    max_copies = max(histo)
    nr_comments = 0
    total_copies = sum(histo)
    copies = 0
    median = None
    for i, nr_copies in enumerate(histo):
        width = 40 * nr_copies / max_copies
        nr_comments += i * nr_copies
        copies += nr_copies
        if copies > total_copies // 2 and median is None:
            median = i
        percent = int(100*nr_copies/total_copies)
        if percent == 0:
            break
        print(f'<tr><td>{i}<td>{percent}%<td><span style="width:{width:.2f}em">{nr_copies}</span></tr>')
    
    average = nr_comments / total_copies
    print(f'''<tr><td colspan="3">{total_copies} copies.
Moyenne {average:.1f} commentaires.<br>
Médiane {median} commentaires.
</tr>''')
    print('</table>')

main()
