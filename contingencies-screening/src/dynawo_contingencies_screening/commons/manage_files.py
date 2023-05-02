from lxml import etree


def parse_xml_file(xml_file):
    # Parse the XML file to be able to process it later
    xml = xml_file
    parser = etree.XMLParser()
    parsed_xml = etree.parse(xml, parser)

    return parsed_xml
