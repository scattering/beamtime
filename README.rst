================================
Neutron proposal deadline scaper
================================

This program attempts to extract the proposal submission deadlines for
various neutron facilities from the facility web pages.

This will be a brittle process and will likely need much care and tuning
of the deadline extraction patterns in the code.

Requires
--------

* Web server
* cron job scheduler
* python 2.5 or above

Installation
------------

Retrieve the current version of the source from::

    https://github.com/pkienzle/beamtime

Edit scrape.py, changing WEBMASTER='' to::

    WEBMASTER='your.name@email.address'

This will ensure that you are notified of errors during web scraping
and allow you to adjust the rules accordingly.

To keep the information up to date, the following commands need to 
be run daily on your server::

    $ python scrape.py > /var/www/deadline.html
    $ chmod a+r /var/www/deadline.html

This is usually done using cron.


Adding facilities
-----------------

To add a new facility, create a new class in scrape.py which defines
the attributes *name*, *url*, and the method *scrape()*.  The *scrape*
method defines the attributes *deadline* and *period* if they are
available, or raises an error.  See the examples in the code for
implementing scrape.

To extend this effectively, you will have to understand the python
regular expression parser. In particular, note that we are using the
pattern (.*?) to match a date, and match.group(1) to extract it.  The
parenthesis cause everything matched within them to be returned as a
group, and the question mark limits it to the shortest possible match.
If the result can span multiple lines you will need the re.DOTALL flag
for the match.

When a facility is updated or a new facility is added you can test
that the web scraping works using::

    $ python scrape.py FACILITY > deadline.html

This will attempt to retrieve just the facility given by *FACILITY*.

Please post any updates to the scraping pattern to github.

Removing brittleness
--------------------

Facilities could adopt a standard interface for exporting proposal 
deadline information, such as::

    http://facility.web/info/proposal_deadline.json

which returns a static page in JSON format::

    {
      'facility' : 'facility name',
      'url'      : 'http://link.to/proposal_system',
      'deadline' : 'string',
      'period'   : 'string',
    }

For proposal systems where the deadline varies, using a standard date
format such as 'YYYY-MM-DD' would be convenient.

