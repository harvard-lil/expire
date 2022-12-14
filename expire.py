# Given rules like these, from dirvish, delete files in a
# directory accordingly.

"""

#       MIN HR    DOM MON       DOW  STRFTIME_FMT
	*   *     *   *         1    +3 months
	*   *     1-7 *         1    +1 year
	*   *     1-7 1,4,7,10  1
	*   10-20 *   *         *    +4 days
#	*   *     *   *         2-7  +15 days


> The expire-rule stanza is for refining how long before a backup
> expires; e.g. the first line has "1" for DOW (day of week),
> i.e. Monday. Hence backups made on a Monday will stay around for 3
> months. The second line says that backups made in the first week of
> the month (DOM = day of month) won't expire until after one year. An
> empty time spec is the same as "never".

"""

import click
from pathlib import Path
from datetime import datetime
from croniter import croniter
from dateutil.relativedelta import relativedelta
from humanize import naturalsize
import logging
import click_log
import sys

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


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
@click_log.simple_verbosity_option(logger)
def expire(rules, rulefile, directory, recursive, files, dryrun):
    """ A tool for expiring old backups. """
    rules = [Rule(r) for r in rules]

    if rulefile:
        rules += [Rule(line) for line in rulefile.readlines()
                  if not line.lstrip().startswith('#') and line.strip()]

    targets = [Path(f) for f in files]

    if directory:
        targets += sorted(Path(directory).glob('**/*' if recursive else '*'))

    freed = deleted = 0
    now = datetime.now()

    for target in [t for t in targets if t.is_file()]:
        ctime = datetime.fromtimestamp(Path(target).stat().st_ctime)

        if (any([rule.matches(ctime, now) for rule in rules])):
            keeping = 'would keep' if dryrun else 'kept'
            logger.info(f'{keeping} {target}')
        else:
            deleted += 1
            freed += Path(target).stat().st_size
            deleting = 'would delete' if dryrun else 'deleted'
            logger.info(f'{deleting} {target}')
            if not dryrun:
                target.unlink()

    if deleted:
        s = 's' if deleted > 1 else ''
        logger.warning(f'{deleting} {deleted} file{s} occupying '
                       f'{naturalsize(freed)}')
    else:
        logger.warning('no files to delete')


class Rule():
    def __init__(self, line):
        parts = line.strip().split(maxsplit=5)
        self.crontab = ' '.join(parts[0:5])
        try:
            self.extent = self._make_delta(parts[5])
        except IndexError:
            self.extent = None

    def matches(self, ctime, now):
        try:
            return (
                croniter.match(self.crontab, ctime) and
                (self.extent is None or now <= ctime + self.extent)
                # it would be clearer to express this as
                #   now - ctime <= self.extent,
                # but you can't compare a timedelta with a relativedelta
            )
        except Exception as e:
            # this Exception is really a croniter error, but croniter does
            # not expose CroniterError -- only several specific errors
            logger.error(e)
            sys.exit(1)

    def _make_delta(self, s):
        """
        This is not ideal, but I don't think there's a more clear
        translation of the "STRFTIME_FMT" field to a time difference,
        especially when months are concerned.
        """
        try:
            v, k = s.split()
        except ValueError as e:
            logger.error(f'Bad extent "{s}": {e}')
            sys.exit()
        try:
            if 'minute' in k:
                return relativedelta(minutes=int(v))
            elif 'day' in k:
                return relativedelta(days=int(v))
            elif 'month' in k:
                return relativedelta(months=int(v))
            elif 'year' in k:
                return relativedelta(years=int(v))
            else:
                logger.error(f'Bad extent "{s}"')
                sys.exit()
        except ValueError as e:
            logger.error(f'Bad extent "{s}": {e}')
            sys.exit()


if __name__ == '__main__':
    expire()
