import base64
import md5
import sys
import pickledb

class UrlShortener:
    def __init__(self, url_prefix='http://l.cfg.sh/'):
        self.db         = pickledb.load('links.db', False)
        self.url_prefix = url_prefix

    def shortcode(self, url):
        """
        Our main shortening function. The rationale here is that
        we are relying on the fact that for similarly sized inputs
        such as URLs the potential for collision in the 32 last bits
        of the MD5 hash is rather unlikely.
        
        The following things happen, in order:
        
        * compute the md5 digest of the given source
        * extract the lower 4 bytes
        * base64 encode the result
        * remove trailing padding if it exists
        
        Of course, should a collision happen, we will evict the previous
        key.
        
        """
        return base64.b64encode(md5.new(url).digest()[-4:]).replace('=','').replace('/','_')

    def shorten(self, url):
        """
        The shortening workflow is very minimal. We try to
        set the redis key to the url value. We catch any
        exception in the process to properly report failures
        in the client
        """

        code = self.shortcode(url)
        
        try:
            self.db.set(code, { 'id': url, 'count' : 0 })

            return {
                    'success'  : True,
                    'url'      : url,
                    'code'     : code,
                    'shorturl' : self.url_prefix + code
            }
        except:
            return { 'success' : False }

    def lookup(self, code):
        """
        The same strategy is used for the lookup than for the
        shortening. Here a None reply will imply either an
        error or a wrong code.
        """
        try:
            val           = self.db.get(code)
            val['count'] += 1

            self.db.set(code, val)

            return val['id']
        except:
            return None
