import sys
import os
import metadata
import table
import query

if __name__ == "__main__":
    meta = metadata.metaData('./files/metadata.txt')
    meta.printData()
    tables = {}
    for tab in meta.dict:
        tables[tab] = table.Table(tab, meta)

    q = query.Query(meta, tables)
    q.process(sys.argv[1])
