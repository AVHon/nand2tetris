
// Runs an infinite loop that listens to the keyboard input. 
// 	When a key is pressed (any key), the program blackens the screen,
// 	i.e. writes "black" (1) in every pixel.
// 	When no key is pressed, the program clears the screen, i.e. writes
// 	"white" in every pixel.
// repeat loop
// 
// The keyboard has only 1 memory location: RAM[24576], aka RAM[KBD]
// 
// The screen occupies 8192 words from RAM[16384] (aka RAM[SCREEN])
// through RAM[24575]. Each pixel is one bit of a word.
// 
// Alex Von Hoene	1 Feb 2013

(BEGIN_PROGRAM)
(WAIT_FOR_KEY_PRESS)
    //store keyboard memory to register D
    @KBD
    D = M
    
    //if register D != 0, exit this loop
    @END_WFKP
    D;JNE
    
    //repeat this loop until a keypress is detected
    @WAIT_FOR_KEY_PRESS
    0;JMP
(END_WFKP)

@SCREEN
D=A
(BLACKEN_SCREEN)
    //if the loop has reached the keyboard location, stop writing
    @KBD
    D=D-A
    @END_BLKSCR
    D;JEQ
    
    @KBD
    D=D+A
    //write 1111111111111111 to RAM[D]
    A = D
    M=-1
    
    //increment D
    D=D+1
    
    //repeat loop
    @BLACKEN_SCREEN
    0;JMP
(END_BLKSCR)

(WAIT_FOR_KEY_RELEASE)
    //store keyboard state to register D
    @KBD
    D=M
    
    //if register D = 0, exit this loop
    @END_WFKR
    D;JEQ
    
    //repeat this loop
    @WAIT_FOR_KEY_RELEASE
    0;JMP
(END_WFKR)

@SCREEN
D=A
(WHITEN_SCREEN)
    //if D is at the keyboard position, exit this loop
    @KBD
    D=D-A
    @END_WHTSCR
    D;JEQ
    
    @KBD
    D=D+A
    //write 0 to the current screen location
    A = D
    M=0
    
    //increment the screen location
    D=D+1
    
    //repeat this loop
    @WHITEN_SCREEN
    0;JMP
(END_WHTSCR)

//repeat this program forever
@BEGIN_PROGRAM
0;JMP
