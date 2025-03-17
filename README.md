# dupfs

dupfs is the draft of a FUSE filesystem that duplicates every operation onto two underlying directories.

**Warning: do not use in production!** This is only a proof of concept.

## Usage

```
uv venv
source .venv/bin/activate
uv pip install -r ./requirements.yml
make
```

As long as dupfs runs, all writes to `/mountpoint` will be written to `/primary` **and** `/secondary`.


## Caveats

* Files already existing in primary directory won't be copied to secondary. Manual stage would be necessary.
* No error handling. Error in secondary can prevent the FS to work. Remember this is not for production ;-)
