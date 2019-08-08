# SevenZipTools
A plugin for [fman](https://fman.io) that replicates a few of 7-zip's context menu functions.

## Testing
This plugin has only been tested on Windows 7 64-bit. I currently don't have a Linux system to test on, and I have no way to test on Mac.

## Use alternate 7-zip executable

By default all commands use the version of 7-zip packaged with fman. This is a 'lite' version with reduced archive format support. Because I need support for .rar archives, it's possible to specify an alternate 7-zip executable in the config file (SevenZipTools.json). For example:

```
"7zip": { "path": "C:\\Program Files\\7-zip\\7z.exe" }
```

This will automatically extend support to include .rar archives. Otherwise only .7z, .zip and .tar files are supported.
If configured, the alternate executable is used for all calls to 7-zip made by the commands in this plugin, but practically speaking there are no advantages to this as far as the other commands are concerned.
Note that support is based on extension, not MIME type.

## Archive support
I know the full version supports more than .7z, .zip, .tar and .rar, and the lite version probably supports more than .7z, .zip, and .tar, but these are all I have tested. Nevertheless it's possible to add support for other types with a config file entry. For example to add support for .iso:

```
"additional extensions": [ ".iso" ]
```

Note that support for .tar does not allow extraction of "nested" types like .tar.xz or .txz. There is no support for this type of archive at all; if you were to explicitly add support for .txz, presumably you'd extract a .tar file. Similarly, if you were to add support for .xz, extracting a .tar.xz would also presumably result in a .tar file. Further, double extensions like .tar.xz will not be detected even if added to the list.

Finally, it's also possible to disable extension checking altogether with the following config entry:

```
"ignore extension": true
```

## Commands added:

### Extract to opposite
Creates a directory in the opposite pane named after the archive under the cursor (minus extension) and extracts everything from that archive to the new directory.

If the intended destination directory already exists, the operation aborts

### Compress to opposite
Compresses everything in the working directory to a .7z archive in the opposite pane named after the working directory.

By default no arguments are passed to the compress command. An entry may be added to the config file to customize the command. For example, to set the compression level to "Ultimate" and enable multi-threading:

```
"compress args": [ "-mx9", "-mmt=on" ]
```

### Get hash
Gets the hash of the file or directory under the cursor. Currently there is no progress dialogue during hash generation, which can take significant time for large files or directories. Without a progress dialogue it's possible to "do stuff" while the hash is being generated, but I recommend waiting for the dialogue indicating the hash to appear.

Note that 7-zip has a unique way of computing the hash of a directory. Technically it returns two hashes, one for "data" and one for "data and names". This command makes use of the former, which computes the hashes of all the files in the directory (and its subdirectories), adds the hashes together, then returns the sum with the leftmost digits truncated such that it has the "expected" number of digits.

By default the hash method used is SHA256. 7zip also supports the CRC32, CRC64, SHA1 & BLAKE2sp hash methods. An alternate method may be specified in the config file. For example, to use CRC32:

```
"hash": "crc32"
```

Note that this will also override the default hash used for comparision (see below).

### Compare files
Gets the hash of the file or directory under the cursor of each pane, compares the hash strings, and shows a dialogue indicating if the files match or differ. If you were paying attention, you might think the "data and names" hash would be the right choice when comparing two directories. Unfortunately, this results in a mismatch if the only difference is the names of the directories being compared. There are workarounds for this, but frankly I don't like any of them. So for the time being directory comparison is data only, meaning that the names of files and subdirectories have no impact on comparison.

As with the "Get hash" command, there are no progress dialogues during generation of the hashes.

By default the hash method used is SHA256. See the description of the "Get hash" command for other supported hash methods. An alternate method may be specified in the config file. For example, to use CRC32:

```
"compare hash": "crc32"
```

## Credits
My `_7zipTaskWithProgress` class is a slightly modified version of the class of the same name in fman's `zip` module.
