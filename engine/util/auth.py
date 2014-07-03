from hmac import *
import hashlib
import time
import random
import datetime
import uuid
import string
import imp
import platform
from socket import error, socket, AF_INET, SOCK_STREAM,SOCK_DGRAM, inet_ntoa,gethostname
from optparse import OptionParser
from subprocess import Popen, PIPE, STDOUT
import struct
from const import one_day_in_seconds, three_months_in_seconds


SECRET_KEY = "sgsdfgsdfgdfgbdfgb"
API_KEY = "wsdfasfgsdfg"

try:
    from hashlib import sha1
    sha = sha1
except:
    import sha

fcntl_module_exists = False
fcntl_module = None
if 'Linux' in platform.system():
    module = "fcntl"
    fp, pathname, description = imp.find_module(module)
    try:
        fcntl_module = imp.load_module(module, fp, pathname, description)
        fcntl_module_exists = True
    finally:
        if fp:
            fp.close()
    
class Network:
    def __init__(self):
        self.hostname = None
        self.domain   = None

    def getHostName(self):
        proc   = Popen(['hostname','-A'],stdout=PIPE,stderr=PIPE)
        result = proc.wait()
        if result == 0:
            self.hostname = proc.stdout.read()
        return self.hostname

    def getDomain(self):
        proc   = Popen(['hostname','-d'],stdout=PIPE,stderr=PIPE)
        result = proc.wait()
        if result == 0:
            self.domain = proc.stdout.read()
        return self.domain

    def getHostByDomain(self):
        host = str(self.getHostName())
        if len(host) == 0:
            host = str(self.getHostName())+"."+str(self.getDomain())
        return host

    def getHost(self):
        self.hostname = gethostname()
        return self.hostname

    def getIpAddress(self,iface): # getIpAddress('eth0')
        if platform.system == "Linux" and fcntl_module_exists == True:
            s = socket(AF_INET, SOCK_DGRAM)
            ipAddr  =  inet_ntoa(fcntl_module.ioctl(s.fileno(),0x8915,struct.pack('256s', iface[:15]))[20:24])
            return str(ipAddr)
        else:   # on windows
            ipAddr = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
            return str(ipAddr)

    def getHwAddr(self,ifname=None):   # getHWAddr('eth0')
        if 'Linux' in platform.system() and fcntl_module_exists == True:
            if ifname == None:
                raise Exception('eth not specified!')
            s = socket(AF_INET, SOCK_DGRAM)
            info = fcntl_module.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
            hwaddr = ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
            return str(hwaddr)
        else:
            '''
                http://docs.python.org/library/uuid.html
                uuid.getnode() :
                    Get the hardware address as a 48-bit positive integer. The first time this runs,
                    it may launch a separate program, which could be quite slow. 
                    If all attempts to obtain the hardware address fail, we choose a random 48-bit number 
                    with its eighth bit set to 1 as recommended in RFC 4122.
                    "Hardware address" means the MAC address of a network interface,
                    and on a machine with multiple network interfaces the MAC address of 
                    any one of them may be returned. 
            '''
            import uuid
            mac_address = str(hex(uuid.getnode()))
            hwaddr = mac_address.replace("0x", "").replace("L", "").upper()
        return str(hwaddr)

'''
    Generate AuthToken
'''    
class AuthToken(object):
    
    def __init__(self, key=None, secret=None, iface='eth0'):
        self.key = key
        self.secret = secret
        self.iface = iface
    
    def simple_hash(self,nchars=16):
        chars = string.printable
        hash = ''
        for string.printable in xrange(nchars):
            rand_char = random.randrange(0,len(chars))
            hash += chars[rand_char]
        return hash   
    
    def expire_in_24h(self):
        '''return a UNIX style timestamp representing 24 hours from now'''
        return int(time.time() + one_day_in_seconds)
    
    def expire_in_1month(self):
        return int(time.time() + three_months_in_seconds)
    
    def expire_in_3months(self):
        '''return a UNIX style timestamp representing 3 months from now'''
        return int(time.time() + three_months_in_seconds)
    
    def shuffle_word(self,word):
        ''' shuffle word '''
        return ''.join(random.sample(word,len(word)))
    
    def sha_key(self,key,secret_word):
        crypted_string = self.shuffle_word(key + str(time.time()) + secret_word)
        return sha(crypted_string).hexdigest()
    
    def generate_uid(self):
        return sha1(str(time()) + str(random.randrange(1000000))).hexdigest()
    
    def generate_uuid(self, tip=None):
        '''
            generate unique ID
        '''
        current_time = long(round(time.time() * 1000))
        if tip is None:
            tip = random.random()
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(current_time)+str(tip))

    @staticmethod
    def password_hash(password, algorithm='sha512'):
        return hashlib.new(algorithm, password).hexdigest()
    
    def generate_auth_token(self):
        net = Network()
        ''' Get web server MAC address for default iface eth0''' 
        mac = net.getHwAddr(self.iface)
        return self._compose_key(mac)
    
    def _compose_key(self, mac):
        if self.key is None:
            self.key = SECRET_KEY
        ''' create secret key '''
        key = "%s%s%s" % (self.key, mac, str(self.expire_in_24h()))
        ''' shuffle key '''
        key = self.shuffle_word(key)
        return self.sha_key(key, API_KEY)


def test_token():
    token = AuthToken()
    otoken = token.generate_auth_token()
    print "Generated token: " + str(otoken)
    

if __name__ == "__main__":
    test_token()
