# GenshinFish
 Auto control fishing

# Why use it?
We are lazy shit

# How to use it?
## If you do not play in English, go to the top of the script and change the game window title to your language.
## Run main.py as admin, start fishing. 
## Cast the rod manually, and it'll detect any status change and control the tension when the time comes. 
## Press K to stop current controlling session in case it might not realize that the fish is already caught( it usually would ) 
## You can scale or move game window if you like, but not during fighting with the fish.

# Extra information
## It's purely based on image recognition, nothing RAM related. Should be safe if you ask me.
## Well it does call some win32api, don't use it if you consider that sus.
## Not tested on anything other than just one 1k 16:9 monitor. I'm lazy.
## And of course you can make it more automated. I'm just too lazy to do it.
## it doesn't take too beefy of a PC to run, but if you can't stay at 60 FPS while running this, consider changing the wait time value in Clicker class __init__. And if it's still laggy, or losing control in a fishing battle, then prob better just fish it yourself.
