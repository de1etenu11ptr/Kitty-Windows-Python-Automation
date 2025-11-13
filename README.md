# Kitty-Windows-Python-Automation

Automates the process of creating specific kitty multi-window sessions, and the build and logging of various projects using a formatted JSON configuration.

The project was built to streamline my workflow, mostly being the building and logging aspects, hence the multi-window session launcher may seem a bit lackluster in comparison as it only creates sessions using a predifined layout and with predefined titles.

The scripts are entirely independent and can be used separately.

# What It Does

KWPA (I'm not that creative, but even I can tell... carrying on) uses the available kitty classes and a few from python's standard library to look for a `.kitty-session.json` in the build window and log window separately (that can be changed in `workstation-kitten.py`).

It uses the found JSON to determine the set of commands to run for a specified profile in that window, and attempts to find the respective build and log windows (using the title properties of kitty windows)

To change the default titles assigned by `session-launcher-kitten.py`, you will need to change a few values in its script as it, by default, creates windows with the titles `project-build` and `project-log` hence why `workstation-kitten.py` searches for those by default).

From there it will send the commands to those kitty windows using kitty's "Window().paste_bytes()" function (I couldn't get Popen to work. I suspect it is due to it being incapable, to my knowledge, of communicating between processes aside from creating a new one). 

# Formatted Json Example

Below is an example of what one of my projects JSON config You can use it to get an idea of what formatting `workstation-kitten.py` expects.
```
{
	"debug" : {
		"build" : [
			[
				"make",
				"BUILD=debug",
				"clean",
				"all"
			],
			"&&",
			[
				"gdb",
				"program"
			]
		],
		"log" : [
			"tail",
			"-f",
			"program.log"
		]
	},
	"test" : {
		"build" : [
			[
				"make",
				"BUILD=test",
				"clean",
				"all"
			],
			"&&",
			"./program"
		],
		"log": [
			"tail",
			"-f",
			"program.log"
		]
	}
}
```

What the program expects is some JSON formatted config in the path of the session, i.e. the current working directory.

It first combs through the entries of the json, and looks for the profile that the user requested, which was either passed to the kitten script (see the example section below), or through a prompt if `-build input` is passed. Within that it expects two arrays, the first being for the "build" window, and the second being for the "log" window, where each of the arrays specify the commands that will be run.

As can be seen from the example above (or concluded), it has a recursive functionality that allows you to use binary operators, such as "&&", and under the hood it uses shlex.join() to ensure arguments are properly quoted. This is probably crude, and could be better implemented.

One of the shortcomings I have already noticed is that implementing some form of blacklist (or whitelist) would be a bit more effort. I am also skeptical on how it would handle something like shell expansion, or parenthesis as those have not been implemented.

# Example

You can run any of the scripts provided by setting them to some keyboard mappings in your `~/.config/kitty/kitty.conf`, for example,

```~/.config/kitty/kitty.conf
map ctrl+f4 kitten workstation-kitten.py -build test
map ctrl+f5 kitten session-launcher-kitten.py -type single
````

Here, for the first mapping, `test` corresponds to a profile in `.kitty-session.json`. The JSON should define arrays for the "build" and "log" windows with the commands to execute.

The second mapping is for the `session-launcher-kitten.py`, where single informs it that only a single os window (kitty defines two windows, an os window which is the whole window you see when launching the terminal emulator, and a kitty window which are the windows that you can create within an os window).

# Limitations

- Shell expansions or parenthesis may not be fully supported.
- Blacklist/whitelist for commands is not implemented.
- Recursive command handling is limited to binary operators like `&&`.

# Plans

No immediate plans — these scripts were created to improve my workflow and may not be actively maintained.
