sh2seedgrinder.py
Copyright (c) GreaseMonkey, 2019
See LICENCE.txt for details (tl;dr it's zlib-licensed).

Special thanks to sh2_luck, whom without their efforts this steaming pile of software wouldn't exist.

This will grind all 2^31 seeds. That's 2,147,483,648 seeds. In practice this can take up to 3 minutes on My Machine™. In time it would be nice to bring that number down but eh, for now this'll do.

Requirements:

- Python 3.6 or higher
- numba
- numpy

To install the requirements that aren't Python:

python3 -m pip install -r requirements.txt

Windows users: You'll want to run that as administrator or something like that. I haven't tried it yet. If someone wants to try that, let me know how it goes and how it's supposed to work. Also it's probably `python` and not `python3` over in Windowsland. You also probably want to grab Python from here: https://www.python.org/downloads/

Linux users: If you don't have pip, tell your package manager to put it back in place because some distros like to take pip out of the base package.

Anyway, I know that It Would Be Nice If™ this had a GUI, but there's probably going to need to be some optimisation or better timeslicing of stuff or better multiprocessing stuff like semaphores or something like that before I inflict a painfully unresponsive GUI on you guys.
