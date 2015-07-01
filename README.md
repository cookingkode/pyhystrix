#pyhystrix
## Python Implementation of the Hystrix Command Pattern

This project is inspired by the Netflix Hystrix project :http://techblog.netflix.com/2012/02/fault-tolerance-in-high-volume.html

The initial commit contains implementation for the Command pattern. Once can define a function, timeout and a fallback. When a timeout is specified, the command gets executed in a **separate** Python process

The code needs rabbit-mq server running locally. 

For configuring logging , please see tests/hello_world.py

## Show me some code

```python
import sys, time
from pyhystrix.command import Command

# Subclass Command and provide run(thing to do) and fallback(what happens
# when run fails or there is a timout
class AddCommand(Command):

    def run(self, x , y):
        time.sleep(4)
        return int(x)+int(y)

    def fallback(self, x , y):
        print "Timeout!"
        return 1000



addcmd = AddCommand()
print addcmd.execute(4, 4) #this will execute synchronously
print addcmd.execute_with_timeout(3, 5, 4) #this will execute in a background thread with timeout
AddCommand.kill() #cleanup
```

## Install 

```
pip install -r requirement.txt
python setup.py install

rabbitm-mq 

python test/hello_world.py
```
