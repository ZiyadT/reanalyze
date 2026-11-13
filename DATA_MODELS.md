# ReAnalyze data models

This file tracks the tables in ReAnalyze's database and explains what their
columns mean. It is written for the current project state: a table is listed
as implemented only when there is a SQLAlchemy model and an Alembic migration
for it.

Think of the database as a set of labeled filing cabinets. Each table is a
cabinet, each row is one folder, and each column is a kind of information
stored in every folder.

## Implemented tables

These tables have both a SQLAlchemy model and an Alembic migration.

### `users`

**Purpose:** Represents a person who owns workspaces and uploaded documents.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique user ID and primary key. |
| `email` | String (up to 320 characters) | Yes | User's unique email address; cannot be blank. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the user row. |

### `workspaces`

**Purpose:** A user's project folder for documents and saved reports. Deleting
a workspace in the app archives it rather than removing its row.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique workspace ID and primary key. |
| `owner_user_id` | Integer | Yes | User who owns the workspace; foreign key to `users.id`. |
| `name` | String (up to 200 characters) | Yes | Workspace name; cannot be blank. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the workspace row. |
| `archived_at` | Timezone-aware timestamp | No | When the workspace was archived; `NULL` means it is active. |

The `(owner_user_id, id)` pair is also unique so the database can verify that
a document linked to this workspace has the same owner.

### `documents`

**Purpose:** Represents one uploaded PDF. The PDF bytes live in file storage;
the database stores its display name and storage key.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique document ID and primary key. |
| `owner_user_id` | Integer | Yes | User who uploaded the document; foreign key to `users.id`. |
| `original_filename` | String (up to 255 characters) | Yes | Filename shown to the user; cannot be blank. |
| `storage_key` | String (up to 512 characters) | Yes | Unique generated name used to find the PDF in file storage; cannot be blank. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the document row. |

The `(owner_user_id, id)` pair is also unique so the database can verify that
the document and workspace in a membership row have the same owner.

### `workspace_documents`

**Purpose:** A membership link between one workspace and one document. It
allows the same user's document to appear in more than one of their workspaces.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique membership ID and primary key. |
| `owner_user_id` | Integer | Yes | Owner shared by the linked workspace and document. |
| `workspace_id` | Integer | Yes | Linked workspace ID. |
| `document_id` | Integer | Yes | Linked document ID. |
| `created_at` | Timezone-aware timestamp | Yes | Time the membership link was created. |

**Database rules:** A unique constraint prevents the same document from being
linked to the same workspace twice. Composite foreign keys make PostgreSQL
reject a link if the workspace and document have different owners. Deleting a
document removes its membership links. Archiving a workspace removes its
current document links but keeps the workspace row, so reports can remain
attached.

**Migration:** [0002_users_workspaces_documents.py](./backend/migrations/versions/0002_users_workspaces_documents.py)

### `embedding_configurations`

**Purpose:** Records how an embedding vector is produced and compared. An
embedding is a list of numbers that represents text, a bit like a coordinate
for finding similar passages on a map. These configuration rows are immutable:
if settings change, create a new row instead of editing the old one.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique ID for this configuration; the primary key. |
| `provider` | String | Yes | Service that provides the embedding model, such as OpenAI. Must not be blank or whitespace only. |
| `model_name` | String | Yes | Name of the embedding model. Must not be blank or whitespace only. |
| `model_version` | String | No | Optional provider version, when one is available. |
| `dimensions` | Integer | Yes | Number of values in each vector produced by this configuration. Must be greater than zero. |
| `normalization` | String | Yes | Vector normalization rule. Currently `none` or `l2` is allowed. |
| `similarity_metric` | String | Yes | Rule used to compare vectors. Currently `cosine`, `dot_product`, or `euclidean` is allowed. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the row. |

**Database rules:** PostgreSQL rejects invalid field values and updates to
configuration rows.

**Defined in:** [models.py](./backend/app/db/models.py)  
**Migration:** [0001_embedding_configurations.py](./backend/migrations/versions/0001_embedding_configurations.py)

### `document_chunks`

**Purpose:** Stores ordered text passages extracted from an uploaded PDF.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique chunk ID and primary key. |
| `document_id` | Integer | Yes | Document this passage came from; foreign key to `documents.id`. |
| `chunk_index` | Integer | Yes | Zero-based position of this chunk in the document. |
| `content` | Text | Yes | Extracted passage text. |
| `page_start` | Integer | Yes | First PDF page represented in the chunk, starting at page 1. |
| `page_end` | Integer | Yes | Last PDF page represented in the chunk. |

The database prevents duplicate chunk positions within one document and
rejects invalid page ranges.

### `chunk_embeddings`

**Purpose:** Stores the numeric representation of a chunk for one embedding
configuration.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique embedding ID and primary key. |
| `document_chunk_id` | Integer | Yes | Chunk represented by this vector; foreign key to `document_chunks.id`. |
| `embedding_configuration_id` | Integer | Yes | Configuration used to create the vector; foreign key to `embedding_configurations.id`. |
| `embedding` | Unbounded pgvector | Yes | Vector values. The database checks that the vector length matches the configuration's `dimensions`. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the embedding row. |

There can be one embedding for each chunk/configuration pair. A chunk can
therefore have multiple vectors if ReAnalyze later supports more than one
embedding configuration.

The vector uses pgvector's unbounded `vector` type. A database trigger checks
that each vector's actual length matches its configuration's `dimensions`.
The trigger is created in
[0003_chunks_embeddings_reports.py](./backend/migrations/versions/0003_chunks_embeddings_reports.py).

### `research_reports`

**Purpose:** Stores a successfully generated report in the workspace. The
prompt is not saved. Source names and page references are plain text inside
`report_text`.

| Column | Type | Required? | Description |
| --- | --- | --- | --- |
| `id` | Integer | Yes | Unique report ID and primary key. |
| `workspace_id` | Integer | Yes | Workspace where this report is saved; foreign key to `workspaces.id`. |
| `title` | String (up to 200 characters) | Yes | Short report title, generated with the report. |
| `report_text` | Text | Yes | Full report body, including plain-text source/page references. |
| `created_at` | Timezone-aware timestamp | Yes | Time PostgreSQL created the report row. |

**Migration:** [0003_chunks_embeddings_reports.py](./backend/migrations/versions/0003_chunks_embeddings_reports.py)

## Data associations

- One `user` can own many `documents` and many `workspaces`.
- `workspaces` and `documents` have a many-to-many relationship through
  `workspace_documents`. PostgreSQL enforces that both records have the same
  owner.
- One `document` has many `document_chunks`; each chunk belongs to one document.
- One `document_chunk` can have many `chunk_embeddings`, one per embedding
  configuration. Each `chunk_embedding` uses exactly one
  `embedding_configuration`.
- One `embedding_configuration` can be used by many `chunk_embeddings`.
- One `workspace` can have many saved `research_reports`; each report belongs
  to one workspace.

## Remaining work

There are no additional tables planned for the agreed MVP. The database schema
does not itself upload files, extract PDFs, generate vectors, or write reports;
those application features are still to be implemented.

**MVP workflow:** A user creates a workspace, adds PDFs, and submits a prompt
to generate a report using all documents currently in that workspace. The
prompt and failed generations are not saved. A successful report is stored as
text in PostgreSQL and can be downloaded as a `.txt` file.

**MVP citation limit:** Source names and page references appear as plain text in
the report. There is no separate citations table or link back to source chunks,
so ReAnalyze cannot automatically check a citation. Deleting a document also
deletes its chunks and embeddings; already-saved report text remains unchanged.

**MVP document rules:** Each upload has one document row and one set of chunks.
An edited PDF uploaded under a different name is a new document. Existing
documents are not reprocessed, and there is no document-version table.

**Ownership and deletion:** A document belongs to its uploader and can be added
only to that user's workspaces. Removing it from one workspace removes only
that membership link. Deleting it removes all its workspace links and derived
chunks and embeddings. Deleting a workspace archives it rather than physically
removing it, so saved reports stay attached.

**IDs:** Application tables will use integer primary keys for the MVP.

## Alembic's bookkeeping table

Alembic creates an `alembic_version` table when migrations are applied. It
stores the ID of the latest migration applied to the database. It is more like
a maintenance log on the filing cabinet than an application data table, so it
has no SQLAlchemy model here.

## What `mapped_column` means

`mapped_column` is SQLAlchemy's way to define one column on a model and connect
it to the Python attribute that represents it. In this example:

```python
id: Mapped[int] = mapped_column(Integer, primary_key=True)
```

- `id` is the attribute your Python code reads and writes.
- `Mapped[int]` tells SQLAlchemy and type-checking tools that this attribute
  represents a database value of type integer.
- `mapped_column(...)` describes the database column: its SQL type and rules.
- `primary_key=True` makes the column the row's unique identifier.

Think of it as labeling a form field: the Python attribute is the field's name,
and `mapped_column` tells the database what kind of answer belongs there and
what rules that answer must follow. SQLAlchemy uses these definitions to
create database metadata and translate between Python objects and database
rows. The Alembic migration separately applies the actual schema changes to
PostgreSQL.
