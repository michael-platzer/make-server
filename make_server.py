#!/usr/bin/env python3

# Licensed under the MIT License, see LICENSE.txt for details
# SPDX-License-Identifier: MIT

import argparse

parser = argparse.ArgumentParser(
  description = "HTTP server that accepts files via HTTP's PUT method, "
                "executes a Makefile, and returns an archive "
                "containing the build products.",
  epilog      = "example: make_server.py -p 8090 -o *.png -o report.pdf /path/to/my/Makefile"
)
parser.add_argument('Makefile')
parser.add_argument('-p', '--port', type=int, default=8000,
  help="the port number on which the HTTP server shall listen, defaults to 8000"
)
parser.add_argument('-o', '--output', action='append', default=[],
  help="files to return to the host (supports Unix style pathname pattern expansion)"
)
args = parser.parse_args()

import http.server
import socketserver
import tempfile
import os
import subprocess
import mimetypes
import glob
import zipfile

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
  def do_PUT(self):
    with tempfile.TemporaryDirectory() as dname:
      dpath  = os.path.abspath(dname)
      ifpath = os.path.join(dpath, os.path.basename(self.path))

      try:
        iflen = int(self.headers.get('Content-Length', None))
      except TypeError:
        self.send_response(411, 'Length Required')
        self.end_headers()
        self.wfile.write(b'The request content appears to be empty.\n')
        return

      ifpos = 0
      with open(ifpath, 'wb+') as outf:
        while ifpos < iflen:
          data   = self.rfile.read(min(65536, iflen - ifpos))
          ifpos += len(data)
          outf.write(data)

      proc = subprocess.run([
        '/bin/sh', '-c', f"cd {dpath} && make -f {os.path.abspath(args.Makefile)}"
      ], capture_output=True)

      if proc.returncode != 0:
        self.send_response(500, 'Command error')
        self.end_headers()
        self.wfile.write(proc.stderr)
        return

      mimes   = [val.split(';', 1)[0] for val in self.headers.get('Accept', '').split(',')]
      ofglobs = args.output + [
        f"*{ext}" for mime in mimes for ext in mimetypes.guess_all_extensions(mime)
      ]
      ofpaths = [path for name in ofglobs for path in glob.glob(name, root_dir=dpath)]

      ozpath = os.path.join(dpath, 'resp.zip')
      with zipfile.ZipFile(ozpath, 'w') as zipf:
        for ofpath in ofpaths:
          zipf.write(os.path.join(dpath, ofpath), ofpath)

      self.send_response(201, 'Created')
      self.end_headers()
      with open(ozpath, mode='rb') as oz:
        self.wfile.write(oz.read())

    def do_GET(self):
      self.send_response(404, 'Not Found')
      self.end_headers()
      self.wfile.write(b'')

if __name__ == '__main__':
  with socketserver.TCPServer(("", args.port), HTTPRequestHandler) as httpd:
    httpd.serve_forever()
