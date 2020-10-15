inputFile = 'profile.gcode'

file = open(inputFile, 'r')
code = []

for line in file:
    line = line.lstrip().rstrip('\n ')

    if line == '':
        continue

    if line[0] == 'G':
        col = {}

        commands = line.split(' ')

        col['g'] = commands[0:1]

        for i in commands[1:]:

            if i[0] == 'X':
                col['x'] = float(i[1:])

            elif i[0] == 'Y':
                col['y'] = float(i[1:])

            elif i[0] == 'Z':
                col['z'] = float(i[1:])

            elif i[0] == 'F':
                # can do something with speeds here in future
                continue

            else:
                print(line)
                raise Warning('Unknown character!')

    code.append(col)

if isinstance(inputFile, str):
    file.close()

# uncomment below to see current output
print(code)
