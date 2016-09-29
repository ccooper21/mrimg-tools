# mrimg-tools

My intent for the `mrimg-tools` project is to provide tools for working with and maintaining Macrium Reflect image file (i.e. `.mrimg` files) outside of the Macrium Reflect application.  Information about Macrium Reflect can be found [here](http://www.macrium.com/).

Here are some examples of capabilities that these tools might provide:

- Verify an image
- Upon editing an image's contents, recalculate its verification hash codes
- Add/remove/change an image's embedded comment
- Convert an `.mrimg` image file to a `.dd` image file
- Rewrite a compressed image as an uncompressed image
- Rewrite an uncompressed image as a compressed image
- Flatten a differential backup into a single image file
- Flatten a set of incremental backups into a single image file

## What's Available Now

As of right now, the only function I have implemented is the ability to decompress the body of an image file.  This is actually a big deal as the compression algorithm used by Reflect is not a well known algorithm.  Rather, the algorithm used appears to be unique to Reflect, borrowing ideas from the [Lempel Ziv]([https://en.wikipedia.org/wiki/LZ77_and_LZ78]) family of compression algorithms.

## Decompressor Caution

The goal of writing the decompressor thus far has been to prove out the decompression algorithm's correctness.  In the interest of maintaining that focus, the decompressor does not yet implement proper buffering of the output data stream.  Specifically, the entire output data stream is buffered in memory before being written to disk.  This presently limits the use of this tool to working with relatively small image files.  The test images I have used thus far for testing were created from a virtual drive less than 100MB in size.
