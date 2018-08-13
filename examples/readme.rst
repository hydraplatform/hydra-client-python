This folder contains a few examples of how to build networks using a remote JSON connection.

1. Create a simple network.
   This is more-or-less the simplest way to add a network to hydra. Building the network dictionary by haand.
   This, however is inscalable

usage: 

```
python create_network_simple.py
```

```
python create_network_simple.py --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```

```
python create_network_simple.py --name='A network' --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```

2. This creates an empty network in Hydra (some nodes and links, but no attributes or data).
   This is a step towards building a network programatically.
usage: 

```
>> python create_empty_network.py
```

```
>> python create_empty_network.py --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```

```
>> python create_empty_network.py --name='A network' --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```

3. This creates a network with nodes, links, groups, attributes and data. This network
   also uses a template, allowing us to define node types. This enables validation and other cool stuff
usage: 

```
>> python create_network_with_data.py
```

```
>> python create_network_with_data.py --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```

```
>> python create_network_with_data.py --name='A network' --url 'http://myserver.com/json' --username='MYUSER' --password='MYPASS'
```


