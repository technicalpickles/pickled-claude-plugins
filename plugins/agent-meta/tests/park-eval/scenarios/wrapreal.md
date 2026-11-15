Session so far (we did this work together, and I am handing it off):

We are in a small Python service called report-demo, on branch feat/csv-export.

The CSV export is finished, committed and merged upstream.

Two things the commits do not show. First, we chose to write the CSV as utf-8-sig on purpose, even though plain utf-8 is smaller: Excel garbles accented names without the BOM, and a downstream importer we tried first rejected the BOM, so the importer needs a fix. Second, nobody checked how the export behaves with more than a million rows, and that is still open.

Please wrap this session up as a close-out record. I am done.
