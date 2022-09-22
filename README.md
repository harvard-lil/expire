expire
======
This is a program for expiring old backup files. It is modeled on
`dirvish-expire`, part of [dirvish](https://dirvish.org/), a rotating
backup system. A good explanation of the expiration rules is in the
[Debian HOWTO](https://dirvish.org/debian.howto.html); note that this
system does not use dirvish's `expire-default` mechanism, so to
accomplish the default expiration of 15 days, the last line in the set
of example rules would need to be uncommented:

```
#       MIN HR    DOM MON       DOW  STRFTIME_FMT
	*   *     *   *         1    +3 months
	*   *     1-7 *         1    +1 year
	*   *     1-7 1,4,7,10  1
	*   10-20 *   *         *    +4 days
#	*   *     *   *         2-7  +15 days
```

The basic idea is that files whose creation times match the crontab in
the first five fields of a given rule are kept for the duration of the
last field, or indefinitely if the last field is empty.

Note that this kind of scheme will not necessarily play nicely with a
group of files that have previously been thinned according to some
other plan. For instance, a directory containing only files from the
first of the month will get over-thinned by rules set up to keep
Monday files.

Installation
------------
For regular use, start a virtual environment and install this package
and its requirements, something like this:
```
python3 -m venv env
. env/bin/activate
pip install git+https://github.com/harvard-lil/expire#egg=expire
```

Usage
-----
```
% expire --help
Usage: expire [OPTIONS]

  A tool for expiring old backups.

Options:
  -r, --rules TEXT              A single rule (repeatable)
  --rulefile FILENAME           File of rules
  -d, --directory TEXT          Directory containing files to be considered
                                for deletion
  --recursive / --no-recursive  [default: no-recursive]
  -f, --files TEXT              A single file to be considered for deletion
                                (repeatable)
  --dryrun / --no-dryrun        [default: dryrun]
  --help                        Show this message and exit.
```

Development
-----------
For development, [install
Poetry](https://python-poetry.org/docs/#installation) and clone this
repository. Then, in the repo's directory, install the package and its
requirements like this:

```
poetry install
```

Keep it clean with `poetry run pflake8`.

Add dependencies with `poetry add`, and keep `requirements.txt`
up-to-date with `poetry export -o requirements.txt`.

Run tests with `poetry run pytest`.

TODO
----
Improve testing.
