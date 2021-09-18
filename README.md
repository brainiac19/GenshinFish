# GenshinFish
 Auto control fishing

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

## Update 0.0.2
Globalization support. No need to configure language now.
**Substitute templates from the release with the ones in the repo to avoid losing control in some cases**