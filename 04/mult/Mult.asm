// Multiply R0 and R1 and store the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[3], respectively.)
// DO NOT change the contents of R0 or R1
// Alex Von Hoene	31 Jan 2013

//clear the contents of R2
@2
M = 0

//if R0 = 0, go to end of loop
@0
D = M
@END
D;JEQ

//store R1 to R3
@1
D=M
@3
M=D

(LOOP)
    //if R3 = 0, go to the end of the loop
    @3
    D = M
    @END
    D;JEQ
    //load R0, store to D
    @0      //store "0" to register A
    D = M   //store the contents of ram[A] to register D
    //add D and R2 and store to R2
    @2          //store "2" to rA
    M = D + M   //add register D and ram[A] (ram[2]) and store to ram[A] (ram[2])
    //decrement R3
    @3
    M = M - 1
    //go back to start of loop
    @LOOP
    0;JMP
(END)
//This is the end of the program. Programs end with an infinite loop
@END
0;JMP
