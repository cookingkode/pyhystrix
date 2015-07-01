import sys, time, logging
sys.path.append('../')
from pyhystrix.command import Command

logging.basicConfig(
    format='%(asctime)s.%(msecs)s:%(name)s:%(thread)d:%(levelname)s:%(process)d:%(message)s',
    filename='/tmp/pyhystrix',
    level=logging.INFO
    )

logger = logging.getLogger('pyhystrix')
logger.setLevel(logging.INFO)


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
AddCommand.kill()
