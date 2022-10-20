##
A remake of my previous Space Invaders emulator.
I tried to use some of Python's newer features and also some tricks that I had learned. You no longer have to compile a cython module to achieve playable speeds.
## Requirements
 - pygame
## Controls
                      Player 1: A - left    Player 2 : left arrow  - left
                                D - right              right arrow - right
                                W - shoot              up arrow    - shoot
                                E - start              right CTRL  - start

                      space       - tilt
                      enter       - insert coin
                      numbers 0-3 - sets the amount of lives to: pressed number + 3
                      numbers 4-5 - bonus life at 4: 1000 points
                                                  5: 1500 points
                      numbers 6-7 - coin info 6: off
                                              7: on
## Sounds
You need to have all of the 0.wav - 8.wav (9 files) sounds inside a folder named "samples", for example "samples/4.wav". If not all files are present, all sounds will be disabled.