print "logging in locally"

from hydra_client import JSONConnection

x = JSONConnection()
x.login()

print "logging in remotely using JSON"

from hydra_client import RemoteJSONConnection
x = RemoteJSONConnection()
x.login()


