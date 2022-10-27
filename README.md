# Minimal Python HTTP make server

Have you ever been in the situation
that you have a build script that needs to run in a container
but the source files are on your local machine
and/or you need the build products on your local machine?
Or even worse, are you forced to use Windows
but need to process files in a Unix environment?

So far, these scenarios required you to manually copy files back-and-forth
between a container or other form of build environment and your local machine.
These times are over now!
This repository provides a minimalistic Python HTTP server
that accepts files via HTTP's PUT method,
executes a Makefile,
and returns an archive containing the build products.
Execute this make server in your container as follows:
```
python3 make_server.py -o *.png -o report.pdf /path/to/my/Makefile
```
Note that option `-o` can be used to specify the build products
that shall be returned to the host
(supports Unix style pathname pattern expansion).
The positional argument is the Makefile to be executed.

Finally, use a tiny wrapper script on your local machine
to seamlessly upload, build, and download files
as if the build was happening locally.

On Windows, you might want to write a short batch script as follows,
which allows you to simply drag-and-drop the file
that you wish to process onto it
and the build products will magically appear in the same directory:
```
@echo off
curl -X PUT --upload-file "%~f1" --fail-with-body -o out.zip http://localhost:8000
if errorlevel 1 (
  type out.zip
  del out.zip
  pause
  exit /b %errorlevel%
)
tar -xf out.zip
del out.zip
```
