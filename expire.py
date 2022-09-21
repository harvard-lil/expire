# Given rules like these, from dirvish, delete files in a
# directory accordingly.

"""

#       MIN HR    DOM MON       DOW  STRFTIME_FMT
	*   *     *   *         1    +3 months
	*   *     1-7 *         1    +1 year
	*   *     1-7 1,4,7,10  1
	*   10-20 *   *         *    +4 days
#	*   *     *   *         2-7  +15 days


The expire-rule stanza is for refining how long before a backup
expires; e.g. the first line has "1" for DOW (day of week),
i.e. Monday. Hence backups made on a Monday will stay around for 3
months. The second line says that backups made in the first week of
the month (DOM = day of month) won't expire until after one year. An
empty time spec is the same as "never".

"""

import click
from pathlib import Path
from datetime import datetime
from croniter import croniter
from dateutil.relativedelta import relativedelta


@click.command()
@click.option('--rules', '-r', multiple=True,
              help='A single rule (repeatable)')
@click.option('--rulefile', type=click.File(), help='File of rules')
@click.option('--directory', '-d',
              help='Directory containing files to be considered for deletion')
@click.option('--recursive/--no-recursive', default=False, show_default=True)
@click.option('--files', '-f', multiple=True,
              help='A single file to be considered for deletion (repeatable)')
@click.option('--dryrun/--no-dryrun', default=True, show_default=True)
def expire(rules, rulefile, directory, recursive, files, dryrun):
    """ A tool for expiring old backups. """
    rules = [make_rule(r) for r in rules]

    if rulefile:
        rules += [make_rule(line) for line in rulefile.readlines()
                  if not line.lstrip().startswith('#')]

    targets = [Path(f) for f in files]

    if directory:
        targets += list(Path(directory).glob('**/*' if recursive else '*'))

    for target in targets:
        if not target.is_file():
            pass

        ctime = datetime.fromtimestamp(Path(target).stat().st_ctime)
        now = datetime.now()

        if (any([matches(ctime, rule, now) for rule in rules])):
            keeping = 'would keep' if dryrun else 'keeping'
            click.echo(f'{keeping} {target}')
        else:
            deleting = 'would delete' if dryrun else 'deleting'
            click.echo(f'{deleting} {target}')
            if not dryrun:
                target.unlink()


def matches(ctime, rule, now):
    return (
        croniter.match(rule.crontab, ctime) and
        (rule.extent is None or now <= ctime + rule.extent)
        # it would be clearer to express this as
        #   now - ctime <= rule.extent,
        # but you can't compare a datetime.timedelta with a relativedelta
    )


def make_rule(line):
    return Rule(line.strip().split(maxsplit=5))


def make_delta(s):
    """
    This is not ideal, but I don't think there's a more clear
    translation of the "STRFTIME_FMT" field to a time difference,
    especially when months are concerned.
    """
    v, k = s.split()
    if 'minute' in k:
        return relativedelta(minutes=int(v))
    elif 'day' in k:
        return relativedelta(days=int(v))
    elif 'month' in k:
        return relativedelta(months=int(v))
    elif 'year' in k:
        return relativedelta(years=int(v))
    else:
        raise Exception(f'Bad extent: {s}')


class Rule():
    def __init__(self, parts):
        self.crontab = ' '.join(parts[0:5])
        try:
            self.extent = make_delta(parts[5])
        except IndexError:
            self.extent = None


if __name__ == '__main__':
    expire()
