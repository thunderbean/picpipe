#!/usr/bin/env python
# coding=utf-8

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.api import memcache

import urllib
import os
import md5
import logging
import time

class WebImageHandler(webapp.RequestHandler):
    def get(self, url):
        url     = urllib.unquote_plus(url)
        if url.find('picpipe.appspot.com') is not -1:
            logging.error('cycle request found')
            self.response.out.write('nothing is here')
            return
        width   = self.request.get('width', 0)
        height  = self.request.get('height', 0)
        width   = int(width)
        height  = int(height)
        mc_key = '%s_%d_%d' % (md5.new(url).hexdigest(), width, height)
        img = memcache.get(mc_key)
        if img is None:
            logging.info('cache missed: %s' % mc_key)
            self.response.headers['x-cache'] = 'miss'
            try:
                result = urlfetch.fetch(url)
                img = result.content
                memcache.set(mc_key, img, 3600*24*7)
                self._set_browser_expire()
            except:
                logging.info('url not found: %s' % url)
                img = open(
                    os.path.join(os.path.dirname(__file__), '404.png'), 'rb').read()
                widht = width or 200
                height = height or 200
        else:
            logging.info('from cache %s' % mc_key)
            self.response.headers['x-cache'] = 'cached'
            self._set_browser_expire()
        if width or height:
            img = images.resize(
                img,
                width,
                height,
                images.JPEG
            )
        self.response.headers['Content-Type'] = 'image/jpg'
        self.response.out.write(img)
        
    def _set_browser_expire(self):
        self.response.headers['Cache-Control'] = 'max-age=%d, public, must-revalidate' % (3600*24*7)
        self.response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(time.time() + 3600*24*7))        


def main():
    application = webapp.WSGIApplication([
        ('/(.*)', WebImageHandler)
        ], debug=True)

    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
