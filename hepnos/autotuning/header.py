

def get_flags_from_header(filename):
    interpreter_directive = False
    flag_translation = {
        '-A': 'allocation',
        '--allocation': 'allocation',
        '-t': 'time',
        '--time': 'time',
        '-n': 'nodes',
        '--nodes': 'nodes',
        '-q': 'queue',
        '--queue': 'queue',
        '-p': 'partition',
        '--partition': 'partition'
    }
    result = []
    for line in open(filename):
        if line.startswith('#!'):
            if interpreter_directive:
                return args
            else:
                interpreter_directive = True
            continue
        elif line.startswith('#H '):
            flags = line.split()[1:]
            result += flags
        else:
            break
    return result
