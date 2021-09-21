# GenshinFish
Auto control fishing. **Specifically optimized for low spec PCs. Manually coded image recognition should make you feel less guilty for using, and is safer from detection. xD** And if the average refresh rate of a fishing session is lower than 20, then it probably straight won't work, try something written in c. The refresh rate will be printed after a fishing session.
 
Keep your game resolution above 800x600. WIndowed or fullscreen don't matter. Language doesn't matter.
 
Run main.exe as admin.

It should show *Ready!*

Choose your bait type then cast the rod manually, it'll help with the tension control.

Keep the whole game window visible! The program depends on all sorts of UI elements to do things.

## Why use it?
We are lazy shit

## How to use it?
Run main.py as admin, start fishing. 

Cast the rod manually, and it'll detect any status change and control the tension when the time comes. 

Press K to stop current controlling session in case it might not realize that the fish is already caught( it usually would ) 

You can scale or move game window if you like, but not during fighting with the fish.

## Extra information
It's purely based on image recognition, nothing RAM related. Should be safe if you ask me.

Well it does call some win32api to pass mouse events, don't use it if you consider that sus.

Not tested on anything other than just one 1k 16:9 monitor. I'm lazy.

And of course you can make it more automated. I'm just too lazy to do it.

It doesn't take too beefy of a PC to run, but if you can't stay at 60 FPS while running this, consider changing the *update_sleep_time* value in config.json, but keep it under 0.2. And if it's still laggy, or losing control sometimes, then prob better just fish it yourself.

## Update v1.0.0
Basically usable now. 


## Update v0.0.4
Value adjustment to cope with different lighting conditions. I only tested dark environment with v0.0.3.

New strategy to reduce the time to locate progress bar before the control loop. In my case, 0.23s to 0.08s.


## Update v0.0.3
Fixed some unstable occasions.

Better compatibility, with lower spec PC, with high resolution monitors, etc.

Pretty significant performence boost. For my 1k monitor laptop with GTX 1060, refresh rate has increased from 20 fps to 60 fps. Higher the resolution, more obvious the effect. If target tension zone indicator displacement happens a lot, try bringing *lower_resolution_ratio* down, minimum 0.

Added tension indicator visual feedback option.

Added clear console on every update option.

Added some debug options.

## Update v0.0.2
Globalization support. No need to configure language now.