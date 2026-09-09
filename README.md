# zupload

## What is zupload?
`zupload` is a command-line tool for uploading scientific datasets and their
metadata to ICOS / ENVRI data portals in a structured and reproducible way.  

It uses a **spreadsheet-driven approach** to describe datasets, their metadata,
and the target portal. The tool then validates, prepares, and uploads both 
metadata and data files using the appropriate service APIs.

`zupload` is designed for:
- batch uploads of many files,
- preparing metadata in a way that is easy to review and reproduce,
- scripted or semi-automated ingestion workflows.

`zupload` is implemented as a set of **Typer-based CLI
commands** and uses an Excel (`.xlsx`) file as its primary input.

## How it works

At a high level, `zupload` turns a spreadsheet into a series of upload actions.

1. **You prepare an Excel file**  
   The spreadsheet describes your datasets: where the files are located, which
   metadata belongs to each file, and which ICOS / ENVRI portal to use.

2. **`zupload` reads the input**  
   The tool loads the spreadsheet and prepares the metadata in the format
   expected by the target services. The upload flow itself does not check the
   input, so a missing field surfaces as a raw error; you can check the input
   up front with the `validate` command (described later).

3. **Metadata is converted to JSON**  
   For each data file, `zupload` builds a metadata JSON payload based on the
   spreadsheet contents. This step can also be run on its own, without 
   uploading anything.

4. **Metadata is uploaded first**  
   The metadata JSON is sent to the portal's metadata service. If this
   succeeds, the service returns an upload URL for the actual data file.

5. **Data files are uploaded**  
   The data files are uploaded directly to the returned URL, completing the
   ingestion process.

This separation between metadata and data uploads makes it easier to validate,
debug, and reproduce uploads, especially when working with many files.

## Installation

`zupload` is a Python-based command-line tool.

Clone the repository and install it into a virtual environment of your choice:

```bash
git clone https://github.com/ICOS-Carbon-Portal/zupload.git
cd zupload
python -m venv .venv
source .venv/bin/activate
pip install .
```

This will install `zupload` and its dependencies and make the CLI commands
available in your environment.

**Note:** zupload is currently intended to be used from a Python environment
rather than as a standalone binary.

## Authentication

`zupload` relies on the standard ICOS authentication flow provided by the
`icoscp_core` library. This means you don't have to worry about manually
handling tokens: as long as you're logged in with ICOS credentials, the 
library will handle retrieving and attaching the necessary authentication to
every request.

To authenticate, follow the instructions in the `icoscp_core` documentation:
https://icos-carbon-portal.github.io/pylib/icoscp/authentication/

If authentication is missing or invalid, upload requests will fail with an
authorization error.

## Usage

`zupload` is used from the command line and operates on an Excel (`.xlsx`)
spreadsheet that describes the datasets to upload.

After activating your Python virtual environment and installing the library,
the `zupload` commands are available directly on the command line.

At a minimum, you point `zupload` to a spreadsheet file and run the upload
command. If no file is provided, `zupload` uses the single `.xlsx` file in the
current directory when there is exactly one; if there are several `.xlsx` files
it stops with an error and asks you to specify which one.

Typical usage looks like this:

```bash
zupload
```
or

```bash
zupload /path/to/spreadsheet.xlsx
```

This will:
- read the spreadsheet,
- prepare metadata for each listed data file,
- upload the metadata to the target portal,
- upload the corresponding data files.

Use `--metadata-only` to upload the metadata but skip uploading the actual data
file.

```bash
zupload /path/to/spreadsheet.xlsx --metadata-only
```

Use `--rows` to restrict the run to specific rows of the `upload_meta` sheet, by
that sheet's row number. `--rows 5` runs a single row, and `--rows 5-12` runs a
contiguous, inclusive range. This works on both the default upload command and
the `validate` command.

```bash
zupload /path/to/spreadsheet.xlsx --rows 5-12
```

By default `zupload` uploads to the portal's production environment. Use
`--staging` to send the metadata to the portal's staging environment instead,
which is useful for testing. Because production uploads are hard to undo, the
tool asks you to confirm before a production upload; pass `--yes` to skip that
confirmation, for example in scripts. Staging must already be set up for your
submitter on the portal side, otherwise the upload is rejected.

```bash
zupload /path/to/spreadsheet.xlsx --staging
```

Additional commands are available for preparing metadata without uploading
data, and for validating an upload before you run it.

When you want to prepare metadata without uploading, there are two options.
`--no-upload` does a dry run: it builds the metadata and prints it, but uploads
nothing and writes no files. `--extract-json` instead writes each row's
metadata JSON next to its data file.

```bash
zupload /path/to/spreadsheet.xlsx --extract-json
```

The `validate` command
inspects the spreadsheet rows and reports any problems without uploading
anything or changing the spreadsheet. It separates findings into errors
(clearly wrong input, such as a missing required field) and warnings (things
that look suspicious but may be fine). It checks the metadata only, so it works
even when the data files are not present locally. It also reports, for each
row, whether it can find the data file at its `fileLocation`; when a file
cannot be found it tells you how to rerun with `--data-dir` to locate the
files and fill in the missing details.

Unlike the upload command, `validate` takes the spreadsheet as the
`--spreadsheet` option rather than as a positional argument.

```bash
zupload validate --spreadsheet /path/to/spreadsheet.xlsx
```

If the data files are available locally but the spreadsheet is missing their
`hashSum` or `fileLocation`, point `validate` at the folder that contains them
with `--data-dir`. It finds each file by name (searching subfolders as well)
and fills in `fileLocation` and `hashSum` directly in the spreadsheet. If it
finds no matching files under that folder, it leaves the spreadsheet unchanged.

```bash
zupload validate --spreadsheet /path/to/spreadsheet.xlsx --data-dir /path/to/data
```

The `fetch` command retrieves the existing metadata for an object from the
portal and prints it. It is a read-only lookup and uploads nothing. You can pass
a PID, a hash, or a landing-page URL.

```bash
zupload fetch <pid|hash|landing-url>
```

The `generate` command scaffolds a new upload spreadsheet from a directory of
data files. It is currently specialized for ICOS Cities footprint NetCDF files,
so most users preparing a normal upload should start from an existing working
spreadsheet instead.

```bash
zupload generate /path/to/directory
```

## Harvesting metadata from the portal (`harvest`)

`harvest` works in the opposite direction to `zupload`: instead of sending a
spreadsheet to the portal, it brings the portal back into a spreadsheet. It
only ever writes to a spreadsheet; it uploads nothing.

`harvest` is installed as its own command, not as a `zupload` subcommand.

It has two modes:

- **Build a new spreadsheet** from one or more landing page URIs, with
  `--landing-page`. No input spreadsheet is needed. This is the recommended
  way to start.
- **Fill in an existing spreadsheet** whose `upload_meta` sheet already has
  the `landingPageURI` column filled in, by pointing `harvest` at the file.

### Building a new spreadsheet from landing page URIs

Give `harvest` one or more landing page URIs and it fetches those objects and
writes a brand-new workbook containing both sheets `zupload` expects. The
`--landing-page` flag is repeatable, and produces one row per URI.

```bash
harvest --landing-page https://meta.icos-cp.eu/objects/6TNdmGyjojb8iLTQ3acDs3-F
harvest --landing-page <uri-a> --landing-page <uri-b> --output my_sheet.xlsx
```

`--output PATH` names the workbook; without it, the file is `harvest.xlsx` in
the current directory.

**A generated sheet carries every column `zupload` reads**, left blank where
the portal has nothing to put in them. This is why generating is the
recommended starting point: the sheet is complete by construction, so nothing
is missing except the values only you can supply. Running `zupload validate`
on a generated sheet reports no schema errors and no schema warnings.

In practice a generated sheet needs only one thing filled in before `zupload`
will take it: **`fileLocation`**, the directory holding the data file, which is
local information the portal does not have. Fill it with:

```bash
zupload validate --spreadsheet <sheet> --data-dir <dir>
```

`harvest` will not write over an existing file. If the output path is already
taken it stops with an error such as
`harvest.xlsx already exists, and harvest will not write over it.` and suggests
either `--output <other path>` or moving the existing file out of the way.
Note that `--overwrite` is **not** the way to replace an output file: that flag
only ever means "replace cells that disagree with the portal", and in this mode
it does nothing (`harvest` prints a note saying so).

The `envri_info` sheet is created with a single `portal` value derived from the
landing page host, so both portals work with no extra flag: `meta.icos-cp.eu`
gives `icos` and `citymeta.icos-cp.eu` gives `icoscities`. Because a
spreadsheet names exactly one portal, all the URIs in one run must be on the
same host; a mixed set stops with an error listing each host and how many URIs
it had.

`--landing-page` cannot be combined with a spreadsheet path or with `--rows`.
Each combination stops with an error explaining why.

`--dry-run` writes no workbook. It prints the portal, the number of rows, and
the full list of columns it would create, leaving only the `logs/` directory
behind.

A URI that cannot be fetched still gets a row, carrying just its
`landingPageURI`, so a later plain `harvest` on the sheet retries it. If every
URI fails, no workbook is written at all.

Running plain `harvest` on a freshly generated sheet reports no changes and
leaves the file byte-identical, so there is no "generate, then harvest again"
step to remember: the two modes agree.

The columns are the ones `zupload` reads, in the order used by the spreadsheet
template. Which columns appear depends on the dataset types involved: a single
station-timeseries object gives 26 columns, and adding a spatiotemporal object
brings it to 29 — the union of the two, with `resolution`, `forStation`, and
`variablesToIngest` appended after the station-specific block.

When the URIs span both dataset types `harvest` still writes the sheet, but
warns:

```text
Warning: these URIs mix dataset types (spatioTemporal, stationTimeSeries). zupload uses a single dataset type per upload, so one sheet per type is safer.
```

The reason is that `zupload` picks one dataset type per upload run and applies
it to every row, so on a mixed sheet it would build the wrong `specificInfo`
for the rows of the minority type. Keeping one sheet per dataset type is the
safe habit.

### Filling in an existing spreadsheet

Point `harvest` at an `.xlsx` whose `upload_meta` sheet already has the
`landingPageURI` column filled in, and it fetches each object's metadata from
the portal and writes it into the remaining columns of the same sheet, in
place.

The intended workflow is:

1. fill in `landingPageURI` for the objects you care about,
2. run `harvest` to pull their metadata into the sheet,
3. review and edit the sheet by hand,
4. run `zupload` to upload the updated metadata.

```bash
harvest                                  # picks the only *.xlsx in CWD
harvest /path/to/spreadsheet.xlsx
harvest sheet.xlsx --rows 5              # one row by upload_meta row number
harvest sheet.xlsx --rows 5-12           # contiguous range, inclusive
harvest sheet.xlsx --dry-run             # report what would change, write nothing
harvest sheet.xlsx --overwrite           # replace cells that disagree with the portal
```

Spreadsheet resolution works exactly as it does for `zupload`: leave the path
out and `harvest` uses the single `.xlsx` file in the current directory, and
stops with an error if there are several. `--rows` also behaves the same way,
taking `upload_meta` sheet row numbers, either a single row (`--rows 5`) or a
contiguous, inclusive range (`--rows 5-12`).

### What `harvest` writes

When filling an existing sheet, `harvest` writes only to blank cells by
default. If a cell already holds a value
that disagrees with the portal, it leaves your value in place, reports the
difference, and tells you to rerun with `--overwrite` to replace them. This is
deliberate: work you entered by hand is never destroyed unless you ask for it.

Values are compared intelligently, so a cell is not flagged as disagreeing
merely because it is written differently. Hexadecimal and base64url hash sums,
`http://` and `https://`, `3744` and `3744.0`, and timestamps ending in `Z`
versus `+00:00` all count as agreement. As a result, running `harvest` twice in
a row changes nothing the second time.

`--dry-run` reports what would change and writes nothing at all; the
spreadsheet is left byte-identical.

`harvest` never writes `fileLocation`, because that column holds a local
directory path rather than portal metadata. Use
`zupload validate --spreadsheet <sheet> --data-dir <dir>` to fill that column.

Columns that the sheet does not yet have are added as needed. A row with a
blank `landingPageURI` is skipped. A row whose object cannot be fetched is
reported and skipped without aborting the run, so the remaining rows are still
harvested.

`harvest` works against both the ICOS and Cities portals with no extra flags,
because it derives the portal host from the landing page URI itself. If that
host disagrees with the portal named in the `envri_info` sheet, it warns once
and carries on.

Because it writes to a spreadsheet, `harvest` writes a run log directory under
`./logs/` in both modes — `./logs/harvest-<timestamp>/` — keeping before and
after copies of the workbook, and prints `Logs saved to <dir>` when it
finishes. This is the same logging the upload command, `generate`, and
`validate --data-dir` do, which use a `zupload-<timestamp>` directory instead.
In generation mode there is no "before" copy, because the spreadsheet does not
exist yet when the run starts.

### Things to know before you upload a harvested sheet

These apply to both modes.

**Re-uploading a harvested sheet updates the same object's metadata in place.**
It does not create a new version. This is the point of the workflow: harvest an
object, edit a field such as the title, run `zupload`, and the object's
metadata is updated.

**`isNextVersionOf` mirrors what the portal reports.** `harvest` copies the
object's own `isNextVersionOf`, converted to id form: if the portal reports no
predecessor the cell is left blank, one predecessor becomes a bare id such as
`LY07JgXMJYhqEVrvfRosjqNI`, and several become a JSON list of ids.

Two things follow from that:

- **The column takes an object id, not a URL.** Putting a landing page URI in
  it is rejected with HTTP 400 and
  `Could not parse SHA-256 hashsum, expected a 32- or 18-byte array`. The
  32-byte form is the full `hashSum`; the 18-byte form is the object id.
- **`harvest` must not invent a value here, and neither should you.** An
  object's identity *is* its hash: the object id is literally the first 24
  characters of the 43-character `hashSum`. Since `harvest` also copies
  `hashSum`, writing that same id into `isNextVersionOf` would make the object
  point at itself, which the portal rejects with
  `Data/doc object cannot be a next version of itself`. Edit that cell only to
  correct a genuine mistake in the original upload.

**`keywords` usually comes back empty, and that is fine.** Object-level
keywords are optional, and the portal holds none for many objects, so
`harvest` leaves the cell blank. Note also that the keywords shown on a landing
page may belong to the object specification rather than to the object itself,
which is why `harvest` does not copy those.

**Staging can reject harvested metadata for reasons that are not about your
sheet.** Harvested metadata references production resources — people,
organisations, stations, instruments, spatial coverages — and the staging
metadata store can lag production. A staging upload may therefore fail on a
reference that is perfectly valid in production, for example
`Invalid contributor URL http://meta.icos-cp.eu/resources/people/Stijn_Naus`
for a person who exists in production but is missing from staging. Staging
checks the shape of the payload well, but it can give false negatives on
resolving references.

You can check a harvested sheet at any point without uploading:

```bash
zupload validate --spreadsheet /path/to/spreadsheet.xlsx
```

## Input spreadsheet

`zupload` uses an Excel (`.xlsx`) spreadsheet as its main input. The 
spreadsheet describes which files should be uploaded, which metadata belongs to
each file, and which portal the upload targets.

Each upload workflow may require a slightly different spreadsheet layout,
depending on the type of data and the target service. For this reason, the
spreadsheet format is intentionally not fully fixed or documented in detail
here.

Example spreadsheets are not yet included with the project. Until they are, base
your new spreadsheet on an existing working spreadsheet, and use its
`instructions` sheet (described below) as your guide to the required sheets,
columns, and value formats.

Spreadsheets also contain an **`instructions` sheet** with additional guidance
and explanations for the different fields. This sheet is meant for human
readers only and is ignored by `zupload` when processing the file.

When preparing a spreadsheet:
- each row typically corresponds to a single data file,
- file paths must be accessible from the machine running `zupload`,
- some fields may contain JSON-formatted values (for example lists of variables
  or keywords).

Basing your spreadsheet on an existing working spreadsheet, and following its
`instructions` sheet, is the recommended way to ensure your spreadsheet matches
what `zupload` expects.

## Things to be aware of

- `zupload` expects the spreadsheet structure and column names to match what
  the tool reads internally. Basing your spreadsheet on an existing working
  spreadsheet, and following its `instructions` sheet, is strongly recommended.
- Some spreadsheet fields are expected to contain valid JSON (for example lists
  of variables or keywords). Make sure these values use proper JSON syntax.
- A spreadsheet produced by `harvest` still needs `fileLocation`, which is
  never harvested because it is a local path rather than portal metadata. Run
  `zupload validate --spreadsheet <sheet>` on a harvested sheet before
  uploading it.
- Uploading a harvested sheet updates the metadata of the object it was
  harvested from; it does not create a new version of it.
- Metadata is uploaded before data files. If metadata upload fails, the data
  file will not be uploaded.
- Data files must be accessible from the machine running `zupload` at the paths
  specified in the spreadsheet.
- Authentication must be set up before running `zupload`. Missing or expired
  credentials will cause uploads to fail.

## Credits

`zupload` was developed within the ICOS / Carbon Portal ecosystem.

Contributors:
- Jonathan Schenk  
- Jonathan Thiry  
- Maggie Hellström  
- Oleg Mirzov  
- Ute Karstens  
- Claude
