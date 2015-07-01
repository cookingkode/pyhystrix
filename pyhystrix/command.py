"""
Used to wrap code that will execute potentially risky functionality
(typically meaning a service call over the network) with fault and latency
tolerance, statistics and performance metrics capture, circuit breaker and
bulkhead functionality.
"""
from __future__ import absolute_import
import logging
import multiprocessing
import six
import pika
import uuid

log = logging.getLogger("pyhystrix")


class CommandWorker(object):
    def __init__(self, cmd, todo):
        self.run = todo
        """
            Multiprocessing will do a fork here; So object will have run
        """
        self.pool = multiprocessing.Process(target=self.task , args=(cmd,))
        self.pool.start()

    def kill(self):
        self.pool.terminate()

    def on_request(self, ch, method, props, body):
        args = body.split(",")
        log.info("[Worker Process] :: " + self.queue + " ARGS: " + str(args))
        response = self.run(None, *args)

        ch.basic_publish(exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id = \
                                                props.correlation_id),
            body=str(response))
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def task(self,q_name):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        except:
            log.exception("[ \n\n\nWorker Process] :: Rabbit-mq server connection error; is it running??\n\n\n\n")
            raise
        self.queue = q_name
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=q_name)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue=q_name)
        log.info( "[Main Process] Awaiting Response from Worker %s" %(q_name))
        self.channel.start_consuming()


class CommandMetaclass(type):
    """ Overrides creation of subclasses of Command. Most important task is to
        create a background process to offload tasks to
    """

    def __new__(cls, name, bases, attrs):
        #TODO can child be called Command?
        if name == "Command":
            return type.__new__(cls, name, bases, attrs)

        class_name = attrs.get('__command_name__', None) or name
        attrs['_worker'] = CommandWorker(class_name, attrs['run']).pool
        attrs['_command_name'] = class_name

        new_class = type.__new__(cls, class_name, bases, attrs)
        #setattr(new_class, 'command_name', class_name)

        return new_class


class Command(six.with_metaclass(CommandMetaclass, object)):
    """ Base Class for all commands to be enriched with pyhystrix.
        example :

        class AddCommand(Command):

            def run(self, x , y):
                return int(x)+int(y)

            def fallback(self, x , y):
                return 1000

        Important Note : The 'run; method should be treated as a staticmethod
        since it's execution might happen in the background worker context.
        'fallback' always run in the context of current process

    """

    def __init__(self, timeout=None):
        self.timeout = timeout
        self.timedout = False
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        except:
            log.exception(" \n\n\n Rabbit-mq server connection error; is it running? \n\n\n")
            raise
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)


    @classmethod
    def kill(self):
        self._worker.terminate()

    def run(self):
        raise NotImplementedError('Subclasses must implement this method.')

    def fallback(self):
        raise NotImplementedError('Subclasses must implement this method.')

    def cache(self):
        raise NotImplementedError('Subclasses must implement this method.')

    def execute(self, *args):
        return self.run(*args)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def on_timeout(self):
        self.timedout = True

    def execute_with_timeout(self , timeout, *args):
        self.response = None
        self.corr_id = str(uuid.uuid4())

        #TODO : better the code
        new_args = []
        for arg in args:
            new_args.append(str(arg))
        args_body = ",".join(new_args)

        self.timerid = self.connection.add_timeout(timeout, self.on_timeout)

        self.channel.basic_publish(exchange='',
                                   routing_key=self._command_name,
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=args_body)

        while self.response is None:
            self.connection.process_data_events()
            if (self.timedout):
                log.exception('exception calling fallback for {}'.format(self))
                self.timedout = False
                self.connection.remove_timeout(self.timerid)
                return self.fallback(*args)

        return self.response

    #TBI
    def observe(self, timeout=None):
        return Null

    #TBI
    def queue(self,  *args ):

        try:
            pass
            #return self.task.apply_async(args)
        except Exception:
            log.exception('exception calling fallback for {}'.format(self))
            log.info('fallback raised {}'.format(future.exception))
            log.info('trying cache for {}'.format(self))
        return null
