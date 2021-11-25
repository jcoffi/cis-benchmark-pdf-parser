#!/usr/bin/env python3

import fitz
import csv
import re
import logging
import argparse

# Initialize variables
(
    rule_count,
    level_count,
    description_count,
    acnt,
    rat_count,
    rem_count,
    cis_count,
) = (0,) * 7
firstPage = None
seenList = []

# Setup console logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging_streamhandler = logging.StreamHandler(stream=None)
logging_streamhandler.setFormatter(
    logging.Formatter(fmt="%(asctime)s %(levelname)-8s %(message)s")
)
logger.addHandler(logging_streamhandler)

# Setup command line arguments
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parses CIS Benchmark PDF content into CSV Format"
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--pdf_file", type=str, required=True, help="PDF File to Parse"
    )
    required.add_argument(
        "--out_file", type=str, required=True, help="Output file in .csv format"
    )
    args = parser.parse_args()

    # Open PDF File
    doc = fitz.open(args.pdf_file)

    # Skip to actual rules
    for currentPage in range(len(doc)):
        findPage = doc.loadPage(currentPage)
        if findPage.searchFor("Recommendations 1"):
            firstPage = currentPage

    # If no "Recommendations" and "Initial Setup" it is not a full CIS Benchmark .pdf file
    if firstPage is None:
        logger.info("*** Not a CIS PDF Benchmark, exiting. ***")
        exit()

    logger.info("*** Total Number of Pages: %i ***", doc.pageCount)

    # Open output .csv file for writing
    with open(args.out_file, mode="w") as cis_outfile:
        rule_writer = csv.writer(
            cis_outfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        rule_writer.writerow(
            [
                "Rule",
                "Profile Applicability",
                "Description",
                "Rationale",
                "Audit",
                "Remediation",
                "CIS Controls",
            ]
        )

        # Loop through all PDF pages
        for page in range(firstPage, len(doc)):
            if page < len(doc):
                data = doc.loadPage(page).getText("text")
                logger.info("*** Parsing Page Number: %i ***", page)

                # Get rule by matching regex pattern for x.x.* (Automated) or (Manual), there are no "x.*" we care about
                try:
                    pattern = r"(\d+(?:\.\d.\d+)?)(.*?)(\(Automated\)|\(Manual\)|\(Scored\)|\(Not Scored\))"
                    rerule = re.search(pattern, data, re.DOTALL)
                    if rerule is not None:
                        rule = rerule.group(2).split("P a g e", 1)[1].strip()
                        rule_count += 1
                except IndexError:
                    logger.info("*** Page does not contain a Rule Name ***")
                except AttributeError:
                    logger.info("*** Page does not contain a Rule Name ***")

                # Get Profile Applicability by splits as it is always between Profile App. and Description, faster than regex
                try:
                    data = re.sub("[^a-zA-Z0-9\.\:\\n-]+", " ", data)
                    l_post = data.split("Profile Applicability:", 1)[1]
                    level = l_post.partition("Description:")[0].strip()
                    level = re.sub("[^a-zA-Z0-9\\n-]+", " ", level)

                    level_count += 1
                except IndexError:
                    logger.info("*** Page does not contain Profile Levels ***")

                # Get Description by splits as it is always between Description and Rationale, faster than regex
                try:
                    d_post = data.split("Description:", 1)[1]
                    description = d_post.partition("Rationale")[0].strip()
                    description_count += 1
                except IndexError:
                    logger.info("*** Page does not contain Description ***")

                # Get Rationale by splits as it is always between Rationale and Audit, faster than regex
                try:
                    rat_post = data.split("Rationale:", 1)[1]
                    rat = rat_post.partition("Audit:")[0].strip()
                    rat_count += 1
                except IndexError:
                    logger.info("*** Page does not contain Rationale ***")

                # Get Audit by splits as it is always between Audit and Remediation, faster than regex
                try:
                    a_post = data.split("Audit:", 1)[1]
                    audit = a_post.partition("Remediation")[0].strip()
                    acnt += 1
                except IndexError:
                    logger.info("*** Page does not contain Audit ***")

                # Get Remediation by splits as it is always between Remediation and CIS Controls, faster than regex
                try:
                    rem_post = data.split("Remediation:", 1)[1]
                    rem = rem_post.partition("CIS Controls:")[0].strip()
                    rem_count += 1
                except IndexError:
                    logger.info("*** Page does not contain Remediation ***")

                # Get CIS Controls by splits as they are always between CIS Controls and P a g e, regex the result
                try:
                    cis_post = data.split("CIS Controls:", 1)[1]
                    cis = cis_post.partition("P a g e")[0].strip()
                    cis = re.sub("[^a-zA-Z0-9\\n.-]+", " ", cis)
                    cis_count += 1
                except IndexError:
                    logger.info("*** Page does not contain CIS Controls ***")

                # We only write to csv if a parsed rule is fully assembled
                if rule_count:
                    row_count = [
                        rule_count,
                        level_count,
                        description_count,
                        rat_count,
                        acnt,
                        rem_count,
                        cis_count,
                    ]
                    if row_count.count(row_count[0]) == len(row_count):
                        # Have we seen this rule before? If not, write it to file
                        if row_count not in seenList:
                            seenList = [row_count]
                            logger.info("*** Writing the following rule to csv: ***")
                            row = [rule, level, description, rat, audit, rem, cis]
                            logger.info(row)
                            rule_writer.writerow(row)
                page += 1
            else:
                logger.info("*** All pages parsed, exiting. ***")
                exit()
