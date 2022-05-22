import os
import sys
import argparse
'''
INPUT: tab-delimited blastn output. Assuming that taxonomy ID is in this format:
-outfmt "6 qseqid sseqid staxids sscinames scomnames sskingdoms pident length qlen slen mismatch gapopen gaps qstart qend sstart send stitle evalue bitscore qcovs qcovhsp"

This script also assumes that input has been filtered by 90% identity.
awk '{if ($7 > 90) print}' blast.tsv > filtered_blast.tsv

This script also assumes that taxonkit is installed and that the data has been downloaded to the current working directory.
mamba create -n taxonkit taxonkit -y
conda activate taxonkit
wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
tar xzvf taxdump.tar.gz

 Usage: python computeLCA.py filtered_blast.tsv > Table_of_TaxonIDs.tsv
'''


def call_on_taxonkit(current_query, taxons, data_dir):
    result_line = [current_query]
    try:
        # call on taxonkit. lazier to use os.popen - python-bindings exist but introduce a dependency.
        res = os.popen(f'echo {" ".join(taxons)} | taxonkit lca --data-dir {data_dir}').read().split()[-1]
    except IndexError:
        # in some cases, taxonkit fails because the taxonomy ID is not included. The above [-1] crashes.
        res = 'NA'
    result_line.append(res)
    print('\t'.join(result_line))

def main():
    DATA_DIR = '.' # Where taxonkit data is stored.

    parser = argparse.ArgumentParser(description='Parses blastn output, computes LCA for all queries using taxonkit.')
    parser.add_argument('blastn', metavar='FILE', type=str,
                        help='''Filename of blastn outfmt 6 output. Ideally
                        "6 qseqid sseqid staxids sscinames scomnames sskingdoms pident length
                        qlen slen mismatch gapopen gaps qstart qend sstart send stitle evalue bitscore qcovs qcovhsp"''')
    parser.add_argument('--data-dir', metavar='DIR', type=str, default=DATA_DIR,
                        help=f'Where taxonkit data is stored. Defaults to "{DATA_DIR}".')
    args = parser.parse_args()

    data_dir = args.data_dir

    current_query = None
    taxons = None

    with open(args.blastn) as fh:
        for line in fh:
            ll = line.split()
            query = ll[0]
            taxid = ll[2]
            if ';' in taxid:
                # in some cases, an NCBI-NT entry has several taxonomy IDs like 1;2;321;5123413.
                # It seems that these few entries have the entire taxonomy tree. Just use the last one.
                taxid = taxid.split(';')[-1]

            if current_query != query:
                if taxons:
                    call_on_taxonkit(current_query, taxons, data_dir)
                # printed all for the last query, now start collecting for the new query
                taxons = [taxid]
                current_query = query
            else:
                # current query is same as before, add to list
                taxons.append(taxid)

    # print for the very last query, too
    if taxons:
        call_on_taxonkit(current_query, taxons, data_dir)

main()