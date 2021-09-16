# GenshinFish
 Auto control fishing

# Why use it?
We are lazy shit

# How to use it?
## Run main.py as admin, start fishing. 
## Cast the rod manually, and it'll detect any status change and control the tension when the time comes. 
## Press P to exit, press K to stop current controlling session in case it might not realize that the fish is already caught( it usually would ) 
## Don't move or scale the game window when this is running.

# Extra information
It's purely based on image recognition, nothing RAM related. Should be safe if you ask me.
Well it does call some win32api, don't use it if you consider that dangerous.
I said don't move or scale the game window, but you can if you mod the code a bit, just make sure to re-instantiate ImageOperation class after any scaling or moving.
Not tested on anything other than just one 1k 16:9 monitor. I said I'm lazy.
And of course you can make it more automated. I'm just too lazy to do it.