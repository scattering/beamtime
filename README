Neutron proposal deadline scaper
--------------------------------

This program attempts to extract the proposal submission deadlines for
various neutron facilities from the facility web pages.

This will be a brittle process and will likely need much care and tuning
of the deadline extraction patterns in the code.

To add a new facility, create a new class in scrape.py which defines
the attributes *name*, *url*, and the method *scrape()*.  The *scrape*
method defines the attributes *deadline* and *period* if they are
available, or raises an error.  See the examples in the code for
implementing scrape.

To extend this effectively, you will have to understand the python
regular expression parser. In particular, not that we are using the
pattern (.*?) to match a date, and match.group(1) to extract it.  The
parenthesis cause everything matched within them to be returned as a
group, and the question mark limits it to the shortest possible match.
If the pattern spans multiple lines you will need the re.DOTALL flag
to match it.

When a facility is updated or a new facility is added you can test
that facility using::

    $ python scrape.py CLASSNAME > deadline.html

Once the facilities patterns are all working successfully, you can
change WEBMASTER to your email address (so you are notified of
errors in the patterns or the web retrievals) and run the following
through a cron job::

    $ python scrape.py > /var/www/deadline.html
    $ chmod a+r /var/www/deadline.html
