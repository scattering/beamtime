# This program is in the public domain
# Author: Paul Kienzke, William Ratcliff

import sys
import smtplib
import traceback
import urllib2
import re
from datetime import datetime

# Get a time stamp for the start of today.
today = datetime.today()
today = datetime(year=today.year,month=today.month,day=today.day)

# ===== Configuration ======

WEBMASTER = ""
#WEBMASTER = "william.ratcliff@nist.gov"
#WEBMASTER = "paul.kienzle@nist.gov"



# ==================== Facilities =====================

# Facility sets
AMERICAS = []
EUROPE = []
EAST = []

class NCNR:
    name = "NCNR"
    url = "http://www.ncnr.nist.gov/call/current_call.html"
    def scrape(self):
        self.deadline = "activity suspended until Feb. 2012"
AMERICAS.append(NCNR())

class ORNL:
    name = "ORNL"
    url = "http://neutrons.ornl.gov/users/proposals.shtml"
    def scrape(self):
        data = fetchurl(self.url)
        pat = re.compile(r'<td>[^,]+,\s+(.*?),\s+Midnight Eastern Time</td>\s*<td>(.*?)</td>',
                         flags=re.DOTALL)
        match = list(pat.findall(data))
        for deadline, period in match:
            # TODO: this will fail if Locale indicates non-English month names
            if datetime.strptime(deadline, '%B %d, %Y') >= today:
                self.deadline, self.period = deadline, period
                break
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
AMERICAS.append(ORNL())

class LANSCE:
    name = "LANSCE"
    url = "http://lansce.lanl.gov/"
    def scrape(self):
        data = fetchurl(self.url)
        pat = re.compile('Lujan Center.*?Proposal Call.*?Deadline (.*?)<',
                         flags=re.DOTALL)
        match = pat.search(data)
        if match:
            self.deadline = match.group(1)
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
AMERICAS.append(LANSCE())

class CNBC:
    name = "CNBC, Chalk River"
    url = "http://www.cins.ca/beam.html"
    deadline = "continuous proposal system"
    def scrape(self): pass
AMERICAS.append(CNBC())

class ANSTO:
    name = "ANSTO"
    url="https://neutron.ansto.gov.au/Bragg/proposal/index.jsp"
    def scrape(self):
        data = fetchurl(self.url)
        match = re.search('Proposal Round for instrument time (.*?)<.*?>. Proposals are due by (.*?)[.]',
                          data)
        if match:
            self.deadline = match.group(2)
            self.period = match.group(1)
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
EAST.append(ANSTO())

class JPARC:
    name = "J-PARC"
    url = "http://j-parc.jp/MatLife/en/applying/koubo.html"
    def scrape(self): pass
EAST.append(JPARC())

class ISIS:
    name = "ISIS"
    url = "http://www.isis.stfc.ac.uk/apply-for-beamtime/"
    def scrape(self):
        data = fetchurl(self.url)
        match = re.search('Proposal deadline:\W*?(.*?) for beamtime from (.*?)\W*?<',
                          data)
        if match:
            self.deadline = match.group(1)
            self.period = match.group(2)
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
EUROPE.append(ISIS())

class ILL:
    name = "ILL"
    url = "http://club.ill.fr/cv/"
    def scrape(self):
        data = fetchurl(self.url)
        match = re.search('Next deadline is\W*?(.*?)[.]?<', data)
        if match:
            self.deadline = match.group(1)
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
EUROPE.append(ILL())

class LLB:
    name = "LLB"
    url = "http://www-llb.cea.fr/en/fr-en/proposal.php"
    deadline = "1 May and 1 November annually"
    def scrape(self):
        return # Show all rather than just the next
        if (5 < today.month < 11 
            or (today.month == 5 and today.day > 1) 
            or (today.month == 11 and today.day == 1)):
             self.deadline = "1 November %d"%today.year
        elif today.month > 5:
             self.deadline = "1 May %d"%(today.year+1)
        else:
             self.deadline = "1 May %d"%(today.year) 
EUROPE.append(LLB())

class BENSC:
    name = "BENSC"
    url = "http://www.helmholtz-berlin.de/user/neutrons/user-info/call-for-proposals_en.html"
    deadline = "1 March and 1 September annually"
    def scrape(self):
        return # Show all rather than just the next
        if (3 < today.month < 9
            or (today.month == 3 and today.day > 1)
            or (today.month == 9 and today.day == 1)):
             self.deadline = "1 September %d"%today.year
        elif today.month > 3:
             self.deadline = "1 March %d"%(today.year+1)
        else:
             self.deadline = "1 March %d"%(today.year)

EUROPE.append(BENSC())

class FRM_II:
    name = "FRM II"
    url = "http://www.frm2.tum.de/en/user-office/user-guide/index.html"
    def scrape(self): pass
EUROPE.append(FRM_II())

class SINQ:
    name = "SINQ"
    url = "http://sinq.web.psi.ch/sinq/sinq_call.html"
    def scrape(self):
        data = fetchurl(self.url)
        match = re.search('proposal\W*submission\W*deadline:\W*<font.*?>\W*(.*?)\W*</font', data)
        if match:
            self.deadline = match.group(1)
        else:
            raise ValueError("Can't find proposal data. Website layout changed?")
EUROPE.append(SINQ())


# ===== page layout ===
PAGE = """\
<html>
<link rel="stylesheet" type="text/css" href="site.css" />
<title>Beamtime Proposal Deadlines</title>
<body>
<h2>Beamtime proposal deadlines</h2>

%(table)s

* This information was obtained automatically from the respective
websites and we cannot guarantee that it is correct.  Please verify dates
with the individual facilities.

</body>
</html>
"""

TABLE_HEADER = """\
<table class="pretty-table"><tbody>
  <tr class="header">
     <th scope="col">Institute</th>
     <th scope="col">Submission Deadline*</th>
     <th scope="col">Experiment Period</th>
  </tr>"""
TABLE_REGION = """\
  <tr class="region">
      <th scope="row" colspan="3">%(region)s</td>
  </tr>"""
TABLE_ROW = """\
  <tr class="%(rowclass)s">
    <th scope="row"><a href="%(url)s">%(name)s</a></td>
    <td>%(deadline)s</td>
    <td>%(period)s</td>
  </tr>"""
TABLE_FOOTER = """</tbody></table>"""


def build_table(regions):
    emit = [TABLE_HEADER]

    for region,facilities in regions:
        emit.append(TABLE_REGION%dict(region=region))
        odd = True
        for facility in facilities:
            d = dict(name = facility.name,
                     url = facility.url,
                     deadline = facility.deadline,
                     period = facility.period,
                     rowclass = "odd" if odd else "even",
                     )
            emit.append(TABLE_ROW%d)
            odd=not odd

    emit.append(TABLE_FOOTER)

    return "\n".join(emit)



def scrape(facilities, limit=None):
    errors = []
    for facility in facilities:
        try:
            if not limit or facility.__class__.__name__ in limit:
                facility.scrape()
        except:
            errors.append(facility.name+"\n"+traceback.format_exc())
        if not hasattr(facility,'period'):
            facility.period = ''
        if not hasattr(facility,'deadline'):
            facility.deadline = 'unknown'
        if not testurl(facility.url):
            errors.append("%s: broken link\n  %s"%(facility.name,facility.url))
    return errors


def testurl(url):
    try:
        f = urllib2.urlopen(urllib2.Request(url))
        okay = True
    except:
        okay = False
    return okay

def fetchurl(url):
    return urllib2.urlopen(url).read()
def fetchdom(url):
    import BeautifulSoup
    return BeautifulSoup.BeautifulSoup(fetchurl(url))

def mail(sender, receivers, message,
         subject='no subject', server='localhost'):
    """
    Send an email message to a group of receivers
    """
    if ':' in server:
        host,port = server.split(':')
        port = int(port)
    else:
        host,port = server,25
    header="From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n"
    header %= sender,", ".join(receivers),subject
    #print "Sending the following mail message:\n"+header+message
    #print "Trying to connect to",host,port
    smtp = smtplib.SMTP(host,port)
    #print "Connection established"
    smtp.sendmail(sender,receivers,header+message)
    #print "Mail sent from",sender,"to",", ".join(receivers)
    smtp.quit()



def main():
    if len(sys.argv) > 1:
        limit = sys.argv[1:]
    else:
        limit = None

    # Scrape all facility webpages, storing results in the facility objects.
    # Return 
    errors = scrape(AMERICAS+EUROPE+EAST, limit)

    table = build_table([('North America',AMERICAS),
                         ('Europe',EUROPE),
                         ('Asia and Australia',EAST),
                         ])
    page = PAGE%dict(table=table)
    print page

    if errors:
        if limit is not None and WEBMASTER != "":
            mail(sender=WEBMASTER,
                 receivers=[WEBMASTER],
                 message="\n".join(errors),
                 subject="proposal deadline scraper")
        else:
            print >>sys.stderr, "\n".join(errors)


if __name__ == "__main__":
    main()
