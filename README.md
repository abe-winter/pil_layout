# pil_layout

Basic layout engine for PIL rescued from an in-house codebase.

If you're looking to use a declarative spec to combine images and text into a new image, this may be for you.

File a ticket if you want to use this and need basic docs.

## Example

(todo)

## Why PIL layout

I think other people are using headless browsers + CSS to do this, but short of embedding chrome I think there isn't a go-to way to do this with python.

If you're generating images on a python web server from a mix of other images, this may be a good choice.

## Status

Basic things work (padding, axis layout + flex, text wrapping) but some of the constraints processing is janky.

Test coverage exists but is sparse.

Not sure about speed or memory use -- guessing PIL uses a fair amount of memory.
