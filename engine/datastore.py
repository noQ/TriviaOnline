'''
Created on Jan 20, 2012

@author: Adrian Costia

'''
from mongoengine import connect
from util import configparser as cfg

class DataStoreConnectionError(Exception):
    pass

class DataStore(object):
    _cfgFileDataStore   = "DB"
    _cfgServerAddrOpt   = "server_address"
    _cfgServerPortOpt   = "port"
    _cfgUser            = "username"
    _cfgPassword        = "password"
    CFG_REPLICASET = "replicaset"
    
    _defaultServerAddr  = "localhost"
    _defaultServerPort  = 27017
    
    '''
        Initialize data store connection
         - params: collection - database
        Example: DataStore("users") , where users is the collection
         
    '''
    def __init__(self, db, port=27017):
        self.username   = None
        self.password   = None
        self.has_credentials = False
        self.collection = db
        self.db_connection = None
        self.use_replicaset = False
        self.replicaSet = None
        
        # loading configuration from web.cfg if section [DB] is present
        if cfg.Config.getConfig().has_section("DB"):
            # read option server address
            if cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgServerAddrOpt) is None:
                self.serverAddr = DataStore._defaultServerAddr
            else: # read from config
                self.serverAddr = cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgServerAddrOpt)
            # read option server port
            if cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgServerPortOpt) is None:
                self.serverPort = DataStore._defaultServerPort
            else:
                self.serverPort = cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgServerPortOpt)
            ''' check if replica set is enabled '''
            if cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore.CFG_REPLICASET) is not None:
                self.replicaSet = cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore.CFG_REPLICASET)
                self.use_replicaset = True
        else:
            self.serverAddr = DataStore._defaultServerAddr
            self.serverPort = DataStore._defaultServerPort
        
        try:
            self.username = cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgUser)
        except Exception:
            pass
        
        try:
            self.password = cfg.Config.getValue(DataStore._cfgFileDataStore, DataStore._cfgPassword)
        except Exception:
            pass
        
        if self.username is not None and self.password is not None:
            self.has_credentials = True

    def connect(self):
        try:
            if self.has_credentials == True: # connect using credentials
                self.db_connection = connect(
                        self.collection,
                        host=self.serverAddr, port=self.serverPort,
                        username=self.username, password=self.password
                        )
            else:
                if self.use_replicaset:
                    port = int(self.serverPort)
                    self.db_connection = connect(self.collection, **{ 
                                                                     "host" : self.serverAddr,
                                                                     "port":port,
                                                                     "replicaSet" :self.replicaSet,
                                                                     "read_preference" : True
                                                                     })                    
                else:
                    self.db_connection = connect(
                                                 self.collection,
                                                 host=self.serverAddr,
                                                 port=int(self.serverPort)
                                                  )
            return self.db_connection
                
        except Exception, e:
            raise DataStoreConnectionError("Cannot connect to the database:\n%s" % e)
    