# VM COmpiler for Hack Platform, part 2
# loads xxx.vm and outputs to xxx.asm
# Alex Von Hoene
# 1 April 2013

from vmMemoryTranslator import *


def getFileName():
	#return getFileName()
	#return 'FunctionCalls/FibonacciElement/Main.vm'
	#return 'FunctionCalls/FibonacciElement/Sys.vm'
	return 'FunctionCalls/SimpleFunction/SimpleFunction.vm'
	#return 'FunctionCalls/StaticsTest/Class1.vm'
	#return 'FunctionCalls/StaticsTestClass2.vm'
	#return 'FunctionCalls/StaticsTestSys.vm'
	#return 'ProgramFlow/BasicLoop/BasicLoop.vm'
	#return 'ProgramFlow/FibonacciSeries/FibonacciSeries.vm'



def translateLineToAsm(line):
	words = line.split(' ')	# divide the line into a list of words
	command = words[0].lower()
	if vmCommandIsArithmetic(command) or command == 'push' or command == 'pop':
		translated = translateMemoryLineToAsm(line)
	else:
		if command == 'call':
			global calls
			# push the return address to the stack
			translated = ['@callReturnAdddress'+str(calls),
						  'D=A', '@SP', 'M=M+1', 'A=M-1', 'M=D']
			# push LCL, ARG, THIS, and THAT to the stack, in that order
			for location in ['LCL', 'ARG', 'TYHIS', 'THAT']:
				translated.extend(['@'+location, 'D=A', '@SP', 'M=M+1',
								  'A=M-1', 'M=D'])
			# reposition ARG to SP-n-5, where n is the number of
			# arguments of the called function
			translated.extend(['@5', 'D=A', '@SP', 'D=M-D',
							  '@'+str(words[2]), 'D=D-A', '@ARG', 'M=D'])
			# point LCL to top of stack
			translated.extend(['@SP', 'D=A', '@LCL', 'M=D'])
			
			# increment the total number of calls
			calls += 1
		elif command == 'function':
			translated = ['('+words[1]+')']
			for i in range(int(words[2])):
				translated.extend(translateMemoryLineToAsm('push local 0'))
		elif command == 'return':
			# store LCL to R13
			translated = ['@LCL', 'D=M', '@R13', 'M=D']
			# store LCL-5 to R14
			translated.extend(['@5', 'D=A', '@LCL', 'D=A-D', '@R14', 'M=D'])
			# 
		else:
			translated = ['stuff', 'more']
	return translated

def translateVmToAsm(vm):
    asm = []
    global jumps
    jumps = 0
    initializationCommands = ['@'+str(STACK_START), 'D=A', '@SP', 'M=D']
    for line in initializationCommands:
        asm.append(line)
    for line in vm:
        translated = translateLineToAsm(line)
        for command in translated:
            asm.append(command)
    global jumps
    closingCommands = ['(VmJump.'+str(jumps)+')', '@VmJump.'+str(jumps), '0;JMP' ]
    jumps += 1
    for line in closingCommands:
        asm.append(line)
    return asm

######################
#### MAIN PROGRAM ####
######################
vmFileName = getFileName()
vm = getVMFileContents(vmFileName)
global vmName
vmName = getVMName(vmFileName)

vm = cleanVMLines(vm)

global calls
calls = 0
asm = translateVmToAsm(vm)

print(asm)
saveASM(asm, vmFileName)
