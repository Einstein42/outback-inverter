#!/usr/bin/python
""" Node Server for Polyglot 
      by Einstein.42(James Milne)
      milne.james@gmail.com"""

from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector
from outback_types import OutbackNode

VERSION = "0.1.1"


class OutbackNodeServer(SimpleNodeServer):
    """This is a comment for the NodeServer"""
    controller = None
    inverter_master = None
    inverter_slaves = []
    sunspec = None
    flexnet = None

    def setup(self):
        manifest = self.config.get('manifest',{})
        self.poly.logger.info("FROM Poly ISYVER: %s", self.poly.isyver)        
        self.controller = OutbackNode(self,'outbackaxs','Outback Control', True, manifest)
        self.controller.addInverters(self.controller)
        # Close active connection. We don't keep it open if we don't need it.
        self.controller.closeConnection()
        self.update_config()
        
    def poll(self):
        pass

    def long_poll(self):
        pass
        
def main():
    """Setup connection, node server, and nodes"""
    poly = PolyglotConnector()
    # Override shortpoll and longpoll timers to 5/30, once per second is excessive in this nodeserver 
    nserver = OutbackNodeServer(poly, 5, 30)
    poly.connect()
    poly.wait_for_config()
    poly.logger.info("Outback Interface version " + VERSION + " created. Initiating setup.")
    nserver.setup()
    poly.logger.info("Setup completed. Running Server.")
    nserver.run()
    
if __name__ == "__main__":
    main()
