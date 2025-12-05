"""
RabbitMQ client utilities.
"""
import json
import logging
from typing import Callable, Optional
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from .enums import JobPriority, QUEUE_NAMES, DEAD_LETTER_EXCHANGE, DEAD_LETTER_QUEUE

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client for publishing and consuming messages."""
    
    def __init__(self, rabbitmq_url: str):
        """Initialize RabbitMQ client.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
        """
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare dead letter exchange
            self.channel.exchange_declare(
                exchange=DEAD_LETTER_EXCHANGE,
                exchange_type='direct',
                durable=True
            )
            
            # Declare dead letter queue
            self.channel.queue_declare(
                queue=DEAD_LETTER_QUEUE,
                durable=True
            )
            
            # Bind dead letter queue to exchange
            self.channel.queue_bind(
                queue=DEAD_LETTER_QUEUE,
                exchange=DEAD_LETTER_EXCHANGE
            )
            
            # Declare priority queues
            for priority, queue_name in QUEUE_NAMES.items():
                self.channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={
                        'x-max-priority': 10,
                        'x-dead-letter-exchange': DEAD_LETTER_EXCHANGE,
                    }
                )
            
            logger.info("Connected to RabbitMQ successfully")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def publish_job(
        self,
        job_id: str,
        job_type: str,
        priority: JobPriority,
        payload: dict,
        delay: int = 0
    ):
        """Publish a job to the appropriate queue.
        
        Args:
            job_id: Unique job identifier
            job_type: Type of job
            priority: Job priority
            payload: Job payload data
            delay: Delay in seconds before job should be processed
        """
        if not self.channel:
            self.connect()
        
        queue_name = QUEUE_NAMES[priority]
        
        message = {
            'job_id': job_id,
            'job_type': job_type,
            'payload': payload,
        }
        
        properties = BasicProperties(
            delivery_mode=2,  # Persistent
            priority=10 if priority == JobPriority.HIGH else 5 if priority == JobPriority.MEDIUM else 1,
            content_type='application/json',
        )
        
        # If delay is specified, use RabbitMQ delayed message plugin or TTL
        if delay > 0:
            # For simplicity, we'll use a delayed queue approach
            # In production, consider using rabbitmq_delayed_message_exchange plugin
            properties.expiration = str(delay * 1000)  # milliseconds
        
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=properties
        )
        
        logger.info(f"Published job {job_id} to queue {queue_name}")
    
    def consume(
        self,
        queue_name: str,
        callback: Callable,
        prefetch_count: int = 1
    ):
        """Start consuming messages from a queue.
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Callback function to handle messages
            prefetch_count: Number of messages to prefetch
        """
        if not self.channel:
            self.connect()
        
        self.channel.basic_qos(prefetch_count=prefetch_count)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
        logger.info(f"Starting to consume from queue: {queue_name}")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
    
    def ack_message(self, delivery_tag: int):
        """Acknowledge a message.
        
        Args:
            delivery_tag: Delivery tag of the message
        """
        if self.channel:
            self.channel.basic_ack(delivery_tag=delivery_tag)
    
    def nack_message(self, delivery_tag: int, requeue: bool = False):
        """Negative acknowledge a message.
        
        Args:
            delivery_tag: Delivery tag of the message
            requeue: Whether to requeue the message
        """
        if self.channel:
            self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
    
    def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")
