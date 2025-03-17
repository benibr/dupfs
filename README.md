# dupfs

dupfs is the draft of a FUSE filesystem that duplicates every operation onto two underlying directories.

**Warning: do not use in production!** This is only a proof of concept.

## Usage

## TODO:
 * add map for FDs
 * full function support
 * README with examples and explenation

## Caveats

* Files already existing in primary directory won't be copied to secondary. Manual stage would be necessary.
* No error handling. Error in secondary can prevent the FS to work. Remember this is not for production ;-)
