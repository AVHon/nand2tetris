# Hack Assembler
# Loads Hack Assembly file xxx.asm and converts it to Hack binary file xxx.hack
# Alex Von Hoene
# 9 March 2013

import os.path
import sys


def getAsmFileName():
    print('Please enter the path and name of')
    print('the .asm file, or enter "q" to quit')
    asmFileName = input()
    if asmFileName.lower() == 'q':
        print('Quitting.')
        sys.exit()
    if os.path.exists(asmFileName):
        return asmFileName
    else:
        print('"' + asmFileName + '"' + ' does not exist.')
        return getAsmFileName()

def printProgram(fileList):
    for lineNumber in range(len(fileList)):
        print(str(lineNumber) + ": " + fileList[lineNumber])

def removeNonCode(fileList):
    removedSpaces = 0
    for lineNumber in range(len(fileList)):
        line = fileList[lineNumber]
        line.expandtabs(1)  # replace tabs with 1 space each
        emptiedLine = ''
        for char in line:
            if char == ' ':
                removedSpaces += 1
            else:
                emptiedLine += char
        # remove newline from end of each line
        if emptiedLine.endswith('\r\n'):
            fileList[lineNumber] = emptiedLine[:-2]
        elif emptiedLine.endswith('\n'):
            fileList[lineNumber] = emptiedLine[:-1]
        else:
            fileList[lineNumber] = emptiedLine
    print('Removed ' + str(removedSpaces) + ' spaces, tabs, and EOLs.')

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

    removedLines = 0
    lineNumber = 0
    while lineNumber < len(fileList):
        line = fileList[lineNumber]
        if (line == '\n') or (len(line) == 0):
            fileList = fileList[:lineNumber] + fileList[lineNumber + 1:]
            removedLines += 1
        else:
            lineNumber += 1
    print('Removed ' + str(removedLines) + ' empty lines.')
    return fileList

def getPredefinedSymbols():
    symbols = {'SP':0, 'LCL':1, 'ARG':2, 'THIS':3, 'THAT':4, 'SCREEN':16384, 'KBD':24576}
    # add registers R0 through R15 to the sumbols dictionary
    for i in range(16):
        registerName = 'R' + str(i)
        symbols[registerName] = i
    return symbols

def getLabels(fileList, symbols):
    symbolsFound = 0
    lineNumber = 0
    lineNumberWithoutSymbols = 0
    while lineNumber < len(fileList):
        line = fileList[lineNumber]
        if line.startswith('(') and line.endswith(')'):
            symbolName = line[1:-1]
            symbols[symbolName] = lineNumberWithoutSymbols
            symbolsFound = symbolsFound + 1
        else:
            lineNumberWithoutSymbols += 1
        lineNumber += 1
    print('Found ' + str(symbolsFound) + ' lables.')
    return symbols

def removeLabels(fileList):
    symbolsRemoved = 0
    lineNumber = 0
    while lineNumber < len(fileList):
        line = fileList[lineNumber]
        if line.startswith('(') and line.endswith(')'):
            #fileList.remove(line)
            fileList.pop(lineNumber)    # pop is faster than remove
            symbolsRemoved = symbolsRemoved + 1
        else:
            lineNumber += 1
    print('Removed ' + str(symbolsRemoved) + ' labels.')
    return fileList

def getVariables(fileList, symbols):
    variablesFound = 0
    variableAddress = 16
    for line in fileList:
        if line.startswith('@'):
            symbol = line[1:]
            if not symbol.isdigit():
                if not symbol in symbols:
                    symbols[symbol] = variableAddress
                    variableAddress += 1
                    variablesFound += 1
    print('Found ' + str(variablesFound) + ' variables.')
    return symbols

def replaceSymbols(fileList, symbols):
    replacedReferences = 0
    lineNumber = 0
    while lineNumber < len(fileList):
        line = fileList[lineNumber]
        if line.startswith('@'):
            symbolInLine = line[1:]
            if  not symbolInLine.isdigit():
                if symbolInLine in symbols:
                    fileList[lineNumber] = '@' + str(symbols[symbolInLine])
                    replacedReferences += 1
                else:
                    print('Undefined symbol reference "' + symbolInLine + '" in line ' + str(lineNumber))
                    print('KNOWN SYMBOLS:')
                    print(symbols)
                    sys.exit()
        lineNumber += 1
    print('Replaced ' + str(replacedReferences) + ' symbol references with constants.')
    return fileList

def saveProgramToFile(fileList, fileName):
    file = open(fileName, 'w')
    for line in fileList:
        file.write(line + '\n')
    file.close()

def translateLineToAInstruction(line):
    line = line.lstrip('@')
    binary = bin(int(line))
    binary = binary.lstrip('0b')   #python represents binary numbers as 0bxxxxxx
    binary = binary.zfill(16)  #add zeroes to the beginning of the line until it is 15 characters long
    return binary

def getAandCompBits(line):
    cInstructions = {'0':'0101010',   '1':'0111111',   '-1':'0111010',
                     'D':'0001100',   'A':'0110000',   '!D':'0001101',
                     '!A':'0110001',  '-D':'0001111',  '-A':'0110011',
                     'D+1':'0011111', 'A+1':'0110111', 'D-1':'0001110',
                     '1+D':'0011111', '1+A':'0110111',
                     
                     'A-1':'0110010', 'D+A':'0000010', 'D-A':'0010011',
                                      'A+D':'0000010',
                     
                     'A-D':'0000111', 'D&A':'0000000', 'D|A':'0010101',
                                      'A&D':'0000000', 'A|D':'0010101',
                     
                     'M':'1110000',   '!M':'1110001',  '-M':'1110011',
                     'M+1':'1110111', 'M-1':'1110010', 'D+M':'1000010',
                     '1+M':'1110111',                  'M+D':'1000010',
                     
                     'D-M':'1010011', 'M-D':'1000111', 'D&M':'1000000',
                     'D|M':'1010101', 'M|D':'1010101', 'M&D':'1000000'}
    # the comp part comes after the optional '=' and before the optional ';'
    if '=' in line:
        line = line.split('=')[1]
    if ';' in line:
        line = line.split(';')[0]

    if not (line in cInstructions):
        print('Instruction not recognized: ' + line)
        sys.exit()
    return cInstructions[line]


def getDestBits(line):
    # computation results are stored to the locations specified before the '='
    # for example, 'MD=A+1' stores A+1 to M and D
    # there does not have to be a '=', if this is so then return '000'
    destBin = ''
    if '=' in line:
        # remove the '=' and everything after
        destAsm = line.split('=')[0]
        # there are 3 possible destinations: A, D, and M, in that order
        for dest in 'ADM':
            if dest in destAsm:
                destBin += '1'
            else:
                destBin += '0'
    else:
        destBin = '000'
    return destBin

def getJumpBits(line):
    # there is only a jump if there is a ';' in the line
    jumpBin = ''
    if ';' in line:
        # remove the ';' and everything before
        jumpAsm = line.split(';')[1]
        # these are all of the jump codes and their binary equivalents
        # 'code':'binary', 'code':'binary', ...
        jumpAcronyms = {'JGT':'001','JEQ':'010','JGE':'011','JLT':'100','JNE':'101','JLE':'110','JMP':'111'}
        jumpBin = jumpAcronyms[jumpAsm]
    else:
        jumpBin = '000'
    return jumpBin

def translateLineToCInstruction(line):
    return '111' + getAandCompBits(line) + getDestBits(line) + getJumpBits(line)

def translateLineToBinary(line):
    if line.startswith('@'):
        return translateLineToAInstruction(line)
    else:
        return translateLineToCInstruction(line)

def translateAsmToBinary(asm):
    binary = []
    for line in asm:
        binaryLine = translateLineToBinary(line)
        binary.append(binaryLine)
    return binary
        

######################
# START MAIN PROGRAM #
######################
#open and copy the file
asmFileName = getAsmFileName()
##asmFileName = 'add/Add.asm'
##asmFileName = 'max/Max.asm'
##asmFileName = 'rect/Rect.asm'
##asmFileName = 'pong/Pong.asm'
print('Opening ' + asmFileName)
asmFile = open(asmFileName, 'r')
asm = asmFile.readlines()

#convert the code to pure assembly:
#   remove whitespace and comments
#   replace symbols
asm = removeNonCode(asm)
symbols = getPredefinedSymbols()
symbols = getLabels(asm, symbols)
asm = removeLabels(asm)
symbols = getVariables(asm, symbols)
asm = replaceSymbols(asm, symbols)

#save the intermediate result to xxx_withoutSyms.asm
asmWoSymsFileName = asmFileName[:-4] + '_withoutSyms.asm'
saveProgramToFile(asm, asmWoSymsFileName)
print('Pure Asembly program saved to ' + asmWoSymsFileName)

#convert pure assembly to binary, save the result
binary = translateAsmToBinary(asm)
print('Pure assembly program converted to HACK binary.')
binaryFileName = asmFileName[:-4] + '.hack'
saveProgramToFile(binary, binaryFileName)
print('HACK binary saved to ' + binaryFileName)

print('Closing ' + asmFileName)
asmFile.close()
print('Done.')
