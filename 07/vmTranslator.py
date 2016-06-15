# VM Compiler for Hack platform
# Loads xxx.vm, converts to Hack assembly, saves output to xxx.asm
# Alex Von Hoene
# 28 March 2013

import os.path
import sys

# important constants
STATIC_START = 16
STACK_START = 256
HEAP_START = 2048
IO_START = 16384

def getVmFileName():
    print('Please enter the path and name of')
    print('the .vm file, or enter "q" to quit')
    vmFileName = input()
    if vmFileName.lower() == 'q':
        print('Quitting.')
        sys.exit()
    if os.path.exists(vmFileName):
        if vmFileName.endswith('.vm'):
            return vmFileName
        else:
            print('"' + vmFileName + '" does not have a .vm file extension.')
            return getVmFileName()
    else:
        print('"' + vmFileName + '" does not exist.')
        return getVmFileName()

def removeComments(fileList):
    removedComments = 0
    for lineNumber in range(len(fileList)):
        line = fileList[lineNumber]
        uncommentedLine = ''
        for charNumber in range(len(line) - 1):
            if line[charNumber] + line[charNumber + 1] == '//':
                uncommentedLine = line[:charNumber]
                removedComments += 1
                fileList[lineNumber] = uncommentedLine
    print('Removed ' + str(removedComments) + ' comments.')
    return fileList

def trimLines(fileList):
    # removes EOLs and trailing spaces and tabs
    removedCharacters = 0
    for lineNumber in range(len(fileList)):
        line = fileList[lineNumber]
        if line.endswith('\c\r'):
            line = line[:-2]
        elif line.endswith('\n'):
            line = line[:-1]
        line.expandtabs(1)
        while line.endswith(' '):
            line = line[:-1]
            removedCharacters += 1
        line = line.replace('  ', ' ')
        fileList[lineNumber] = line
    print('Removed ' + str(removedCharacters) + ' trailing characters.')
    return fileList
            
def removeEmptyLines(fileList):
    lineNumber = 0
    removedLines = 0
    while lineNumber < len(fileList):
        if len(fileList[lineNumber]) == 0:
            fileList.pop(lineNumber)
            removedLines += 1
        else:
            lineNumber += 1
    print('Removed ' + str(removedLines) + ' empty lines.')
    return fileList


def translateArithmeticToAsm(line):
    cmd = line[0]
    # there are 3 types of arithmetic commands:
    #   operators that take 2 arguments from the stack
    #   operators that take 1 argument from the stack
    #   comparisons (which take 2 arguments from the stack)
    twoArgOperators = {'add':'+', 'sub':'-', 'and':'&', 'or':'|'}
    oneArgOperators = {'neg':'-', 'not':'!'}
    comparisons = {'eq':'JEQ', 'gt':'JGT', 'lt':'JLT'}
    
    if cmd in twoArgOperators:
        operator = twoArgOperators[cmd]
        return ['@SP', 'A=M-1', 'D=M', '@SP', 'M=M-1', 'A=M-1', 'M=M' + operator + 'D']
    elif cmd in oneArgOperators:
        operator = oneArgOperators[cmd]
        return ['@SP', 'A=M-1', 'M=' + operator + 'M']
    elif cmd in comparisons:
        jump = comparisons[cmd]
        global jumps
        jumpName = 'VmJump.'+str(jumps)
        jumps += 1
        asm = []
        # pop arg2 from top of stack to D, then to R13
        asm.extend(['@SP', 'M=M-1', 'A=M', 'D=M', '@R13', 'M=D'])
        # store arg1 to D
        asm.extend(['@SP', 'A=M-1', 'D=M'])
        # store D-R13 to R13
        asm.extend(['@R13', 'M=D-M'])
        # store TRUE to R14
        asm.extend(['@0', 'D=!A', '@R14', 'M=D'])
        # load arg1-arg2 to D, load the jump address
        asm.extend(['@R13', 'D=M', '@'+jumpName])
        # if the comparison is TRUE, skip this step. Else, write FALSE to R14
        asm.extend(['D;'+jump, '@0', 'D=A', '@R14', 'M=D', '('+jumpName+')'])
        # write R14 to top of stack
        asm.extend(['@R14', 'D=M', '@SP', 'A=M-1', 'M=D'])
        return asm
    else:
        print('Arithmetic command not recognized: "' + cmd + '"')
        sys.exit()

def translatePushToAsm(line):
    asm = []
    segment = line[1]
    index = line[2]

    namedSegments = {'argument':'ARG', 'local':'LCL', 'this':'THIS', 'that':'THAT'}
    pointerIndicies = {'0':'THIS', '1':'THAT'}

    # get value from segment[index], store to D
    if segment == 'constant':
        asm.extend(['@'+index, 'D=A'])
    elif segment == 'static':
        asm.extend(['@'+vmName+'.'+index, 'D=M'])
    elif segment == 'pointer':
        asm.extend(['@'+pointerIndicies[index], 'D=M'])
    elif segment == 'temp':
        if index == '0':
           asm.extend(['@R5', 'D=M'])
        else:
            asm.extend(['@R5', 'D=A', '@'+index, 'A=A+D', 'D=M'])
    elif segment in namedSegments:
        if index == '0':
            asm.extend(['@'+namedSegments[segment], 'A=M', 'D=M'])
        else:
            asm.extend(['@'+namedSegments[segment], 'A=M', 'D=A', '@'+index, 'A=A+D', 'D=M'])
    else:
        print('Segment not recognized: "' + segment + '"')
        sys.exit()

    # store to top of stack, increment stack
    asm.extend(['@SP', 'M=M+1', 'A=M-1', 'M=D'])
    return asm

def translatePopToAsm(line):
    asm = []
    segment = line[1]
    index = line[2]

    namedSegments = {'argument':'ARG', 'local':'LCL', 'this':'THIS', 'that':'THAT'}
    pointerIndicies = {'0':'THIS', '1':'THAT'}

    # decrement the stack, get the value off the top of the stack, store to D
    asm.extend(['@SP', 'M=M-1', 'A=M', 'D=M'])

    # store address of segment[index] to A
    if segment == 'static':
        asm.append('@'+vmName+'.'+index)
    elif segment == 'pointer':
        asm.append('@'+pointerIndicies[index])
    elif segment == 'temp':
        if index == '0':
            asm.append('@R5')
        else:
            # temporarily store D to R13
            # store index to R14
            # store the address of temp[index] to R14
            # store R13 to D
            # store R14 to A
            asm.extend(['@R13', 'M=D', '@'+index, 'D=A', '@R14', 'M=D', '@R5', 'D=A', '@R14', 'M=M+D', '@R13', 'D=M', '@R14', 'A=M'])
    elif segment in namedSegments:
        address = namedSegments[segment]
        if index == '0':
            asm.extend(['@'+address, 'A=M'])
        else:
            asm.extend(['@R13', 'M=D', '@'+index, 'D=A', '@R14', 'M=D', '@'+address, 'D=M', '@R14', 'M=M+D', '@R13', 'D=M', '@R14', 'A=M'])

    # store D to A
    asm.append('M=D')

    return asm
    

def vmCommandIsArithmetic(command):
    return command in ['add','sub','neg','eq','gt','lt','and','or','not']

def translateLineToAsm(line):
    line = line.split(' ') # convert the string into a list
    command = line[0].lower()
    if vmCommandIsArithmetic(command):
        return translateArithmeticToAsm(line)
    elif command == 'push':
        return translatePushToAsm(line)
    elif command == 'pop':
        return translatePopToAsm(line)
    else:
        print('VM command type not recognized: "' + line + '"')
        sys.exit()

def translateVmToAsm(vm):
    asm = []
    initializationCommands = ['@'+str(STACK_START), 'D=A', '@SP', 'M=D']
    for line in initializationCommands:
        #print(line)
        asm.append(line)
    for line in vm:
        #print(line)
        translated = translateLineToAsm(line)
        for command in translated:
            #print('\t' + command)
            asm.append(command)
    global jumps
    closingCommands = ['(VmJump.'+str(jumps)+')', '@VmJump.'+str(jumps), '0;JMP' ]
    jumps += 1
    for line in closingCommands:
        #print(line)
        asm.append(line)
    return asm



######################
# START MAIN PROGRAM #
######################
# get and open the file
##vmFileName = getVmFileName()
##vmFileName = 'MemoryAccess/BasicTest/BasicTest.vm'
##vmFileName = 'MemoryAccess/PointerTest/PointerTest.vm'
##vmFileName = 'MemoryAccess/StaticTest/StaticTest.vm'
##vmFileName = 'StackArithmetic/SimpleAdd/SimpleAdd.vm'
vmFileName = 'StackArithmetic/StackTest/StackTest.vm'
print('Opening ' + vmFileName)
vmFile = open(vmFileName, 'r')
vm = vmFile.readlines()

# close the file
print('Closing ' + vmFileName)
vmFile.close()

vm = removeComments(vm)
vm = trimLines(vm)
vm = removeEmptyLines(vm)

global vmName
vmName = vmFileName.split('/')[len(vmFileName.split('/')) - 1][:-3]
global stackLength
stackLength = 0
global jumps
jumps = 0
asm = translateVmToAsm(vm)

##for line in asm:
##    print(line)

asmFileName = vmFileName[:-2]+'asm'
asmFile = open(asmFileName, 'w')
for line in asm:
    asmFile.write(line + '\n')
asmFile.close()
print('Assembly saved to ' + asmFileName)
