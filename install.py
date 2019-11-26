import sys, os, html, tempfile, shlex

if len(sys.argv) not in (3, 4):
    sys.stderr.write('''\
usage: python3 install.py <data_dir> <tests_dir> [testsys_dir]

Installs the contests into the specified dk-careglaz installation.
    <data_dir> refers to the dk-careglaz data directory (`data/` in the installation root).
    <tests_dir> refers to the directory containing the **already extracted** tests.
    [testsys_dir] (optional) refers to the root directory of the 'testing system' itself.
''')
    exit(1)

def listdir_russian(path):
    return [i.split(b'!', 1)[0].decode('latin-1').encode('cp858', 'replace').decode('cp866', 'replace') for i in os.listdir(path.encode('utf-8'))]

def listdir_sorted(path):
    return list(sorted(os.listdir(path.encode('utf-8')), key=lambda x: x.split(b'!', 1)[0]))

def keyfunc(name):
    i = 0
    ans = []
    while i < len(name):
        if name[i].isnumeric():
            q = ''
            while i < len(name) and name[i].isnumeric():
                q += name[i]
                i += 1
            ans.append(int(q))
            ans.append(q)
        else:
            q = ''
            while i < len(name) and not name[i].isnumeric():
                q += name[i]
                i += 1
            ans.append(q)
    return tuple(ans)

data_dir = sys.argv[1]
tests_dir = sys.argv[2]
testsys_dir = sys.argv[3] if len(sys.argv) == 4 else None

ls_dump = os.listdir(tests_dir)
assert set(ls_dump) == set(map(str, range(len(ls_dump))))

contest_names = list(sorted(listdir_russian(testsys_dir+'/tests'))) if testsys_dir != None else [str(i + 1) for i in range(len(ls_dump))]
assert len(ls_dump) == len(contest_names)

contest_dirs = iter(listdir_sorted(testsys_dir+'/tests')) if testsys_dir != None else None

intro = []

for i, n in enumerate(contest_names):
    os.mkdir(data_dir+'/scoreboard/cmc-pas-'+str(i))
    contest_dir = data_dir+'/tasksheets/cmc-pas-'+str(i)
    os.mkdir(contest_dir)
    with open(contest_dir+'/name.txt', 'w') as file: file.write(n)
    intro.append('<p><a href="cmc-pas-'+str(i)+'">'+html.escape(n)+'</a></p>')
    tester = '''\
from collections import OrderedDict
from dkcareglaz.tester import show_ok, run_solution, display_output, superstrip
from html import escape

def read_doubles(ans):
    return [list(map(float, i.split())) for i in ans.strip().split('\\n')]

def validate(out, ans):
    try: ans = read_doubles(ans)
    except ValueError: pass
    else:
        try: out = read_doubles(out)
        except ValueError: return False
        return len(ans) == len(out) and all(len(x) == len(y) and all(abs(i - j) < 1e-7 for i, j in zip(x, y)) for x, y in zip(ans, out))
    return superstrip(out).strip() == superstrip(ans).strip()

def test(elf, log, tests):
    out = True
    wa = False
    for i, (test, ans) in enumerate(tests):
        normal, stdout, stderr = run_solution(elf, test, log, 'Test #{}'.format(i+1), encoding='latin-1')
        if normal:
            if show_ok(log, all(not validate(stdout, i) for i in ans.split('||'))):
                out = False
                wa = True
        else: out = False
        display_output(test, stdout, stderr, log)
        if wa:
            log.write('correct answer\\n')
            log.write(escape(superstrip(ans))+'\\n')
    return out

def get_tester(tests):
    def tester(elf, log): return test(elf, log, tests)
    return tester

tasks = OrderedDict()
'''
    dump_dir = tests_dir+'/'+str(i)
    ls_tasks = os.listdir(dump_dir)
    assert set(ls_tasks) == set(map(str, range(len(ls_tasks))))
    if contest_dirs == None:
        task_names = [str(i + 1) for i in range(len(ls_tasks))]
        statements = None
    else:
        task_names = []
        statements = []
        statements_dir = testsys_dir.encode('utf-8')+b'/tests/'+next(contest_dirs)
        for task in os.listdir(statements_dir):
            if task.endswith(b'_r.rtf'):
                task_names.append(task[:-6].decode('ascii', 'replace'))
                statements.append(statements_dir+b'/'+task)
        task_names = list(zip(task_names, statements))
        task_names.sort(key=lambda t: keyfunc(t[0]))
        task_names, statements = zip(*task_names)
    for j, n2 in enumerate(task_names):
        task_dir = dump_dir+'/'+str(j)
        test_set = []
        idx = 1
        while os.path.exists(task_dir+'/iii'+str(idx)):
            test_set.append((open(task_dir+'/iii'+str(idx), encoding='latin-1').read(), open(task_dir+'/ooo'+str(idx), encoding='latin-1').read()))
            idx += 1
        tester += 'tasks[%r] = (%r, get_tester(%r))\n'%(str(j+1), n2, test_set)
    if statements != None:
        statements = iter(statements)
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(temp_dir+'/1.html', 'w') as o_html:
                for n2 in task_names:
                    o_html.write('<h1>'+html.escape(n2)+'</h1>')
                    with open(next(statements), 'rb') as rfile:
                        with open(temp_dir+'/0.rtf', 'wb') as wfile:
                            wfile.write(rfile.read())
                    assert not os.system('libreoffice --convert-to html --outdir '+shlex.quote(temp_dir)+' '+shlex.quote(temp_dir+'/0.rtf'))
                    with open(temp_dir+'/0.html') as rfile:
                        o_html.write(rfile.read())
            assert not os.system('libreoffice --convert-to odt --outdir '+shlex.quote(temp_dir)+' '+shlex.quote(temp_dir+'/1.html'))
            with open(temp_dir+'/1.odt', 'rb') as rfile:
                with open(temp_dir+'/2.odt', 'wb') as wfile:
                    wfile.write(rfile.read())
            assert not os.system('libreoffice --convert-to html --outdir '+shlex.quote(temp_dir)+' '+shlex.quote(temp_dir+'/2.odt'))
            with open(temp_dir+'/2.html') as rfile:
                with open(contest_dir+'/tasks.html', 'w') as file: file.write(rfile.read())
                tester += '\nintro = %r\n'%('<a href="../tasks/cmc-pas-'+str(i)+'">Условия задач</a>')
    with open(contest_dir+'/tester.py', 'w') as file: file.write(tester)

os.mkdir(data_dir+'/scoreboard/cmc-pas')
os.mkdir(data_dir+'/tasksheets/cmc-pas')

intro = '\n'.join(intro)

with open(data_dir+'/tasksheets/cmc-pas/tasks.html', 'w') as file:
    file.write('<html>\n<head>\n<meta charset="utf-8" />\n</head>\n<body>\n')
    file.write(intro)
    file.write('\n</body>\n</html>\n')

with open(data_dir+'/tasksheets/cmc-pas/tester.py', 'w') as file:
    file.write('intro = %r\n\ntasks = {}\n'%intro)
