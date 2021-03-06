# This is a template for a Python scraper on morph.io (https://morph.io)
# including some code snippets below that you should find helpful

import urllib2
import pdfquery
from lxml import etree
import scraperwiki
from datetime import datetime

# Drop previous data table
# try:
#     scraperwiki.sql.execute("DROP TABLE data")
# except:
#     print "table data not found"

extractedOn = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

# Get the pdf file
def download_file(url):
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    # print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 64000
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        # status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        # status = status + chr(8) * (len(status) + 1)
        # print status,

    f.close()
    return file_name

def parse_page(page):
        suburb_x0 = page.xpath('.//LTTextLineHorizontal[substring(text(),1,6)="Suburb"][1]/@x0')[0]
        address_x0 = page.xpath('.//LTTextLineHorizontal[substring(text(),1,7)="Address"][1]/@x0')[0]
        type_x0 = page.xpath('.//LTTextBoxHorizontal[substring(text(),1,4)="Type"][1]/@x0')[0]
        price_x1 = page.xpath('.//LTTextBoxHorizontal[substring(text(),1,5)="Price"][1]/@x1')[0][0:5]
        result_x0 = page.xpath('.//LTTextBoxHorizontal[substring(text(),1,6)="Result"][1]/@x0')[0]
        agent_x0 = page.xpath('.//LTTextBoxHorizontal[substring(text(),1,5)="Agent"][1]/@x0')[0]
        lines_y0 = set(page.xpath('.//*[string-length()>0]/@y0'))

        for line_y0 in lines_y0:

            item = {
                "suburb": "",
                "address": "",
                "type": "",
                "price": "",
                "result": "",
                "agent": "",
                "link": ""
            }

            empty_item = item.copy()

            suburb = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][@x0="' + suburb_x0 + '"]/text()')
            if len(suburb) > 0:
                item["suburb"]=suburb[0].strip()

            address_elem = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][@x0="' + address_x0 + '"]')
            if len(address_elem) > 0:
                address = address_elem[0].xpath("./text()")
                item["address"]=address[0].strip()
                addr_x0 = address_elem[0].xpath("./@x0")[0]
                addr_y0 = address_elem[0].xpath("./@y0")[0]
                addr_x1 = address_elem[0].xpath("./@x1")[0]
                addr_y1 = address_elem[0].xpath("./@y1")[0]

            prop_type = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][@x0="' + type_x0 + '"]/text()')
            if len(prop_type) > 0:
                item["type"]=prop_type[0].strip()

            price = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][substring(@x1,1,5)="' + price_x1[0:5] + '"]/text()')

            if len(price) > 0:
                item["price"]=price[0].strip()
#            else:
#                print price_x1
#                for c in page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"]'):
#                    print etree.tostring(c, pretty_print=True)

            result = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][@x0="' + result_x0 + '"]/text()')
            if len(result) > 0:
                item["result"]=result[0].strip()

            agent = \
                page.xpath('.//*[string-length(normalize-space(text()))>0][@y0="' + line_y0 + '"][@x0="' + agent_x0 + '"]/text()')
            if len(agent) > 0:
                item["agent"]=agent[0].strip()

            try:
                addr_x0 and addr_y0 and addr_y0 and addr_y1
            except:
                item["link"]=""
            else:
                link_xpath = ".//Annot[@x0<%s][@y0<%s][@x1>%s][@y1>%s]/@URI" % (addr_x0, addr_y0, addr_x1, float(addr_y1)-1)
                link = page.xpath(link_xpath)
                if len(link)>0:
                    item["link"]=link[0].strip()

            if "".join(empty_item.values()) == "".join(item.values()):
                continue

            # If 3 or more fields are empty, don't save it, just print it
            if item.values().count("") > 2:
                print "Found bogus line %s" % item
                continue

            # Write out to the sqlite database using scraperwiki library
            scraperwiki.sqlite.save(unique_keys=['suburb','address'], data={
                "suburb": item["suburb"],
                "address": item["address"],
                "type": item["type"],
                "price": item["price"],
                "result": item["result"],
                "agent": item["agent"],
                "url": item["link"],
                "extracted_on": extractedOn
            })


# Main scrapper logic
file_name = "http://www.homepriceguide.com.au/saturday_auction_results/Melbourne_Domain.pdf"
local_file = download_file(file_name)
#local_file="Melbourne_Domain.pdf"
print "PDF file retrieved"

# It won't go to 250 :)
for page_num in range(1,250):

    pdf = pdfquery.PDFQuery(local_file,
                            round_floats=True,
                            round_digits=2,
                            normalize_spaces=True,
                            resort=True
                            )

    try:
        pdf.load(page_num)
    except:
        print "Done"
        break

    print "PDF page %s loaded into memory" % page_num

    root = pdf.tree

    # for every page determine column coordinates and parse values
    for page in root.xpath("/pdfxml/LTPage"):
        parse_page(page)

    root = None
    pdf.load(None)
    pdf = None
