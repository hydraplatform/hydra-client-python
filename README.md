# hydra-client-python
Hydra Platform client libraries for Python

Installation
------------

pip install hydra-client


Usage:
------

The hydra client can interact with both hydra-base and hydra-server. Here
we give an example of each, requesting a network from its ID.

Hydra Base
**********

```
import hydra_client as hc

hb_conn = hc.JSONConnection()

hb_conn.login(username='root', password='')

hb_conn.get_network(2)

```

Hydra Server
************

First, start hydra server:

```
hydra-server run

```

```
import hydra_client as hc

hb_conn = hc.RemoteJSONConnection(url='http://localhost:8080/json')

hb_conn.login(username='root', password='')

hb_conn.get_network({'network_id':1})

```
